# axinix-ai
🚀 Axinix AI — An autonomous AI voice assistant powered by Google Gemini. It pre-filters GitHub plugins by intent, asks for explicit confirmation, and only then installs code that passes static security policy.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Axinix AI is an advanced Linux-native voice assistant (Arch/KDE friendly). It executes local commands, stores long-term memory, and expands itself by learning new plugins on demand.

## 🧱 Microkernel Layout
- `main.py` is the engine layer only (audio loop, Gemini session, UI queues, and plugin loader).
- Core capabilities are shipped as plugins.
- `plugins/00_core_memory.py` provides SQLite memory (`save_fact`, `get_fact`, plus compatibility aliases).
- `plugins/01_core_system.py` provides native Linux control (app launch, media, volume, system stats, city time, standby, screen control).
- `plugins/02_core_web.py` provides DuckDuckGo/Wikipedia research, weather, news, and web media openers.

## 🔥 Adaptive Plugin Workflow
Ask for any capability, for example “Jarvis, install a crypto tracker plugin,” and the assistant:
1. Searches GitHub for candidate repos tagged `axinix-plugin`.
2. Pulls metadata-only context (description, stars, README preview) for top matches.
3. Asks user for explicit confirmation before any source code download.
4. Downloads code only after confirmation, then runs static checks (`eval`, `exec`, `os.system`, etc.).
5. Saves only approved plugin code into `plugins/` for availability after tool refresh/restart.

## 🛠️ Built-in Capabilities
- **System Control:** Launches apps and controls media/volume natively via `playerctl` and `wpctl`/`pactl`.
- **Memory:** Stores facts in `memory.db` through the `save_memory` / `get_memory` tools.
- **Internet Research & Weather:** Live DuckDuckGo/Wikipedia search plus `wttr.in` weather lookups.
- **Entertainment:** Opens YouTube/Spotify searches, rolls dice, flips coins, etc.
- **Dynamic Plugins:** `plugins/cyber_installer.py` enforces confirm-before-pull and strict static scanning before installation.

## 🚀 Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/archpulse/axinix-ai.git
   cd axinix-ai
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies (ensure `portaudio`/audio drivers are present).
   ```bash
   pip install -r requirements.txt
   ```
4. Set `GOOGLE_API_KEY` either in `.env`, the Settings UI, or during the first-run setup wizard.
5. Run `python main.py`.

## 🧩 Writing Plugins
Create a `.py` with functions plus `register_plugin()` returning `(tools, mapping)`. Tag the repo with `axinix-plugin`, and Axinix AI will find it via the built-in plugin manager.

(See `plugins/` for the sample `cyber_installer` plugin.)

## 🔧 The Setup Wizard
On first launch the PyQt wizard collects your preferences:
- Language + theme selection with localized page copy covering English, Russian, Ukrainian, German, Spanish, French, Chinese, Japanese, Korean, and Portuguese.
- API key entry panel that points you to Google AI Studio and ensures Gemini access is configured before the assistant starts.
- Default city input that seeds `get_city_time_info`, weather/news lookups, and tone prompts.
- Instructions to click `[INIT]`, wait for `System Online`, and use the local `openwakeword` “Hey Jarvis” wake phrase once the wizard finishes.
The wizard explains that plugin discovery is metadata-first, download is confirm-gated, and every plugin still passes static security checks before saving.
