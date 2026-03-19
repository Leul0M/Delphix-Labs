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

# Default Ollama model
DEFAULT_OLLAMA_MODEL = "qwen3.5:4b"

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


def get_user_input(prompt: str, default: str = "", yes: bool = False) -> str:
    """Prompt the user for input (or return default / exit in non-interactive mode)."""
    if yes:
        return default

    if not is_interactive():
        print_error("No interactive input available. Run this installer from a terminal, or rerun with --yes to accept defaults.")
        sys.exit(1)

    try:
        return input(prompt)
    except EOFError:
        print_error("No input available (stdin closed unexpectedly). Run this installer from a terminal.")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Local Agent CLI Installer")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Accept defaults and skip interactive prompts.")
    return parser.parse_args()


def run_command(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> Tuple[bool, str]:
    """Run shell command with error handling"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"

def check_python_version() -> bool:
    """Check if Python 3.8+ is installed"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
    return False

def check_ollama() -> bool:
    """Check if Ollama is installed"""
    success, _ = run_command(["which", "ollama"], check=False)
    if not success:
        success, _ = run_command(["where", "ollama"], check=False)
    
    if success:
        print_success("Ollama is installed")
        return True
    
    print_warning("Ollama not found")
    return False

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
        print_success("Ollama installed successfully")
        return True
    else:
        print_error("Failed to install Ollama automatically")
        print_info("Please install manually from https://ollama.com")
        return False

def pull_model(model: str = DEFAULT_OLLAMA_MODEL) -> bool:
    """Pull Ollama model"""
    print_info(f"Pulling model {model} (this may take a few minutes)...")
    print(f"{Colors.GRAY}    Download progress:{Colors.ENDC}")
    
    success, output = run_command(["ollama", "pull", model], check=False)
    
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

    cmd = ["ollama", "serve"]
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
    """Clone from GitHub or create local project"""
    print_info("Setting up project files...")
    
    # Create directory structure
    config_dir = install_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Write agent.py
    agent_code = '''import json
import aiohttp
import subprocess
import os
from typing import List, Dict, Any
from dataclasses import dataclass

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
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not any(abs_path.startswith(d) for d in self.allowed_dirs):
            return "Error: Access denied. Path must be within allowed directories."
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class ShellTool(Tool):
    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute a shell command",
            parameters={"command": {"type": "string", "description": "Shell command to execute"}}
        )
        self.blocked_commands = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', '> /dev/sda']
    
    async def execute(self, command: str) -> str:
        if any(blocked in command.lower() for blocked in self.blocked_commands):
            return "Error: Command blocked for safety reasons."
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=os.path.expanduser("~/agent_workspace")
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return f"Exit code: {result.returncode}\\\\n{output[:2000]}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds."
        except Exception as e:
            return f"Error: {str(e)}"

class Agent:
    def __init__(self, model: str = DEFAULT_OLLAMA_MODEL):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/chat"
        self.tools: Dict[str, Tool] = {
            "file_read": FileTool(),
            "shell": ShellTool(),
        }
        self.conversation_history: List[Dict] = []
        self.max_history = 10
        
    def get_system_prompt(self) -> str:
        tools_desc = "\\\\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
        return f"""You are a helpful AI assistant running locally.
Available tools:
{tools_desc}

To use a tool, respond with JSON: {{"tool": "tool_name", "parameters": {{"param": "value"}}}}
If no tool needed, respond normally. Be concise."""

    async def chat(self, message: str) -> str:
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation_history[-self.max_history:],
            {"role": "user", "content": message}
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ollama_url,
                json={"model": self.model, "messages": messages, "stream": False, "options": {"temperature": 0.7}}
            ) as response:
                result = await response.json()
                assistant_msg = result["message"]["content"]
        
        # Check for tool call
        try:
            if assistant_msg.strip().startswith("{") and "\\\"tool\\\"" in assistant_msg:
                tool_call = json.loads(assistant_msg.strip())
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                if tool_name in self.tools:
                    tool_result = await self.tools[tool_name].execute(**parameters)
                    self.conversation_history.extend([
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": f"Used {tool_name}"}
                    ])
                    
                    # Interpret result
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self.ollama_url,
                            json={
                                "model": self.model,
                                "messages": [
                                    {"role": "system", "content": "Summarize tool result concisely."},
                                    {"role": "user", "content": f"Tool {tool_name} returned:\\\\n{tool_result[:1000]}\\\\n\\\\nSummarize for user."}
                                ],
                                "stream": False
                            }
                        ) as resp:
                            interp = await resp.json()
                            summary = interp["message"]["content"]
                            self.conversation_history.append({"role": "assistant", "content": summary})
                            return f"🔧 Used {tool_name}:\\\\n{summary}"
        except json.JSONDecodeError:
            pass
        
        self.conversation_history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": assistant_msg}
        ])
        return assistant_msg

_agent = None
def get_agent():
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent
'''
    
    (config_dir / "agent.py").write_text(agent_code)
    
    # Write telegram_bot.py
    bot_code = '''import logging
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.agent import get_agent

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Local Agent Online!\\\\n\\\\n"
        "I can help with:\\\\n"
        "• 📁 Reading files (~/agent_workspace)\\\\n"
        "• 🖥️ Running shell commands\\\\n"
        "• 💬 General chat\\\\n\\\\n"
        "Try: 'Read welcome.txt' or 'Run ls -la'"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_agent().conversation_history = []
    await update.message.reply_text("🧹 History cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = await get_agent().chat(user_msg)
        if len(response) > 4000:
            response = response[:4000] + "\\\\n... (truncated)"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
'''
    
    (config_dir / "telegram_bot.py").write_text(bot_code)
    
    # Write requirements.txt
    req_content = '''fastapi==0.104.1
uvicorn==0.24.0
python-telegram-bot==20.7
aiohttp==3.9.1
pydantic==2.5.0
python-dotenv==1.0.0
'''
    (install_dir / "requirements.txt").write_text(req_content)
    
    # Write .env.example
    env_example = f'''# Local Agent Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
OLLAMA_MODEL={DEFAULT_OLLAMA_MODEL}
WORKSPACE_DIR=~/agent_workspace
'''
    (install_dir / ".env.example").write_text(env_example)
    
    # Write run.sh
    run_script = '''#!/bin/bash
source venv/bin/activate
export $(cat .env | xargs)
python -m config.telegram_bot
'''
    (install_dir / "run.sh").write_text(run_script)
    os.chmod(install_dir / "run.sh", 0o755)
    
    # Write run.bat for Windows
    run_bat = '''@echo off
call venv\\\\Scripts\\\\activate.bat
for /f "tokens=*" %%a in (.env) do set %%a
python -m config.telegram_bot
'''
    (install_dir / "run.bat").write_text(run_bat)
    
    print_success(f"Project created at {install_dir}")
    return True

def create_virtual_env(install_dir: Path) -> bool:
    """Create Python virtual environment"""
    print_info("Creating virtual environment...")
    
    venv_path = install_dir / "venv"
    
    # Create venv
    success, output = run_command([sys.executable, "-m", "venv", str(venv_path)], check=False)
    
    if not success:
        print_error(f"Failed to create virtual environment: {output}")
        return False
    
    print_success("Virtual environment created")
    return True

def install_dependencies(install_dir: Path) -> bool:
    """Install Python packages"""
    print_info("Installing dependencies (this may take a minute)...")
    
    pip_cmd = str(install_dir / "venv" / "bin" / "pip")
    if sys.platform == "win32":
        pip_cmd = str(install_dir / "venv" / "Scripts" / "pip.exe")
    
    success, output = run_command([pip_cmd, "install", "-r", "requirements.txt"], cwd=str(install_dir), check=False)
    
    if success:
        print_success("Dependencies installed")
        return True
    else:
        print_error(f"Failed to install dependencies: {output}")
        return False

def configure_bot(install_dir: Path, yes: bool = False) -> bool:
    """Interactive bot configuration."""
    if yes:
        print_info("Skipping interactive bot configuration (use .env to configure later).")
        return False

    print_step(6, 7, "Configuration", Icons.KEY)
    
    print_info("Let's configure your Telegram bot!")
    print(f"{Colors.GRAY}    1. Open Telegram and message @BotFather{Colors.ENDC}")
    print(f"{Colors.GRAY}    2. Send /newbot and follow instructions{Colors.ENDC}")
    print(f"{Colors.GRAY}    3. Copy the token (looks like 123456:ABC-DEF...){Colors.ENDC}")
    print()
    
    token = get_user_input(f"{Colors.CYAN}Enter your bot token: {Colors.ENDC}", yes=yes).strip()

    if not token or ":" not in token:
        print_error("Invalid token format")
        return False
    
    # Write .env file
    env_path = install_dir / ".env"
    env_content = f"""TELEGRAM_BOT_TOKEN={token}
OLLAMA_MODEL={DEFAULT_OLLAMA_MODEL}
WORKSPACE_DIR=~/agent_workspace
"""
    env_path.write_text(env_content)
    
    print_success("Configuration saved to .env")
    return True

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


def main():
    args = parse_args()

    clear()
    print_banner()
    
    # Determine install directory
    default_dir = Path.home() / "local-agent"
    print(f"{Colors.GRAY}Default install location: {default_dir}{Colors.ENDC}")
    custom_dir = get_user_input(
        f"{Colors.CYAN}Install directory [Enter for default]: {Colors.ENDC}",
        default="",
        yes=args.yes
    ).strip()
    
    install_dir = Path(custom_dir) if custom_dir else default_dir
    
    if install_dir.exists():
        if args.yes:
            print_warning(f"Directory {install_dir} already exists (overwriting due to --yes)")
            shutil.rmtree(install_dir)
        else:
            print_warning(f"Directory {install_dir} already exists")
            confirm = get_user_input(
                f"{Colors.YELLOW}Overwrite? (y/N): {Colors.ENDC}",
                default="n",
                yes=args.yes
            ).lower()
            if confirm != 'y':
                print_info("Installation cancelled")
                return
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
    
    # Step 3: Pull Model
    print_step(3, total_steps, "Downloading AI Model", Icons.GEAR)
    if not pull_model():
        print_warning("Model download failed, will retry on first run")
    time.sleep(0.5)
    
    # Step 4: Start Ollama server
    print_step(4, total_steps, "Starting Ollama server", Icons.DATABASE)
    start_ollama_server(install_dir / "ollama.log")
    time.sleep(0.5)

    # Step 5: Setup Project
    print_step(5, total_steps, "Creating Project Files", Icons.FOLDER)
    setup_workspace(install_dir)
    clone_or_create_project(install_dir)
    create_virtual_env(install_dir)
    install_dependencies(install_dir)
    time.sleep(0.5)

    # Step 6: Configure
    if not configure_bot(install_dir, yes=args.yes):
        print_warning("Configuration incomplete. Edit .env manually later.")

    # Step 7: Final instructions
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