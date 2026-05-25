"""Example skill — list files in ~/agent_workspace."""

import os
from pathlib import Path


def run(**kwargs) -> str:
    # kwargs may include message/task from skill: "..." commands
    _task = kwargs.get("message") or kwargs.get("task") or ""
    workspace = Path(os.path.expanduser("~/agent_workspace"))
    workspace.mkdir(exist_ok=True)
    entries = sorted(workspace.iterdir())
    if not entries:
        return "Workspace is empty."
    lines = [f"Workspace: {workspace}", ""]
    for p in entries:
        tag = "dir" if p.is_dir() else "file"
        lines.append(f"  [{tag}] {p.name}")
    return "\n".join(lines)
