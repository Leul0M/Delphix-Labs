"""Keep Ollama running in the background for the Telegram overlay."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_BIN = "ollama"


def resolve_ollama_cmd() -> Optional[str]:
    global OLLAMA_BIN
    found = shutil.which("ollama")
    if found:
        OLLAMA_BIN = found
        return found
    if sys.platform == "win32":
        for p in (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe",
        ):
            if p.is_file():
                OLLAMA_BIN = str(p)
                return OLLAMA_BIN
    return None


def ollama_cmd(*args: str) -> List[str]:
    return [OLLAMA_BIN, *args]


def is_ollama_running(host: str = OLLAMA_HOST, port: int = OLLAMA_PORT, timeout: float = 1.0) -> bool:
    try:
        import socket

        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def ensure_ollama_background(log_file: Optional[Path] = None) -> bool:
    """Start `ollama serve` in the background if it is not already reachable."""
    if is_ollama_running():
        return True

    if not resolve_ollama_cmd():
        return False

    log_path = log_file or Path.cwd() / "ollama.log"
    try:
        stdout = open(log_path, "a", encoding="utf-8")
    except OSError:
        stdout = subprocess.DEVNULL

    cmd = ollama_cmd("serve")
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
            )
    except FileNotFoundError:
        return False

    for _ in range(30):
        if is_ollama_running():
            return True
        time.sleep(1)
    return is_ollama_running()
