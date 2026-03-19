import json
import aiohttp
import subprocess
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

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
            description="Read contents of a file",
            parameters={"path": {"type": "string", "description": "File path to read"}}
        )
        self.allowed_dirs = [os.path.expanduser("~/agent_workspace"), os.getcwd()]
    
    async def execute(self, path: str) -> str:
        # Security: Only allow reading from allowed directories
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not any(abs_path.startswith(d) for d in self.allowed_dirs):
            return f"Error: Access denied. Path must be within allowed directories."
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class ShellTool(Tool):
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute a shell command (requires confirmation for destructive ops)",
            parameters={"command": {"type": "string", "description": "Shell command to execute"}}
        )
        self.blocked_commands = ['rm -rf /', 'mkfs', 'dd if=/dev/zero']
    
    async def execute(self, command: str) -> str:
        # Safety checks
        if any(blocked in command.lower() for blocked in self.blocked_commands):
            return "Error: Command blocked for safety reasons."
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=os.path.expanduser("~/agent_workspace")
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return f"Exit code: {result.returncode}\n{output[:2000]}"  # Limit output length
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {str(e)}"

class Agent:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/chat"
        self.tools: Dict[str, Tool] = {
            "file_read": FileTool(),
            "shell": ShellTool(),
        }
        self.conversation_history: List[Dict] = []
        self.max_history = 10
        
    def get_system_prompt(self) -> str:
        tools_desc = "\n".join([
            f"- {name}: {tool.description} (params: {json.dumps(tool.parameters)})"
            for name, tool in self.tools.items()
        ])
        
        return f"""You are a helpful AI assistant running locally on the user's machine.
You have access to the following tools:
{tools_desc}

To use a tool, respond with a JSON object in this format:
{{"tool": "tool_name", "parameters": {{"param1": "value1"}}}}

If you don't need a tool, respond normally. Always be concise."""

    async def chat(self, message: str) -> str:
        # Build messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation_history[-self.max_history:],
            {"role": "user", "content": message}
        ]
        
        # Call Ollama
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7}
                }
            ) as response:
                result = await response.json()
                assistant_msg = result["message"]["content"]
        
        # Check if it's a tool call
        try:
            if assistant_msg.strip().startswith("{") and "\"tool\"" in assistant_msg:
                tool_call = json.loads(assistant_msg.strip())
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                if tool_name in self.tools:
                    tool_result = await self.tools[tool_name].execute(**parameters)
                    
                    # Add to history and get final response
                    self.conversation_history.append({"role": "user", "content": message})
                    self.conversation_history.append({"role": "assistant", "content": f"Using {tool_name}..."})
                    
                    # Ask LLM to interpret tool result
                    follow_up = await self._interpret_tool_result(tool_name, tool_result)
                    self.conversation_history.append({"role": "assistant", "content": follow_up})
                    
                    return f"🔧 Used {tool_name}:\n{follow_up}"
        except json.JSONDecodeError:
            pass
        
        # Normal response
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": assistant_msg})
        
        return assistant_msg
    
    async def _interpret_tool_result(self, tool_name: str, result: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Summarize the tool result concisely for the user."},
                        {"role": "user", "content": f"Tool {tool_name} returned:\n{result[:1000]}\n\nSummarize this for the user."}
                    ],
                    "stream": False
                }
            ) as response:
                result = await response.json()
                return result["message"]["content"]

# Singleton instance
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent