"""Load, run, and create reusable Python skills when Ollama cannot handle a task directly."""

from __future__ import annotations

import importlib.util
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SkillInfo:
    skill_id: str
    description: str
    parameters: Dict[str, Any]
    path_py: Path


def get_install_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_skills_dir() -> Path:
    if os.getenv("DELPHIX_INSTALL_DIR"):
        return Path(os.environ["DELPHIX_INSTALL_DIR"]).expanduser().resolve() / "skills"
    return get_install_root() / "skills"


class SkillsManager:
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = (skills_dir or get_skills_dir()).resolve()
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> List[SkillInfo]:
        skills: List[SkillInfo] = []
        for meta_path in sorted(self.skills_dir.glob("*.json")):
            if meta_path.name.startswith("_"):
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            skill_id = meta.get("skill_id") or meta_path.stem
            py_path = self.skills_dir / f"{skill_id}.py"
            if not py_path.is_file():
                continue
            skills.append(
                SkillInfo(
                    skill_id=skill_id,
                    description=meta.get("description", ""),
                    parameters=meta.get("parameters", {}),
                    path_py=py_path,
                )
            )
        return skills

    def format_skills_for_prompt(self) -> str:
        skills = self.list_skills()
        if not skills:
            return "(no saved skills yet — use create_skill when a task needs custom code)"
        lines = []
        for s in skills:
            lines.append(
                f"- {s.skill_id}: {s.description} (params: {json.dumps(s.parameters)})"
            )
        return "\n".join(lines)

    def run_skill(self, skill_id: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        parameters = parameters or {}
        py_path = self.skills_dir / f"{skill_id}.py"
        if not py_path.is_file():
            return f"Error: skill '{skill_id}' not found in {self.skills_dir}"

        spec = importlib.util.spec_from_file_location(f"skill_{skill_id}", py_path)
        if spec is None or spec.loader is None:
            return f"Error: could not load skill '{skill_id}'"

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            return f"Error loading skill '{skill_id}': {e}"

        if not hasattr(module, "run"):
            return f"Error: skill '{skill_id}' must define run(**kwargs) -> str"

        try:
            result = module.run(**parameters)
            return str(result) if result is not None else "(skill returned nothing)"
        except Exception as e:
            return f"Error running skill '{skill_id}': {e}"

    @staticmethod
    def _safe_skill_id(name: str) -> str:
        slug = re.sub(r"[^a-z0-9_]+", "_", name.lower().strip())
        slug = slug.strip("_")
        return slug[:64] or "custom_skill"

    def save_skill(
        self,
        skill_name: str,
        description: str,
        python_code: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        skill_id = self._safe_skill_id(skill_name)
        py_path = self.skills_dir / f"{skill_id}.py"
        meta_path = self.skills_dir / f"{skill_id}.json"

        code = python_code.strip()
        if "def run" not in code:
            indented = "\n".join(
                "    " + line if line.strip() else line for line in code.splitlines()
            )
            code = (
                "def run(**kwargs):\n"
                '    """Auto-generated skill."""\n'
                f"{indented}\n"
                "    return 'Skill completed.'\n"
            )

        py_path.write_text(code if code.endswith("\n") else code + "\n", encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                {
                    "skill_id": skill_id,
                    "description": description,
                    "parameters": parameters or {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return skill_id
