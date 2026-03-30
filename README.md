# JARVIS AI 🤖
🚀 **JARVIS** — An autonomous AI voice assistant powered by Google Gemini. Featuring a microkernel architecture that discovers, security-scans, and installs GitHub plugins on demand.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![OS](https://img.shields.io/badge/OS-Arch%20Linux-blueviolet)

JARVIS is a Linux-native assistant optimized for **Arch Linux** (Gnome/KDE). It executes local commands, stores long-term memory, and expands its capabilities by learning new plugins.

## 🧠 Core Architecture
- **Microkernel Layout:** `main.py` acts as the engine (audio loop, Gemini session, UI queues). All logic is decoupled into plugins.
- **Adaptive Workflow:** Ask *"Jarvis, install a crypto tracker,"* and it will search GitHub for `axinix-plugin` tags, show metadata, and wait for your confirmation.
- **Static Security Scan:** Before saving any plugin to `plugins/`, JARVIS scans the code for risky calls like `eval` or unchecked `os.system`.
- **Long-term Memory:** Uses SQLite to store facts about you and your preferences.

## 🛠 Setup & Launch
Optimized for **Arch Linux + Gnome on X11**. Uses the `uv` package manager for maximum speed.

### Quick Start:
1. **Clone the repo:**
   ```bash
   git clone [https://github.com/archpulse/JARVIS.git](https://github.com/archpulse/JARVIS.git)
   cd JARVIS
Run with uv (Recommended):

Bash
QT_QPA_PLATFORM=xcb uv run main.py
Note: QT_QPA_PLATFORM=xcb ensures Qt stability on X11 sessions.

Configuration:
On the first launch, the PyQt Wizard will guide you through API key entry (Google AI Studio) and basic localization settings.

🧩 Plugin System
plugins/00_core_memory.py — Fact storage and retrieval.

plugins/01_core_system.py — Native Linux control (volume, apps, system stats via playerctl/wpctl).

plugins/02_core_web.py — DuckDuckGo search, Wikipedia, and weather.

🎙 Voice Interaction
Powered by local openwakeword. Wake phrase: "Hey Jarvis".

Built by a Linux user for Linux users. Running on Arch, thinking with Gemini.
