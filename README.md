# J.A.R.V.I.S.

Open-source Arch Linux copilot for power users, maintainers, and people who want their desktop to do more than sit there.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux-blue)
![Tests](https://img.shields.io/badge/tests-unittest-brightgreen)

## What it is

J.A.R.V.I.S. is a local, plugin-based voice assistant for Arch Linux. It combines:

- system automation
- web research
- persistent memory
- safe plugin installation
- voice-first control

The project is built for people who want a practical Linux copilot, not a generic chat toy.

## Why this repo exists

This project focuses on one narrow pain point: making Linux workflows faster without hiding what is happening.

- You can ask for system health instead of opening five terminals.
- You can search Arch Wiki and the web from one assistant.
- You can load plugins dynamically without editing the core app.
- You can keep feature flags off until you want them.

That combination is what makes the project useful to developers who star repositories and come back later.

## What it can do

- Check system health, top processes, memory, and city-aware briefings
- Search Arch Wiki, DuckDuckGo, Wikipedia, and IT news
- Remember facts and conversation history in SQLite
- Detect screen-analysis requests and capture the screen when asked
- Install vetted plugins through a confirmation flow
- Expose optional tools through feature flags

## 3-minute demo

If you want to show the project publicly, use this sequence:

1. Launch the app and complete the setup wizard.
2. Press `INIT`.
3. Say:
   - `Check system health`
   - `Search Arch Wiki for pipewire latency`
   - `Remember that I prefer concise answers`
   - `What is on my screen?`
   - `Search for plugins related to Arch system monitoring`

This gives viewers the core value in under three minutes:

- local desktop automation
- search
- memory
- vision
- extensibility

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/archpulse/jarvis.git
   cd jarvis
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy the sample environment:
   ```bash
   mkdir -p ~/.jarvis/.ai
   cp .env.example ~/.jarvis/.ai/.env
   ```

4. Start the app:
   ```bash
   python main.py
   ```

5. Follow the first-run wizard, add your Gemini API key, then click `INIT`.

## Feature Flags

These optional tools can be enabled without changing code:

- `JARVIS_FEATURE_MEMORY_DIGEST`
- `JARVIS_FEATURE_SYSTEM_SNAPSHOT`
- `JARVIS_FEATURE_CITY_BRIEFING`

Useful overrides:

- `JARVIS_AI_DATA_DIR`
- `JARVIS_DEFAULT_CITY`
- `JARVIS_MODEL_ID`
- `JARVIS_TOOL_TIMEOUT_SECONDS`
- `JARVIS_WEB_RESEARCH_CACHE_ENABLED`

See [docs/configuration.md](docs/configuration.md) for the full list.

## Why developers may star it

People usually save projects when they are:

- immediately understandable
- easy to try
- obviously useful
- well documented
- small enough to inspect

This repo tries to satisfy that by keeping the assistant modular, test-covered, and configurable.

## Project Structure

- `main.py`: voice loop, UI, assistant orchestration
- `setup_wizard.py`: first-run setup and onboarding
- `plugins/`: feature modules loaded at runtime
- `utils.py`: shared helpers
- `jarvis_config.py`: env/config defaults and feature flags
- `docs/`: configuration and demo docs
- `tests/`: unit tests for config and feature flags

## Development

Run the test suite:

```bash
python -m unittest discover -s tests
```

## Contributing

If you want to add a plugin, keep it:

- small
- well documented
- safe by default
- testable without the full GUI

See [CONTRIBUTING.md](CONTRIBUTING.md) for the preferred contribution flow.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

---
Created for people who actually use Linux.
