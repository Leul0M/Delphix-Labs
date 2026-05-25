"""
Delphix Labs agent — Telegram overlay on Ollama.

All user messages go to Ollama; replies go back to Telegram.
Tools and saved skills extend Ollama when chat alone is not enough.
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

from config.skills_manager import SkillsManager, get_install_root

DEFAULT_MODEL = "llama3.2:2b"
FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.2:2b")
# Models that often need 10GB+ RAM on Ollama — avoid on ~6GB machines
HIGH_RAM_MODELS = frozenset(
    {
        "qwen3.5:4b",
        "qwen3.5",
        "qwen3:8b",
        "qwen3:14b",
        "mistral:7b",
        "llama3.1:8b",
        "llama3:8b",
        "gemma3:4b",
    }
)
MAX_ACTION_DEPTH = 4


def is_memory_error(status: int, body: str) -> bool:
    lower = body.lower()
    return status == 500 and (
        "system memory" in lower or "more system memory" in lower
    )


def persist_ollama_model_to_env(model: str) -> None:
    """Update ~/local-agent/.env so the smaller model sticks after restart."""
    env_path = get_install_root() / ".env"
    if not env_path.is_file():
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    out: List[str] = []
    found = False
    for line in lines:
        if line.startswith("OLLAMA_MODEL="):
            out.append(f"OLLAMA_MODEL={model}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"OLLAMA_MODEL={model}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]

    async def execute(self, **kwargs) -> str:
        raise NotImplementedError


class FileTool(Tool):
    def __init__(self):
        super().__init__(
            name="file_read",
            description="Read contents of a file under ~/agent_workspace",
            parameters={"path": {"type": "string", "description": "File path to read"}},
        )
        self.allowed_dirs = [
            os.path.abspath(os.path.expanduser("~/agent_workspace")),
            os.path.abspath(os.getcwd()),
        ]

    async def execute(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not any(abs_path.startswith(d) for d in self.allowed_dirs):
            return "Error: Access denied. Path must be within allowed directories."
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"


class ShellTool(Tool):
    def __init__(self):
        super().__init__(
            name="shell",
            description="Run a shell command in ~/agent_workspace (30s timeout)",
            parameters={"command": {"type": "string", "description": "Shell command"}},
        )
        self.blocked_commands = ["rm -rf /", "mkfs", "dd if=/dev/zero"]

    async def execute(self, command: str) -> str:
        if any(blocked in command.lower() for blocked in self.blocked_commands):
            return "Error: Command blocked for safety reasons."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.expanduser("~/agent_workspace"),
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return f"Exit code: {result.returncode}\n{output[:2000]}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {e}"


SKILL_CMD_RE = re.compile(r"^\s*skill:\s*(.+)\s*$", re.IGNORECASE | re.DOTALL)


def parse_skill_command(message: str) -> Optional[str]:
    """
    Parse `skill: "your message"` or `skill: your message`.
    Returns the inner task text, or None if not a skill command.
    """
    match = SKILL_CMD_RE.match(message)
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        return ""
    if (body.startswith('"') and body.endswith('"')) or (
        body.startswith("'") and body.endswith("'")
    ):
        return body[1:-1].strip()
    return body


def extract_json_action(text: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON action object from model output."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


class Agent:
    """Routes Telegram ↔ Ollama with tools and persistent skills."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self._fallback_used = False
        if self.model in HIGH_RAM_MODELS:
            import logging

            logging.getLogger(__name__).warning(
                "Model %s needs a lot of RAM; consider OLLAMA_MODEL=%s in .env",
                self.model,
                FALLBACK_MODEL,
            )
        self.ollama_url = os.getenv(
            "OLLAMA_URL", "http://localhost:11434/api/chat"
        )
        self.tools: Dict[str, Tool] = {
            "file_read": FileTool(),
            "shell": ShellTool(),
        }
        self.skills = SkillsManager()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 12

    def get_system_prompt(self) -> str:
        tools_desc = "\n".join(
            f"- {name}: {tool.description} (params: {json.dumps(tool.parameters)})"
            for name, tool in self.tools.items()
        )
        skills_desc = self.skills.format_skills_for_prompt()

        return f"""You are Delphix Labs, a local AI agent. The user talks via Telegram; you run on Ollama on their PC.

Flow: user message → you (Ollama) → reply goes back to Telegram.

Built-in tools:
{tools_desc}

Saved skills (reuse these when they fit — stored in the skills/ folder):
{skills_desc}

When a task cannot be done with chat, tools, or an existing skill, create a reusable Python skill.

Action JSON (respond with ONLY JSON when taking an action, no extra text):
{{"tool": "file_read|shell", "parameters": {{...}}}}
{{"action": "skill", "skill": "skill_id", "parameters": {{...}}}}
{{"action": "create_skill", "skill_name": "snake_case_name", "description": "what it does", "python_code": "def run(**kwargs):\\n    ...", "parameters": {{}}, "run_after_save": true, "run_parameters": {{}}}}

Rules:
- Prefer an existing skill before create_skill.
- create_skill python_code must define run(**kwargs) returning a string.
- For normal conversation, reply in plain text (no JSON).
- Be concise for Telegram.

Users can force the skills path with: skill: "their message" (handled outside this prompt)."""

    def _format_ollama_error(self, status: int, body: str) -> str:
        if is_memory_error(status, body):
            return (
                f"Not enough RAM to run `{self.model}` (needs more than this PC has free).\n\n"
                f"Fix on the Ollama PC:\n"
                f"  ollama pull {FALLBACK_MODEL}\n"
                f"  nano ~/local-agent/.env\n"
                f"  OLLAMA_MODEL={FALLBACK_MODEL}\n"
                f"  ./run.sh\n\n"
                f"Other light models: gemma2:2b, phi3:mini, qwen2.5:3b"
            )
        return f"Ollama API error {status}: {body[:800]}"

    async def _try_fallback_model(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> Optional[str]:
        """Switch to a smaller model and retry once after an OOM error from Ollama."""
        if self._fallback_used or self.model == FALLBACK_MODEL:
            return None
        old_model = self.model
        self.model = FALLBACK_MODEL
        self._fallback_used = True
        os.environ["OLLAMA_MODEL"] = FALLBACK_MODEL
        persist_ollama_model_to_env(FALLBACK_MODEL)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            ) as response:
                body = await response.text()
                if response.status != 200:
                    self.model = old_model
                    return None
                result = json.loads(body)
                note = (
                    f"⚠️ `{old_model}` needs ~12GB RAM; this PC only has ~6GB free.\n"
                    f"Switched to `{FALLBACK_MODEL}` and updated .env automatically.\n"
                    f"(Run once if needed: ollama pull {FALLBACK_MODEL})\n\n"
                )
                return note + result["message"]["content"]

    async def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        allow_fallback: bool = True,
    ) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            ) as response:
                body = await response.text()
                if response.status != 200:
                    if allow_fallback and is_memory_error(response.status, body):
                        retried = await self._try_fallback_model(messages, temperature)
                        if retried is not None:
                            return retried
                    return self._format_ollama_error(response.status, body)
                result = json.loads(body)
                return result["message"]["content"]

    async def _finalize_for_user(
        self, user_message: str, action_label: str, raw_result: str
    ) -> str:
        reply = await self._ollama_chat(
            [
                {
                    "role": "system",
                    "content": "Summarize the result for the Telegram user in a friendly, concise way.",
                },
                {
                    "role": "user",
                    "content": (
                        f"User asked: {user_message}\n"
                        f"Action: {action_label}\n"
                        f"Result:\n{raw_result[:3000]}"
                    ),
                },
            ],
            temperature=0.5,
        )
        return reply

    async def _dispatch_action(
        self, action: Dict[str, Any], user_message: str, depth: int
    ) -> str:
        if depth >= MAX_ACTION_DEPTH:
            return "Stopped after too many chained actions."

        # Tool call (legacy shape)
        if "tool" in action:
            tool_name = action.get("tool")
            params = action.get("parameters") or {}
            if tool_name not in self.tools:
                return f"Unknown tool: {tool_name}"
            raw = await self.tools[tool_name].execute(**params)
            if raw.startswith("Error:") and depth < MAX_ACTION_DEPTH - 1:
                return await self._ask_create_skill_fallback(user_message, raw)
            return await self._finalize_for_user(user_message, tool_name, raw)

        act = action.get("action")

        if act == "skill":
            skill_id = action.get("skill") or action.get("skill_id")
            params = action.get("parameters") or {}
            raw = self.skills.run_skill(skill_id, params)
            if raw.startswith("Error:") and depth < MAX_ACTION_DEPTH - 1:
                return await self._ask_create_skill_fallback(user_message, raw)
            label = f"skill:{skill_id}"
            if raw.startswith("Error:"):
                return raw
            return await self._finalize_for_user(user_message, label, raw)

        if act == "create_skill":
            skill_name = action.get("skill_name") or action.get("name") or "custom_skill"
            description = action.get("description") or "Custom automation"
            code = action.get("python_code") or action.get("code") or ""
            params_meta = action.get("parameters") or {}
            skill_id = self.skills.save_skill(
                skill_name, description, code, params_meta
            )
            msg = f"Saved skill `{skill_id}` to skills/ folder."

            if action.get("run_after_save", True):
                run_params = action.get("run_parameters") or {}
                run_out = self.skills.run_skill(skill_id, run_params)
                msg += f"\n\nRun output:\n{run_out}"
                if not run_out.startswith("Error:"):
                    return await self._finalize_for_user(
                        user_message, f"create_skill:{skill_id}", msg
                    )
                return msg
            return msg

        return f"Unknown action: {action}"

    def _resolve_skill_id_from_text(self, text: str) -> Optional[str]:
        """If text starts with a known skill_id, return (skill_id, remainder task)."""
        text = text.strip()
        if not text:
            return None
        first, _, rest = text.partition(" ")
        first = first.strip().lower()
        known = {s.skill_id for s in self.skills.list_skills()}
        if first in known:
            return first
        if text.lower() in known:
            return text.lower()
        return None

    async def _select_skill_for_task(
        self, task_message: str
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """Ask Ollama which saved skill fits the task."""
        skills = self.skills.list_skills()
        if not skills:
            return None, {}

        explicit = self._resolve_skill_id_from_text(task_message)
        if explicit:
            rest = task_message[len(explicit) :].strip().strip('"').strip("'")
            params = {"message": rest or task_message, "task": rest or task_message}
            return explicit, params

        pick_prompt = await self._ollama_chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Pick the best saved skill for the user's task. "
                        "Respond with ONLY JSON:\n"
                        '{"skill": "skill_id", "parameters": {"message": "...", ...}}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task_message}\n\n"
                        f"Available skills:\n{self.skills.format_skills_for_prompt()}"
                    ),
                },
            ],
            temperature=0.2,
        )
        action = extract_json_action(pick_prompt)
        if action:
            skill_id = action.get("skill") or action.get("skill_id")
            params = action.get("parameters") or {"message": task_message, "task": task_message}
            if skill_id:
                return skill_id, params

        return None, {"message": task_message, "task": task_message}

    async def _ollama_on_skill_output(
        self, task_message: str, skill_id: str, skill_output: str
    ) -> str:
        """Ollama reads skill output and writes the user-facing answer."""
        return await self._ollama_chat(
            [
                {
                    "role": "system",
                    "content": (
                        "The user invoked skill: mode. A Python skill already ran. "
                        "Read the skill output and answer the user's task clearly for Telegram. "
                        "Do not repeat the raw output verbatim unless helpful."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User task: {task_message}\n"
                        f"Skill used: {skill_id}\n\n"
                        f"Skill output:\n{skill_output[:3500]}"
                    ),
                },
            ],
            temperature=0.6,
        )

    async def chat_with_skill(self, task_message: str) -> str:
        """
        skill: "message" flow — run a skill, then Ollama responds using the output.
        Reply includes both skill output and Ollama's answer.
        """
        skill_id, params = await self._select_skill_for_task(task_message)
        if not skill_id:
            created = await self._ask_create_skill_fallback(
                task_message, "No saved skills matched this task."
            )
            return created

        skill_output = self.skills.run_skill(skill_id, params)
        if skill_output.startswith("Error:"):
            fallback = await self._ask_create_skill_fallback(task_message, skill_output)
            return f"🧩 Skill `{skill_id}`:\n{skill_output}\n\n{fallback}"

        ollama_reply = await self._ollama_on_skill_output(
            task_message, skill_id, skill_output
        )
        if ollama_reply.startswith("Ollama API error") or ollama_reply.startswith(
            "Not enough RAM"
        ):
            return f"🧩 Skill `{skill_id}` output:\n{skill_output}\n\n{ollama_reply}"

        combined = (
            f"🧩 Skill `{skill_id}` output:\n{skill_output}\n\n"
            f"💬 Ollama:\n{ollama_reply}"
        )
        self.conversation_history.append(
            {"role": "user", "content": f'skill: "{task_message}"'}
        )
        self.conversation_history.append(
            {"role": "assistant", "content": combined[:2000]}
        )
        return combined

    async def _ask_create_skill_fallback(
        self, user_message: str, error_context: str
    ) -> str:
        """Ask Ollama to author a new skill when tools/skills fail."""
        prompt = await self._ollama_chat(
            [
                {"role": "system", "content": self.get_system_prompt()},
                {
                    "role": "user",
                    "content": (
                        f"The user asked: {user_message}\n"
                        f"Previous attempt failed: {error_context}\n\n"
                        "Respond with ONLY a create_skill JSON action to solve this. "
                        "Include complete python_code with def run(**kwargs)."
                    ),
                },
            ],
            temperature=0.3,
        )
        action = extract_json_action(prompt)
        if action and action.get("action") == "create_skill":
            return await self._dispatch_action(action, user_message, depth=2)
        return (
            f"Could not complete the task.\n{error_context}\n\n"
            f"Model suggested:\n{prompt[:1500]}"
        )

    async def chat(self, message: str) -> str:
        skill_task = parse_skill_command(message)
        if skill_task is not None:
            return await self.chat_with_skill(skill_task)

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation_history[-self.max_history :],
            {"role": "user", "content": message},
        ]

        assistant_msg = await self._ollama_chat(messages)
        if assistant_msg.startswith("Ollama API error") or assistant_msg.startswith(
            "Not enough RAM"
        ):
            return assistant_msg

        action = extract_json_action(assistant_msg)
        if action:
            result = await self._dispatch_action(action, message, depth=0)
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append(
                {"role": "assistant", "content": result[:2000]}
            )
            return result

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_msg}
        )
        return assistant_msg


_agent: Optional[Agent] = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent
