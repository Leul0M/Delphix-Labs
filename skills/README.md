# Skills folder

When Ollama cannot complete a task with chat or built-in tools, the agent saves a **reusable Python skill** here.

Each skill has two files:

- `skill_name.py` — must define `def run(**kwargs) -> str`
- `skill_name.json` — metadata (`description`, `parameters`)

List skills from Telegram: `/skills`

The agent reuses skills automatically on future similar tasks.
