# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

🚀 **The ultimate AI companion for Arch Linux.** Powered by Google Gemini, J.A.R.V.I.S. is a sophisticated voice assistant designed to make your Linux experience feel like science fiction.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux-blue)

## 🎩 Personality & Experience
J.A.R.V.I.S. operates with refined British politeness, dry wit, and proactive intelligence. He doesn't just wait for commands—he monitors your system, manages your workstation, and assists with everything from coding to connectivity.

## 🛠️ Built-in Arch Linux "Cheat Codes"
J.A.R.V.I.S. comes pre-equipped with specialized plugins to manage your system natively:

- **📦 Package Manager**: Search, install, and update packages via `yay`, `paru`, or `pacman`.
- **📖 Arch Wiki Oracle**: Instant answers and documentation fetched directly from the official Arch Wiki.
- **🏥 System Health**: Proactive monitoring of `systemd` failed services, disk usage, and unmerged `.pacnew` files.
- **📡 Connectivity**: Voice-controlled WiFi management (`nmcli`) and Bluetooth control (`bluetoothctl`).
- **🚀 System Optimization**: Fastfetch summaries and one-command system updates.

## 🧩 Core Capabilities
- **Web Research**: Intelligent internet search using DuckDuckGo and Wikipedia.
- **Vision**: Analyzes your screen content for debugging or general assistance (via `capture_screen`).
- **Autonomous Coding**: Can generate and install its own plugins using the `self_coder` module.
- **Memory**: Remembers facts about you and your preferences across sessions.
- **System Control**: Native app launching, media controls, volume management, and custom modes (Gaming, Dinner, etc.).
- **Optional Tools**: Feature-flagged memory digest, system snapshot, and city briefing tools.

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/archpulse/jarvis.git
   cd jarvis
   ```

2. **Setup Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **External Dependencies:**
   Ensure you have the following installed for full functionality:
   - `portaudio` (for mic input)
   - `playerctl` (for media control)
   - `fastfetch` (for system summary)
   - `networkmanager` (for WiFi control)
   - `bluez-utils` (for Bluetooth control)

4. **Run:**
   ```bash
   python main.py
   ```
   *Follow the Setup Wizard on first launch to configure your Gemini API Key.*

## ⚙ Configuration

Most runtime values are now environment-backed instead of hardcoded. See [docs/configuration.md](docs/configuration.md) for the full list of supported variables and feature flags.

The new optional tools are controlled by these flags:

- `JARVIS_FEATURE_MEMORY_DIGEST`
- `JARVIS_FEATURE_SYSTEM_SNAPSHOT`
- `JARVIS_FEATURE_CITY_BRIEFING`

Common overrides include:

- `JARVIS_AI_DATA_DIR`
- `JARVIS_DEFAULT_CITY`
- `JARVIS_MODEL_ID`
- `JARVIS_TOOL_TIMEOUT_SECONDS`
- `JARVIS_WEB_RESEARCH_CACHE_ENABLED`

## 🧪 Tests

Run the local test suite with:

```bash
python -m unittest discover -s tests
```

## 🧰 Development Notes

- The assistant loads plugins from `plugins/` dynamically at runtime.
- The memory store uses SQLite in the configured AI data directory.
- Web research and news plugins use small caches to reduce repeated network work.

## 🧱 Project Structure
- `main.py`: The central intelligence engine (Voice, AI, GUI).
- `plugins/`: A directory of specialized skills.
- `utils.py`: System-level helper functions.
- `setup_wizard.py`: First-run setup flow and localized onboarding text.
- `main.py`: Primary UI translations and assistant dialogue tables.

## 🤝 Contributing
J.A.R.V.I.S. is designed to be modular. You can add new capabilities by simply dropping a new Python script into the `plugins/` directory.

---
*Created with British elegance and Arch Linux efficiency.*
