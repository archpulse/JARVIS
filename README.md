# J.A.R.V.I.S.

Open-source Arch Linux copilot for power users, maintainers, and people who want their desktop to do more than sit there.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux-blue)
![Version](https://img.shields.io/badge/version-1.2.2-blue.svg)
![Tests](https://img.shields.io/badge/tests-unittest-brightgreen)

## Overview

J.A.R.V.I.S. is a local, plugin-based voice assistant tailored for Arch Linux environments. It brings together system automation, web research, persistent memory, safe plugin management, and voice-first control into a unified, modular ecosystem.

Designed as a practical Linux copilot rather than a generic chat toy, J.A.R.V.I.S. aims to streamline complex workflows and provide immediate access to system information and web resources directly from your desktop.

## Features

- **System Automation & Monitoring**: Instantly check system health, top processes, memory usage, and receive city-aware daily briefings.
- **Integrated Research**: Search the Arch Wiki, DuckDuckGo, Wikipedia, and IT news directly through voice or text commands.
- **Persistent Memory**: Remembers facts, preferences, and conversation history locally using SQLite.
- **Screen Awareness**: Detects screen-analysis requests and can capture and analyze your screen context when asked.
- **Extensible Architecture**: Safely install and load vetted plugins dynamically without modifying the core application.
- **Feature Flags**: Easily toggle optional capabilities on or off as needed.

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/archpulse/jarvis.git
   cd jarvis
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure your environment**:
   ```bash
   mkdir -p ~/.jarvis/.ai
   cp .env.example ~/.jarvis/.ai/.env
   ```

4. **Start the application**:
   ```bash
   python main.py
   ```

5. **Setup**: Follow the first-run wizard, input your Gemini API key, and click `INIT` to initialize the system.

## Configuration

You can customize J.A.R.V.I.S. behavior using feature flags and environment variables. For a full list of available options, including memory digest, system snapshot, and city briefing features, please see [docs/configuration.md](docs/configuration.md).

## Project Structure

- `main.py`: Core voice loop, UI, and assistant orchestration.
- `setup_wizard.py`: First-run setup and onboarding flow.
- `plugins/`: Directory for feature modules loaded at runtime.
- `utils.py`: Shared utility functions and helpers.
- `jarvis_config.py`: Environment configuration, defaults, and feature flags.
- `docs/`: Configuration and documentation.
- `tests/`: Unit test suite.

## Development & Testing

To run the local test suite:

```bash
python -m unittest discover -s tests
```

## Contributing

We welcome contributions! If you want to add a new plugin or feature, please ensure it is:
- Focused and small in scope
- Well documented
- Safe by default
- Testable without requiring the full GUI

Review our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
*Created for people who actually use Linux.*
