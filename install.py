#!/usr/bin/env python3
"""
Local Agent CLI Installer
One-command setup for your personal AI agent
"""

import argparse
import os
import sys
import subprocess
import json
import time
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple

# Default Ollama model (~2–4 GB RAM). qwen3.5:4b needs ~12 GB — use only on high-RAM PCs.
DEFAULT_OLLAMA_MODEL = "llama3.2:2b"
RECOMMENDED_LOW_RAM_MODELS = ("llama3.2:2b", "llama3.2:1b", "gemma2:2b", "phi3:mini", "qwen2.5:3b")

REPO_ROOT = Path(__file__).resolve().parent
REPO_RAW = os.environ.get(
    "REPO_RAW", "https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main"
).rstrip("/")
OLLAMA_BIN = "ollama"

# Relative paths fetched when install.py runs alone (e.g. curl install.py | python3)
BUNDLE_PATHS = (
    "requirements.txt",
    "config/__init__.py",
    "config/agent.py",
    "config/telegram_bot.py",
    "config/ollama_service.py",
    "config/skills_manager.py",
    "config/security.py",
    "skills/README.md",
    "skills/list_workspace.py",
    "skills/list_workspace.json",
    "templates/.env.example",
)


def ensure_repo_bundle() -> bool:
    """Download config/ and requirements from GitHub if missing next to install.py."""
    if (REPO_ROOT / "config").is_dir() and (REPO_ROOT / "requirements.txt").is_file():
        return True

    print_info(f"Downloading project files from {REPO_RAW} ...")
    try:
        from urllib.request import urlopen
    except ImportError:
        print_error("urllib is unavailable; run install.sh or clone the full repository.")
        return False

    for rel in BUNDLE_PATHS:
        dest = REPO_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"{REPO_RAW}/{rel}"
        try:
            with urlopen(url, timeout=60) as resp:
                dest.write_bytes(resp.read())
        except Exception as e:
            print_error(f"Failed to download {url}: {e}")
            return False

    print_success("Project files downloaded.")
    return True


def _configure_console_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows consoles (cp1252) when printing icons."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_configure_console_encoding()

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'

class Icons:
    ROCKET = "🚀"
    ROBOT = "🤖"
    GEAR = "⚙️"
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    PACKAGE = "📦"
    KEY = "🔑"
    FOLDER = "📁"
    DATABASE = "🗄️"
    CHAT = "💬"
    SPARKLES = "✨"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
██████╗ ███████╗██╗     ██████╗ ██╗  ██╗██╗██╗  ██╗    ██╗      █████╗ ██████╗ ███████╗
██╔══██╗██╔════╝██║     ██╔══██╗██║  ██║██║╚██╗██╔╝    ██║     ██╔══██╗██╔══██╗██╔════╝
██║  ██║█████╗  ██║     ██████╔╝███████║██║ ╚███╔╝     ██║     ███████║██████╔╝█████╗  
██║  ██║██╔══╝  ██║     ██╔═══╝ ██╔══██║██║ ██╔██╗     ██║     ██╔══██║██╔══██╗██╔══╝  
██████╔╝███████╗███████╗██║     ██║  ██║██║██╔╝ ██╗    ███████╗██║  ██║██████╔╝███████╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝  
{Colors.ENDC}
{Colors.GRAY}    Local AI Agent Installer v1.0.0 | github.com/Leul0M/Delphix-Labs{Colors.ENDC}
    """
    print(banner)

def print_step(number: int, total: int, title: str, icon: str = ""):
    progress = f"[{number}/{total}]"
    bar = "█" * number + "░" * (total - number)
    print(f"\n{Colors.BLUE}{Colors.BOLD}{icon} Step {progress} {bar} {Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}    {title}{Colors.ENDC}")
    print(f"{Colors.GRAY}    {'─' * 50}{Colors.ENDC}")

def print_success(message: str):
    print(f"{Colors.GREEN}{Icons.CHECK} {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}{Icons.CROSS} {message}{Colors.ENDC}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}{Icons.WARNING} {message}{Colors.ENDC}")

def print_info(message: str):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")


def is_interactive() -> bool:
    """Return True if stdin is a TTY (interactive)."""
    return sys.stdin.isatty()


def read_tty_line(prompt: str) -> Optional[str]:
    """Read one line from the real terminal when stdin is piped (e.g. curl | bash)."""
    if sys.platform == "win32":
        if sys.stdin.isatty():
            try:
                return input(prompt)
            except EOFError:
                return None
        try:
            with open("CONIN$", "r") as con:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                return con.readline().rstrip("\n\r")
        except OSError:
            return None

    try:
        with open("/dev/tty", "r") as tty:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return tty.readline().rstrip("\n")
    except (OSError, AttributeError):
        pass

    if sys.stdin.isatty():
        try:
            return input(prompt)
        except EOFError:
            return None
    return None


def get_user_input(prompt: str, default: str = "", yes: bool = False) -> str:
    """Prompt the user for input (or return default / exit in non-interactive mode)."""
    if yes:
        return default

    if is_interactive():
        try:
            value = input(prompt)
            return value if value else default
        except EOFError:
            print_error("No input available (stdin closed unexpectedly). Run this installer from a terminal.")
            sys.exit(1)

    line = read_tty_line(prompt)
    if line is not None:
        return line if line else default

    print_error(
        "Cannot read input. Run the installer in a terminal, or use --yes with "
        "TELEGRAM_BOT_TOKEN set in the environment."
    )
    sys.exit(1)


def require_user_input(prompt: str) -> str:
    """Prompt the user for a REQUIRED value (works when stdin is piped)."""
    while True:
        line = read_tty_line(prompt)
        if line is None:
            print_error(
                "Cannot read input. Run the installer in a terminal, or use --yes with "
                "TELEGRAM_BOT_TOKEN set in the environment."
            )
            sys.exit(1)
        if line.strip():
            return line.strip()
        print_warning("This value is required. Please try again.")


def parse_args():
    parser = argparse.ArgumentParser(description="Local Agent CLI Installer")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Non-interactive install: use defaults and require "
                             "TELEGRAM_BOT_TOKEN (and optional OLLAMA_MODEL) in the environment.")
    return parser.parse_args()


def run_command(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> Tuple[bool, str]:
    """Run shell command with error handling"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return False, result.stderr if result.stderr else result.stdout
        return True, result.stdout
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, str(e)

def check_python_version() -> bool:
    """Check if Python 3.8+ is installed"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
    return False

def resolve_ollama_cmd() -> Optional[str]:
    """Locate ollama binary (PATH or common Windows install paths)."""
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


def check_ollama() -> bool:
    """Check if Ollama is installed"""
    if resolve_ollama_cmd():
        print_success(f"Ollama is installed ({OLLAMA_BIN})")
        return True

    print_warning("Ollama not found")
    return False


def model_is_pulled(model: str) -> bool:
    """Return True if the model appears in `ollama list`."""
    success, output = run_command(ollama_cmd("list"), check=False)
    if not success:
        return False
    if model in output:
        return True
    base = model.split(":")[0]
    return any(line.startswith(base) for line in output.splitlines())


def install_ollama():
    """Install Ollama based on OS"""
    print_info("Installing Ollama...")
    
    system = sys.platform
    
    if system == "darwin":  # macOS
        success, _ = run_command(["brew", "install", "ollama"], check=False)
        if not success:
            print_info("Trying curl install...")
            success, output = run_command(["curl", "-fsSL", "https://ollama.com/install.sh"], check=False)
            if success:
                success, _ = run_command(["bash", "-c", output], check=False)
    
    elif system == "linux":
        # Use bash to pipe curl output into sh
        success, _ = run_command(["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"], check=False)
    
    elif system == "win32":
        print_error("Please install Ollama manually from https://ollama.com/download")
        print_info("After installation, run this installer again")
        return False
    
    if success:
        # Verify it is in PATH
        if check_ollama():
            print_success("Ollama installed successfully")
            return True
        else:
            print_error("Ollama install script succeeded, but 'ollama' is not in PATH. Please restart your terminal or install manually.")
            return False
    else:
        print_error("Failed to install Ollama automatically")
        print_info("Please install manually from https://ollama.com")
        return False

def pull_model(model: str = DEFAULT_OLLAMA_MODEL) -> bool:
    """Pull Ollama model (skip if already present)."""
    if model_is_pulled(model):
        print_success(f"Model {model} is already installed")
        return True

    print_info(f"Pulling model {model} (this may take a few minutes)...")
    print(f"{Colors.GRAY}    Download progress:{Colors.ENDC}")
    
    success, output = run_command(ollama_cmd("pull", model), check=False)
    
    if success:
        print_success(f"Model {model} ready")
        return True
    else:
        print_error(f"Failed to pull model: {output}")
        return False


def is_ollama_running(host: str = "localhost", port: int = 11434, timeout: float = 1.0) -> bool:
    """Check if Ollama server is running."""
    try:
        import socket
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def start_ollama_server(log_file: Optional[Path] = None) -> Optional[subprocess.Popen]:
    """Start Ollama server in the background."""
    if is_ollama_running():
        print_success("Ollama server is already running")
        return None

    print_info("Starting Ollama server in the background (logs: ollama.log)...")
    log_path = log_file or Path.cwd() / "ollama.log"
    try:
        stdout = open(log_path, "a", encoding="utf-8")
    except Exception:
        stdout = subprocess.DEVNULL

    cmd = ollama_cmd("serve")
    try:
        if sys.platform == "win32":
            proc = subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            proc = subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        print_success(f"Ollama server process launched (PID: {proc.pid})")

        # Wait until the server is reachable before continuing.
        for i in range(30):
            if is_ollama_running():
                print_success("Ollama server is running and reachable")
                return proc
            time.sleep(1)

        print_warning("Ollama server did not respond within 30 seconds. Continuing anyway.")
        return proc
    except FileNotFoundError:
        print_error("Ollama executable not found; please install Ollama and rerun.")
        return None
    except Exception as e:
        print_error(f"Failed to start Ollama server: {e}")
        return None


def setup_workspace(install_dir: Path) -> Path:
    """Create workspace directory"""
    workspace = Path.home() / "agent_workspace"
    workspace.mkdir(exist_ok=True)
    
    # Create sample file
    sample_file = workspace / "welcome.txt"
    sample_file.write_text(f"""Welcome to Local Agent Workspace!
Created: {time.strftime("%Y-%m-%d %H:%M:%S")}

You can ask me to:
- Read files in this directory
- Run shell commands here
- Help with coding tasks

Try: "Read the file welcome.txt"
""")
    
    print_success(f"Workspace created at {workspace}")
    return workspace

def clone_or_create_project(install_dir: Path) -> bool:
    """Copy project files from this repository into the install directory."""
    print_info("Setting up project files...")

    if not ensure_repo_bundle():
        return False

    config_src = REPO_ROOT / "config"
    if not config_src.is_dir():
        print_error(f"Missing config directory at {config_src}")
        return False

    config_dir = install_dir / "config"
    if config_dir.exists():
        shutil.rmtree(config_dir)
    shutil.copytree(config_src, config_dir)

    skills_src = REPO_ROOT / "skills"
    skills_dir = install_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    if skills_src.is_dir():
        for item in skills_src.iterdir():
            dest = skills_dir / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir() and not dest.exists():
                shutil.copytree(item, dest)

    req_src = REPO_ROOT / "requirements.txt"
    if req_src.is_file():
        shutil.copy2(req_src, install_dir / "requirements.txt")
    else:
        print_error(f"Missing requirements.txt at {req_src}")
        return False

    env_example_src = REPO_ROOT / "templates" / ".env.example"
    if env_example_src.is_file():
        shutil.copy2(env_example_src, install_dir / ".env.example")
    else:
        (install_dir / ".env.example").write_text(
            f"TELEGRAM_BOT_TOKEN=your_bot_token_here\n"
            f"OLLAMA_MODEL={DEFAULT_OLLAMA_MODEL}\n"
            f"WORKSPACE_DIR=~/agent_workspace\n"
        )
    
    # Write run.sh — Ollama in background, then Telegram overlay
    run_script = '''#!/bin/bash
cd "$(dirname "$0")"
export DELPHIX_INSTALL_DIR="$(pwd)"
source venv/bin/activate
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama in background (ollama.log)..."
  nohup ollama serve >> ollama.log 2>&1 &
  sleep 2
fi
python -m config.telegram_bot
'''
    (install_dir / "run.sh").write_text(run_script)
    os.chmod(install_dir / "run.sh", 0o755)
    
    # Write run.bat for Windows
    run_bat = '''@echo off
cd /d "%~dp0"
set DELPHIX_INSTALL_DIR=%CD%
call venv\\\\Scripts\\\\activate.bat
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do set %%a=%%b
)
where ollama >nul 2>&1 && (
  curl -sf http://localhost:11434/api/tags >nul 2>&1 || (
    echo Starting Ollama in background...
    start /B ollama serve >> ollama.log 2>&1
    timeout /t 2 /nobreak >nul
  )
)
python -m config.telegram_bot
'''
    (install_dir / "run.bat").write_text(run_bat)
    
    print_success(f"Project created at {install_dir}")
    return True

def normalize_install_dir(raw: str, default: Path) -> Path:
    """Resolve install directory; relative paths are under the user's home (not cwd)."""
    text = (raw or "").strip()
    if not text or text in ("~", "~/", "home"):
        return default.expanduser().resolve()

    path = Path(text).expanduser()
    if not path.is_absolute():
        path = Path.home() / path
    return path.resolve()


def create_virtual_env(install_dir: Path) -> bool:
    """Create Python virtual environment"""
    print_info("Creating virtual environment...")
    
    venv_path = install_dir / "venv"
    
    # Create venv (--upgrade-deps helps ensure pip is available)
    success, output = run_command(
        [sys.executable, "-m", "venv", str(venv_path)],
        cwd=str(install_dir),
        check=False,
    )
    
    if not success:
        print_error(f"Failed to create virtual environment: {output}")
        if sys.platform == "linux":
            print_info("On Debian/Ubuntu, you may need to run: sudo apt install python3-venv")
        return False
    
    print_success("Virtual environment created")
    return True

def install_dependencies(install_dir: Path) -> bool:
    """Install Python packages"""
    print_info("Installing dependencies (this may take a minute)...")

    python_exe = get_venv_python(install_dir)
    if not python_exe.is_file():
        print_error(
            f"Virtualenv Python not found at {python_exe}. "
            "Try: sudo apt install python3-venv  (Debian/Ubuntu)"
        )
        return False

    success, output = run_command(
        [str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=str(install_dir),
        check=False,
    )
    
    if success:
        print_success("Dependencies installed")
        return True
    else:
        print_error(f"Failed to install dependencies: {output}")
        return False

def configure_bot(install_dir: Path, token: str, model: str) -> None:
    """Write the .env configuration file with the provided token and model."""
    if model in ("qwen3.5:4b", "qwen3.5") and model not in RECOMMENDED_LOW_RAM_MODELS:
        print_warning(
            f"{model} needs ~12GB+ RAM. Switching .env default to {DEFAULT_OLLAMA_MODEL}."
        )
        model = DEFAULT_OLLAMA_MODEL
    env_path = install_dir / ".env"
    env_content = f"""TELEGRAM_BOT_TOKEN={token}
OLLAMA_MODEL={model}
WORKSPACE_DIR=~/agent_workspace
"""
    env_path.write_text(env_content)
    print_success("Configuration saved to .env")

def print_final_instructions(install_dir: Path):
    """Print final setup instructions"""
    print_step(7, 7, "Installation Complete!", Icons.SPARKLES)
    
    print(f"""
{Colors.GREEN}{Colors.BOLD}{Icons.ROBOT} Your Local Agent is ready!{Colors.ENDC}

{Colors.CYAN}Next steps:{Colors.ENDC}

1. {Colors.YELLOW}Ollama server has been started automatically.{Colors.ENDC}
   {Colors.GRAY}If it is not running, start it with: ollama serve{Colors.ENDC}

2. {Colors.YELLOW}In a new terminal, run your agent:{Colors.ENDC}
   {Colors.GRAY}cd {install_dir}{Colors.ENDC}
   {Colors.GRAY}./run.sh{Colors.ENDC} {Colors.GRAY}(Linux/Mac){Colors.ENDC}
   {Colors.GRAY}run.bat{Colors.ENDC} {Colors.GRAY}(Windows){Colors.ENDC}

3. {Colors.YELLOW}Open Telegram and message your bot!{Colors.ENDC}

{Colors.CYAN}Available commands:{Colors.ENDC}
   /start - Show welcome message
   /clear - Clear conversation history
   Any text - Chat with your local AI

{Colors.CYAN}Example messages:{Colors.ENDC}
   • "Read welcome.txt"
   • "Run ls -la"
   • "What can you do?"

{Colors.GRAY}Workspace directory: ~/agent_workspace{Colors.ENDC}
{Colors.GRAY}Config file: {install_dir}/.env{Colors.ENDC}
""")
    
    # Save quickstart to file
    quickstart = install_dir / "QUICKSTART.md"
    quickstart.write_text(f"""# Local Agent - Quick Start

## Start the Agent

1. Ollama should already be running.
   If needed, start it manually:
   ollama serve

2. In a new terminal, run the bot:
   cd {install_dir}
   ./run.sh

## Usage

Message your bot on Telegram with:
- "Read <filename>" - Read files from workspace
- "Run <command>" - Execute shell commands
- General chat for any questions

## Configuration

Edit `{install_dir}/.env` to change settings.

## Troubleshooting

- If Ollama fails: `ollama pull {DEFAULT_OLLAMA_MODEL}`
- If bot fails: Check token in .env file
- View logs: Check terminal output
""")
    
    print(f"{Colors.GREEN}Quick reference saved to {quickstart}{Colors.ENDC}")


def get_venv_python(install_dir: Path) -> Path:
    """Return path to the Python executable inside the virtual environment."""
    if sys.platform == "win32":
        return install_dir / "venv" / "Scripts" / "python.exe"
    for name in ("python", "python3"):
        candidate = install_dir / "venv" / "bin" / name
        if candidate.is_file():
            return candidate
    return install_dir / "venv" / "bin" / "python"


def run_agent(install_dir: Path) -> Optional[subprocess.Popen]:
    """Start the Telegram bot in the background."""
    python_exe = get_venv_python(install_dir)

    if not python_exe.exists():
        print_error("Unable to find virtualenv Python. Did dependency installation succeed?")
        return None

    cmd = [str(python_exe), "-m", "config.telegram_bot"]
    print_info("Starting the Delphix Labs agent (Telegram bot) in the background...")
    try:
        proc = subprocess.Popen(cmd, cwd=str(install_dir), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print_success(f"Agent started (PID: {proc.pid}).")
        return proc
    except Exception as e:
        print_error(f"Failed to start agent: {e}")
        return None


def prompt_run_agent(install_dir: Path, yes: bool = False):
    answer = get_user_input(
        f"{Colors.CYAN}Run the Delphix Labs agent now? (y/N): {Colors.ENDC}",
        default="y" if yes else "",
        yes=yes
    ).strip().lower()
    if answer == "y":
        run_agent(install_dir)
    else:
        print_info("You can start the agent later with ./run.sh (Linux/Mac) or run.bat (Windows)")


def collect_install_settings(yes: bool) -> Optional[Tuple[Path, str, str]]:
    """Collect install directory, bot token, and model before automated steps."""
    default_dir = (Path.home() / "local-agent").resolve()

    if yes:
        install_dir = normalize_install_dir(
            os.environ.get("INSTALL_DIR", ""),
            default_dir,
        )
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not bot_token or ":" not in bot_token:
            print_error(
                "Non-interactive install requires TELEGRAM_BOT_TOKEN in the environment "
                "(format: 123456789:ABCdef...)."
            )
            sys.exit(1)
        chosen_model = (
            os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
            or DEFAULT_OLLAMA_MODEL
        )
        if install_dir.exists():
            print_warning(f"Directory {install_dir} already exists (will overwrite)")
        print_success(f"Install directory: {install_dir}")
        print_success(f"Using model: {chosen_model}")
        return install_dir, bot_token, chosen_model

    print(f"{Colors.GRAY}Default install location: {default_dir}{Colors.ENDC}")
    custom_dir = require_user_input(
        f"{Colors.CYAN}Install directory [Enter for default]: {Colors.ENDC}"
    ).strip()
    install_dir = normalize_install_dir(custom_dir, default_dir)
    print_success(f"Install directory: {install_dir}")

    if install_dir.exists():
        print_warning(f"Directory {install_dir} already exists")
        confirm = require_user_input(
            f"{Colors.YELLOW}Overwrite? (y/N): {Colors.ENDC}"
        ).strip().lower()
        if confirm != "y":
            print_info("Installation cancelled")
            return None

    print()
    print_info("Let's configure your Telegram bot!")
    print(f"{Colors.GRAY}    1. Open Telegram and search for @BotFather{Colors.ENDC}")
    print(f"{Colors.GRAY}    2. Send /newbot and follow the instructions{Colors.ENDC}")
    print(f"{Colors.GRAY}    3. Copy the token BotFather gives you (looks like 123456:ABC-DEF...){Colors.ENDC}")
    print()
    bot_token = ""
    while True:
        bot_token = require_user_input(
            f"{Colors.CYAN}Enter your Telegram bot token: {Colors.ENDC}"
        ).strip()
        if bot_token and ":" in bot_token:
            break
        print_error(
            "Invalid token format. It should look like  123456789:ABCdefGHI-jkl  "
            "(digits, colon, letters)."
        )
        print_warning("Please try again.")

    print()
    print_info("Which Ollama model should the agent use?")
    print(f"{Colors.GRAY}    Default: {DEFAULT_OLLAMA_MODEL} (fits low RAM PCs){Colors.ENDC}")
    print(f"{Colors.GRAY}    Low RAM:   {', '.join(RECOMMENDED_LOW_RAM_MODELS)}{Colors.ENDC}")
    print(f"{Colors.GRAY}    High RAM:  qwen3.5:4b needs ~12 GB+ free memory{Colors.ENDC}")
    print(f"{Colors.GRAY}    Press Enter to use the default.{Colors.ENDC}")
    model_input = require_user_input(
        f"{Colors.CYAN}Ollama model [{DEFAULT_OLLAMA_MODEL}]: {Colors.ENDC}"
    ).strip()
    chosen_model = model_input if model_input else DEFAULT_OLLAMA_MODEL
    print_success(f"Using model: {chosen_model}")
    print()
    return install_dir, bot_token, chosen_model


def main():
    args = parse_args()

    if not is_interactive() and not args.yes:
        print_info(
            "Piped install: prompts will appear in your terminal. "
            "For a fully automated install, set TELEGRAM_BOT_TOKEN before piping."
        )

    clear()
    print_banner()

    settings = collect_install_settings(args.yes)
    if settings is None:
        return
    install_dir, bot_token, chosen_model = settings
    install_dir = install_dir.resolve()

    # ── Now run all automated steps unattended ────────────────────────────
    if install_dir.exists():
        shutil.rmtree(install_dir)
    install_dir.mkdir(parents=True)

    total_steps = 7

    # Step 1: Check Python
    print_step(1, total_steps, "Checking Python Installation", Icons.PACKAGE)
    if not check_python_version():
        sys.exit(1)
    time.sleep(0.5)

    # Step 2: Check/Install Ollama
    print_step(2, total_steps, "Setting up Ollama", Icons.DATABASE)
    if not check_ollama():
        if not install_ollama():
            print_error("Cannot continue without Ollama")
            sys.exit(1)
    time.sleep(0.5)

    # Step 3: Start Ollama server
    print_step(3, total_steps, "Starting Ollama server", Icons.DATABASE)
    start_ollama_server(install_dir / "ollama.log")
    if not is_ollama_running():
        print_warning("Ollama server is not running properly.")
    time.sleep(0.5)

    # Step 4: Pull the chosen model
    print_step(4, total_steps, "Downloading AI Model", Icons.GEAR)
    if not pull_model(chosen_model):
        print_error("Model download failed. Please check your internet connection or Ollama installation.")
        sys.exit(1)
    time.sleep(0.5)

    # Step 5: Create project files
    print_step(5, total_steps, "Creating Project Files", Icons.FOLDER)
    setup_workspace(install_dir)
    if not clone_or_create_project(install_dir):
        print_error("Failed to create project files")
        sys.exit(1)
    time.sleep(0.5)

    # Step 6: Set up virtual environment and install dependencies
    print_step(6, total_steps, "Installing Dependencies", Icons.PACKAGE)
    if not create_virtual_env(install_dir):
        print_error("Failed to create virtual environment")
        sys.exit(1)
    if not install_dependencies(install_dir):
        print_error("Failed to install dependencies")
        sys.exit(1)
    time.sleep(0.5)

    # Step 7: Write .env and finish
    print_step(7, total_steps, "Finalizing Configuration", Icons.KEY)
    configure_bot(install_dir, token=bot_token, model=chosen_model)
    print_final_instructions(install_dir)
    prompt_run_agent(install_dir, yes=args.yes)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Installation cancelled by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)