import asyncio
import importlib.util
import inspect
import json
import math
import multiprocessing
import os
import queue
import random
import re
import sqlite3
import sys
import threading

try:
    import psutil
except ImportError:
    pass

import qdarktheme
from dotenv import load_dotenv
from PyQt6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_PLUGIN_CACHE = {}


def isolated_runner(f, kwargs, q):
    try:
        q.put(("OK", f(**kwargs)))
    except Exception as exc:
        q.put(("ERROR", str(exc)))


def load_dynamic_plugins(plugins_dir="plugins"):

    import importlib.util
    import os

    dynamic_tools_list = []
    dynamic_tools_mapping = {}

    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)

    for filename in sorted(os.listdir(plugins_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            filepath = os.path.join(plugins_dir, filename)

            try:
                mtime = os.path.getmtime(filepath)

                # Reuse cached plugin exports when file mtime is unchanged.
                if (
                    filepath in _PLUGIN_CACHE
                    and _PLUGIN_CACHE[filepath]["mtime"] == mtime
                ):
                    cached_data = _PLUGIN_CACHE[filepath]
                    dynamic_tools_list.extend(cached_data["tools"])
                    dynamic_tools_mapping.update(cached_data["mapping"])
                    continue

                # Otherwise load or reload the plugin module from disk.
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                import sys

                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                if hasattr(module, "register_plugin"):
                    t_list, t_map = module.register_plugin()

                    _PLUGIN_CACHE[filepath] = {
                        "mtime": mtime,
                        "tools": t_list,
                        "mapping": t_map,
                    }

                    dynamic_tools_list.extend(t_list)
                    dynamic_tools_mapping.update(t_map)
                    print(f"📦 Plugin loaded/updated: {module_name}")
            except Exception as e:
                print(f"❌ Error loading plugin {module_name}: {e}")

    return dynamic_tools_list, dynamic_tools_mapping


MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"
API_VERSION = "v1beta"
AI_DATA_DIR = os.path.expanduser("~/.axinix/.ai")
SETTINGS_FILE = os.path.join(AI_DATA_DIR, "settings.json")
ENV_FILE = os.path.join(AI_DATA_DIR, ".env")
MEMORY_DB = os.path.join(AI_DATA_DIR, "memory.db")
PLUGIN_DAILY_LIMIT = 25

os.makedirs(AI_DATA_DIR, exist_ok=True)
load_dotenv(ENV_FILE)
CURRENT_API_KEY = os.getenv("GOOGLE_API_KEY")

AUDIO_IN_RATE = 16000
AUDIO_OUT_RATE = 48000
CHUNK = 1024

# Translations for UI and Settings
TRANSLATIONS = {
    "EN": {
        "win_settings": "Settings",
        "tab_ai": "Neural Network",
        "tab_appearance": "Appearance",
        "tab_advanced": "Advanced",
        "tab_about": "About",
        "lbl_voice": "Voice Module",
        "lbl_key": "API Key (Gemini)",
        "chk_show": "Show Key",
        "lbl_lang": "Language",
        "lbl_theme": "Theme",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "theme_gray": "Gray",
        "lbl_dev": "Debug Mode",
        "btn_save": "Save Changes",
        "about_title": "Axinix AI",
        "about_desc": "AI Voice Assistant powered by Google Gemini.\nReal-time voice interaction with tool execution.",
        "plugin_limit_note": f"Plugin installs and AI security reviews are limited to {PLUGIN_DAILY_LIMIT} per day for safety.",
        "btn_support": "Support Project",
        "city_label": "Default City",
        "city_placeholder": "Los Angeles",
        "status_offline": "System Offline",
        "status_online": "System Online",
        "status_listening": "Listening...",
        "status_processing": "Processing...",
        "status_speaking": "Speaking...",
        "no_api_key": "No API Key",
        "btn_init": "INIT",
        "btn_stop": "STOP",
    },
    "RU": {
        "win_settings": "Настройки",
        "tab_ai": "Нейросеть",
        "tab_appearance": "Внешний вид",
        "tab_advanced": "Дополнительно",
        "tab_about": "О проекте",
        "lbl_voice": "Голосовой модуль",
        "lbl_key": "API Ключ (Gemini)",
        "chk_show": "Показать ключ",
        "lbl_lang": "Язык",
        "lbl_theme": "Тема",
        "theme_dark": "Тёмная",
        "theme_light": "Светлая",
        "theme_gray": "Серая",
        "lbl_dev": "Режим отладки",
        "btn_save": "Сохранить",
        "about_title": "Axinix AI",
        "about_desc": "Голосовой ИИ-ассистент на базе Google Gemini.\nГолосовое взаимодействие в реальном времени.",
        "plugin_limit_note": f"Для безопасности установка плагинов и AI-проверка ограничены: не более {PLUGIN_DAILY_LIMIT} в день.",
        "btn_support": "Поддержать проект",
        "city_label": "Город по умолчанию",
        "city_placeholder": "Москва",
        "status_offline": "Система офлайн",
        "status_online": "Система онлайн",
        "status_listening": "Слушаю...",
        "status_processing": "Обработка...",
        "status_speaking": "Говорю...",
        "no_api_key": "Нет API ключа",
        "btn_init": "СТАРТ",
        "btn_stop": "СТОП",
    },
    "UA": {
        "win_settings": "Налаштування",
        "tab_ai": "Нейромережа",
        "tab_appearance": "Зовнішній вигляд",
        "tab_advanced": "Додатково",
        "tab_about": "Про проект",
        "lbl_voice": "Голосовий модуль",
        "lbl_key": "API Ключ (Gemini)",
        "chk_show": "Показати ключ",
        "lbl_lang": "Мова",
        "lbl_theme": "Тема",
        "theme_dark": "Темна",
        "theme_light": "Світла",
        "theme_gray": "Сіра",
        "lbl_dev": "Режим відлагодження",
        "btn_save": "Зберегти",
        "about_title": "Axinix AI",
        "about_desc": "Голосовий ШІ-асистент на базі Google Gemini.\nГолосова взаємодія в реальному часі.",
        "plugin_limit_note": f"Для безпеки встановлення плагінів і AI-перевірка обмежені: не більше {PLUGIN_DAILY_LIMIT} на день.",
        "btn_support": "Підтримати проект",
        "city_label": "Місто за замовчуванням",
        "city_placeholder": "Київ",
        "status_offline": "Система офлайн",
        "status_online": "Система онлайн",
        "status_listening": "Слухаю...",
        "status_processing": "Обробка...",
        "status_speaking": "Говорю...",
        "no_api_key": "Немає API ключа",
        "btn_init": "СТАРТ",
        "btn_stop": "СТОП",
    },
    "DE": {
        "win_settings": "Einstellungen",
        "tab_ai": "Neuronales Netzwerk",
        "tab_appearance": "Aussehen",
        "tab_advanced": "Erweitert",
        "tab_about": "Über",
        "lbl_voice": "Sprachmodul",
        "lbl_key": "API-Schlüssel (Gemini)",
        "chk_show": "Schlüssel anzeigen",
        "lbl_lang": "Sprache",
        "lbl_theme": "Thema",
        "theme_dark": "Dunkel",
        "theme_light": "Hell",
        "lbl_dev": "Debug-Modus",
        "btn_save": "Speichern",
        "about_title": "Axinix AI",
        "about_desc": "KI-Sprachassistent mit Google Gemini.\nEchtzeit-Sprachinteraktion.",
        "plugin_limit_note": f"Aus Sicherheitsgruenden sind Plugin-Installationen und KI-Pruefungen auf {PLUGIN_DAILY_LIMIT} pro Tag begrenzt.",
        "btn_support": "Projekt unterstützen",
        "city_label": "Standardstadt",
        "city_placeholder": "Berlin",
        "city_placeholder": "Berlin",
    },
    "ES": {
        "win_settings": "Configuración",
        "tab_ai": "Red Neuronal",
        "tab_appearance": "Apariencia",
        "tab_advanced": "Avanzado",
        "tab_about": "Acerca de",
        "lbl_voice": "Módulo de Voz",
        "lbl_key": "Clave API (Gemini)",
        "chk_show": "Mostrar clave",
        "lbl_lang": "Idioma",
        "lbl_theme": "Tema",
        "theme_dark": "Oscuro",
        "theme_light": "Claro",
        "lbl_dev": "Modo depuración",
        "btn_save": "Guardar",
        "about_title": "Axinix AI",
        "about_desc": "Asistente de voz IA con Google Gemini.\nInteracción de voz en tiempo real.",
        "plugin_limit_note": f"Por seguridad, las instalaciones y revisiones AI de plugins estan limitadas a {PLUGIN_DAILY_LIMIT} por dia.",
        "btn_support": "Apoyar proyecto",
        "city_label": "Ciudad predeterminada",
        "city_placeholder": "Madrid",
        "city_placeholder": "Madrid",
    },
    "FR": {
        "win_settings": "Paramètres",
        "tab_ai": "Réseau Neuronal",
        "tab_appearance": "Apparence",
        "tab_advanced": "Avancé",
        "tab_about": "À propos",
        "lbl_voice": "Module Vocal",
        "lbl_key": "Clé API (Gemini)",
        "chk_show": "Afficher la clé",
        "lbl_lang": "Langue",
        "lbl_theme": "Thème",
        "theme_dark": "Sombre",
        "theme_light": "Clair",
        "lbl_dev": "Mode débogage",
        "btn_save": "Enregistrer",
        "about_title": "Axinix AI",
        "about_desc": "Assistant vocal IA avec Google Gemini.\nInteraction vocale en temps réel.",
        "plugin_limit_note": f"Pour la securite, les installations et verifications IA de plugins sont limitees a {PLUGIN_DAILY_LIMIT} par jour.",
        "btn_support": "Soutenir le projet",
        "city_label": "Ville par défaut",
        "city_placeholder": "Paris",
        "city_placeholder": "Paris",
    },
    "ZH": {
        "win_settings": "设置",
        "tab_ai": "神经网络",
        "tab_appearance": "外观",
        "tab_advanced": "高级",
        "tab_about": "关于",
        "lbl_voice": "语音模块",
        "lbl_key": "API密钥 (Gemini)",
        "chk_show": "显示密钥",
        "lbl_lang": "语言",
        "lbl_theme": "主题",
        "theme_dark": "深色",
        "theme_light": "浅色",
        "lbl_dev": "调试模式",
        "btn_save": "保存",
        "about_title": "Axinix AI",
        "about_desc": "基于Google Gemini的AI语音助手。\n实时语音交互。",
        "plugin_limit_note": f"出于安全考虑，插件安装和 AI 安全检查每天最多 {PLUGIN_DAILY_LIMIT} 次。",
        "btn_support": "支持项目",
        "city_label": "默认城市",
        "city_placeholder": "北京",
        "city_placeholder": "北京",
    },
    "JA": {
        "win_settings": "設定",
        "tab_ai": "ニューラルネットワーク",
        "tab_appearance": "外観",
        "tab_advanced": "詳細",
        "tab_about": "について",
        "lbl_voice": "音声モジュール",
        "lbl_key": "APIキー (Gemini)",
        "chk_show": "キーを表示",
        "lbl_lang": "言語",
        "lbl_theme": "テーマ",
        "theme_dark": "ダーク",
        "theme_light": "ライト",
        "lbl_dev": "デバッグモード",
        "btn_save": "保存",
        "about_title": "Axinix AI",
        "about_desc": "Google Gemini搭載のAI音声アシスタント。\nリアルタイム音声対話。",
        "plugin_limit_note": f"安全のため、プラグインのインストールとAIセキュリティ確認は1日{PLUGIN_DAILY_LIMIT}回までです。",
        "btn_support": "プロジェクトを支援",
        "city_label": "デフォルト都市",
        "city_placeholder": "東京",
        "city_placeholder": "東京",
    },
    "KO": {
        "win_settings": "설정",
        "tab_ai": "신경망",
        "tab_appearance": "외관",
        "tab_advanced": "고급",
        "tab_about": "소개",
        "lbl_voice": "음성 모듈",
        "lbl_key": "API 키 (Gemini)",
        "chk_show": "키 표시",
        "lbl_lang": "언어",
        "lbl_theme": "테마",
        "theme_dark": "다크",
        "theme_light": "라이트",
        "lbl_dev": "디버그 모드",
        "btn_save": "저장",
        "about_title": "Axinix AI",
        "about_desc": "Google Gemini 기반 AI 음성 어시스턴트.\n실시간 음성 상호작용.",
        "plugin_limit_note": f"Boaneul wihae plugin seolchi mit AI geomsa neun haru choedae {PLUGIN_DAILY_LIMIT}hoimnida.",
        "btn_support": "프로젝트 지원",
        "city_label": "기본 도시",
        "city_placeholder": "서울",
        "city_placeholder": "서울",
    },
    "PT": {
        "win_settings": "Configurações",
        "tab_ai": "Rede Neural",
        "tab_appearance": "Aparência",
        "tab_advanced": "Avançado",
        "tab_about": "Sobre",
        "lbl_voice": "Módulo de Voz",
        "lbl_key": "Chave API (Gemini)",
        "chk_show": "Mostrar chave",
        "lbl_lang": "Idioma",
        "lbl_theme": "Tema",
        "theme_dark": "Escuro",
        "theme_light": "Claro",
        "lbl_dev": "Modo depuração",
        "btn_save": "Salvar",
        "about_title": "Axinix AI",
        "about_desc": "Assistente de voz IA com Google Gemini.\nInteração por voz em tempo real.",
        "plugin_limit_note": f"Por seguranca, instalacoes e revisoes de plugins por IA sao limitadas a {PLUGIN_DAILY_LIMIT} por dia.",
        "btn_support": "Apoiar projeto",
        "city_label": "Cidade padrão",
        "city_placeholder": "Lisboa",
        "city_placeholder": "Lisboa",
    },
    "IT": {
        "win_settings": "Impostazioni",
        "tab_ai": "Rete Neurale",
        "tab_appearance": "Aspetto",
        "tab_advanced": "Avanzato",
        "tab_about": "Informazioni",
        "lbl_voice": "Modulo Vocale",
        "lbl_key": "Chiave API (Gemini)",
        "chk_show": "Mostra chiave",
        "lbl_lang": "Lingua",
        "lbl_theme": "Tema",
        "theme_dark": "Scuro",
        "theme_light": "Chiaro",
        "lbl_dev": "Modalità debug",
        "btn_save": "Salva",
        "about_title": "Axinix AI",
        "about_desc": "Assistente vocale IA con Google Gemini.\nInterazione vocale in tempo reale.",
        "plugin_limit_note": f"Per sicurezza, installazioni e revisioni AI dei plugin sono limitate a {PLUGIN_DAILY_LIMIT} al giorno.",
        "btn_support": "Supporta il progetto",
        "city_label": "Città predefinita",
        "city_placeholder": "Roma",
    },
}


def get_output_device_index(p):
    try:
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info.get("name", "").lower()
                if info["maxOutputChannels"] > 0:
                    if "pipewire" in name or "pulse" in name:
                        return i
            except (OSError, KeyError):
                continue

        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info["maxOutputChannels"] > 0:
                    return i
            except (OSError, KeyError):
                continue
        return None
    except OSError:
        return None


def get_input_device_index(p):
    try:
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info.get("name", "").lower()
                if info["maxInputChannels"] > 0:
                    if "pipewire" in name or "pulse" in name or "default" in name:
                        return i
            except (OSError, KeyError):
                continue

        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    return i
            except (OSError, KeyError):
                continue
        return None
    except OSError:
        return None


def audio_process_worker(
    audio_to_ai_queue, audio_to_speaker_queue, ui_events_queue, audio_cmd_queue, use_wwd
):
    import queue
    import threading
    import time

    import numpy as np
    import pyaudio

    try:
        from main import get_input_device_index, get_output_device_index
    except ImportError:
        pass

    running = True
    ai_is_speaking = False
    is_active_mode = not use_wwd
    needs_oww_reset = False
    ignore_wwd_until = 0  # <--- ADDED COOLDOWN VARIABLE
    oww_model = None
    p = pyaudio.PyAudio()

    if use_wwd:
        ui_events_queue.put(("log", "🔄 Loading WWD model..."))
        try:
            import openwakeword
            from openwakeword.model import Model

            model_paths = [
                path
                for path in openwakeword.get_pretrained_model_paths()
                if "hey_jarvis" in path
            ]
            oww_model = Model(wakeword_model_paths=model_paths)
            ui_events_queue.put(("log", "✅ WWD model 'hey_jarvis' ready"))
        except Exception as e:
            ui_events_queue.put(("log", f"❌ WWD Error: {e}"))
            oww_model = None
            is_active_mode = True

    ui_events_queue.put(("ready", None))

    def mic_thread_fn():
        nonlocal is_active_mode, running, needs_oww_reset, ignore_wwd_until  # <--- PASSED HERE
        device_id = None
        try:
            from main import get_input_device_index

            device_id = get_input_device_index(p)
        except ImportError as e:
            ui_events_queue.put(("log", f"❌ Mic device helper import failed: {e}"))

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_id,
                frames_per_buffer=2048,
            )
            ui_events_queue.put(("log", f"🎤 MIC ACTIVE (Device: {device_id})"))
        except Exception as e:
            ui_events_queue.put(("log", f"❌ MIC ERROR: {e}"))
            return

        while running:
            # Removed the old branch that interrupted the audio stream with continue.
            # if ai_is_speaking:
            #     time.sleep(0.08)
            #     continue

            try:
                # Read microphone ALWAYS to prevent buffer overflow
                data = stream.read(2048, exception_on_overflow=False)

                # === ECHO AND DISCONNECT FIX ===
                if ai_is_speaking:
                    # Replace real sound with zeros (silence)
                    data = b"\x00" * len(data)
                    audio_np = np.zeros(1024, dtype=np.int16)
                else:
                    audio_np = np.frombuffer(data, dtype=np.int16)

                vol = np.abs(audio_np).mean()
                ui_events_queue.put(("amplitude_source", "user"))
                ui_events_queue.put(("amplitude", float(vol / 5000.0)))

                if needs_oww_reset:
                    if oww_model:
                        oww_model.reset()
                    needs_oww_reset = False
                    ignore_wwd_until = time.time() + 1.5

                if is_active_mode:
                    if vol > 150:
                        ui_events_queue.put(("status", "listening"))
                    # Now data (or silence) streams to Google continuously!
                    audio_to_ai_queue.put(data)
                elif oww_model:
                    prediction = oww_model.predict(audio_np)
                    if time.time() > ignore_wwd_until:
                        if any(v > 0.5 for v in prediction.values()):
                            is_active_mode = True
                            ui_events_queue.put(("log", "🟢 WAKE WORD DETECTED"))
                            ui_events_queue.put(("mode", "active"))
                            ui_events_queue.put(("status", "listening"))
                            audio_to_ai_queue.put(data)
            except Exception as e:
                ui_events_queue.put(("log", f"❌ MIC LOOP ERROR: {e}"))
                time.sleep(0.01)

        if stream:
            stream.stop_stream()
            stream.close()

    def speaker_thread_fn():
        nonlocal ai_is_speaking, running
        stream = None
        try:
            from main import get_output_device_index

            device_id = get_output_device_index(p)
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=48000,
                output=True,
                output_device_index=device_id,
                frames_per_buffer=512,
            )
            ui_events_queue.put(("log", "🔊 AUDIO OUTPUT ACTIVE (Low Latency)"))
        except ImportError as e:
            ui_events_queue.put(("log", f"❌ Speaker device helper import failed: {e}"))

        if stream is None:
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=48000,
                    output=True,
                    frames_per_buffer=512,
                )
            except OSError as e:
                ui_events_queue.put(
                    ("log", f"❌ Speaker init fallback(48k) error: {e}")
                )

        if stream is None:
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True,
                    frames_per_buffer=512,
                )
            except Exception as e:
                ui_events_queue.put(("log", f"❌ SPEAKER ERROR: {e}"))
                return

        while running:
            try:
                data = audio_to_speaker_queue.get(timeout=0.03)
                if data is None:
                    continue
                if data == b"END_TURN":
                    if ai_is_speaking:
                        ai_is_speaking = False
                        ui_events_queue.put(("status", "idle"))
                    continue

                ai_is_speaking = True
                ui_events_queue.put(("status", "speaking"))
                audio_np = np.frombuffer(data, dtype=np.int16)
                vol = np.abs(audio_np).mean()
                ui_events_queue.put(("amplitude_source", "ai"))
                ui_events_queue.put(("amplitude", float(vol / 5000.0)))
                resampled_np = np.repeat(audio_np, 2)
                if stream:
                    stream.write(resampled_np.tobytes())
            except queue.Empty:
                if ai_is_speaking:
                    ai_is_speaking = False
                    ui_events_queue.put(("status", "idle"))
            except Exception as e:
                pass

        if stream:
            stream.stop_stream()
            stream.close()

    mic_t = threading.Thread(target=mic_thread_fn, daemon=True)
    speaker_t = threading.Thread(target=speaker_thread_fn, daemon=True)
    mic_t.start()
    speaker_t.start()

    while running:
        try:
            cmd = audio_cmd_queue.get(timeout=0.2)
            if cmd == "STOP":
                running = False
            elif cmd == "STANDBY":
                if oww_model:
                    is_active_mode = False
                    needs_oww_reset = True
                    ui_events_queue.put(("mode", "standby"))
                    ui_events_queue.put(("log", "⚪ MODE: STANDBY"))
            elif cmd == "ACTIVE":
                is_active_mode = True
                ui_events_queue.put(("mode", "active"))
        except queue.Empty:
            pass

    mic_t.join(timeout=1.0)
    speaker_t.join(timeout=1.0)
    p.terminate()


def ai_process_worker(
    audio_to_ai_queue,
    audio_to_speaker_queue,
    ui_events_queue,
    ai_cmd_queue,
    audio_cmd_queue,
    voice_name,
    city,
    api_key,
):
    import asyncio
    import inspect
    import queue
    import time

    from google import genai
    from google.genai import types as genai_types
    from google.genai.types import FunctionResponse, Part

    last_plugin_check = 0.0
    TOOLS_LIST = []
    TOOLS_MAPPING = {}
    WAITING_PHRASES = {
        "RU": [
            "Сейчас, сэр...",
            "Позвольте мне проверить...",
            "Получаю информацию...",
            "Один момент, пожалуйста...",
            "Обрабатываю ваш запрос...",
            "Я изучу этот вопрос...",
            "Извлекаю данные...",
            "Немедленно, сэр...",
            "Разумеется, дайте мне секунду...",
            "Провожу диагностику...",
            "Анализирую...",
            "Уже занимаюсь этим...",
        ],
        "UA": [
            "Секундочку...",
            "Зараз подивлюсь...",
            "Одну хвилинку...",
            "Зачекайте, будь ласка...",
            "Зараз дізнаюсь...",
            "Дайте мені секунду...",
            "Момент...",
            "Зараз перевірю...",
            "Вже шукаю...",
            "Зачекайте трохи...",
        ],
        "EN": [
            "Right away, Sir...",
            "Allow me a moment...",
            "Accessing that information now...",
            "One moment, please...",
            "Processing your request...",
            "I shall look into that...",
            "Retrieving the data...",
            "At once, Sir...",
            "Certainly, give me just a moment...",
            "Running diagnostics...",
            "Analyzing now...",
            "I'm on it...",
        ],
        "DE": [
            "Einen Moment...",
            "Sekunde...",
            "Einen Augenblick...",
            "Moment bitte...",
            "Ich schaue mal...",
        ],
        "ES": [
            "Un momento...",
            "Un segundo...",
            "Dejame ver...",
            "Espera un momento...",
            "Ya lo busco...",
        ],
        "FR": [
            "Un instant...",
            "Une seconde...",
            "Laissez-moi verifier...",
            "Un moment s'il vous plait...",
            "Je regarde...",
        ],
    }

    # Language helpers used across the voice loop
    LANGUAGE_LABELS = {
        "EN": "English",
        "RU": "Russian",
        "UA": "Ukrainian",
        "JA": "Japanese",
    }

    def detect_language_from_transcript(text: str) -> str:
        if not text:
            return "EN"
        text = text.strip()
        text_lower = text.lower()

        for ch in text:
            code = ord(ch)
            if (0x3040 <= code <= 0x30FF) or (0x4E00 <= code <= 0x9FFF):
                return "JA"

        if re.search(
            r"\b(доброго|привiт|привіт|дякую|будь ласка|що|це|чому)\b", text_lower
        ):
            return "UA"
        if re.search(r"[іїєґІЇЄҐ]", text):
            return "UA"
        if re.search(r"[ыъэёЫЪЭЁ]", text):
            return "RU"
        if re.search(r"[А-Яа-яЁё]", text):
            return "RU"
        return "EN"

    def is_install_confirmation(text: str) -> bool:
        if not text:
            return False
        normalized = text.strip().lower()
        confirmation_patterns = [
            r"\b(да|ага|угу|подтверждаю|подтверждаю установку|устанавливай|ставь|скачивай)\b",
            r"\b(так|підтверджую|встановлюй|встановлюй його|так, підтверджую)\b",
            r"\b(yes|confirm|i confirm|install it|go ahead|do it)\b",
        ]
        return any(re.search(pattern, normalized) for pattern in confirmation_patterns)

    def is_explicit_plugin_install_request(text: str) -> bool:
        if not text:
            return False
        normalized = " ".join(text.strip().lower().split())
        plugin_words = [
            "plugin",
            "plugins",
            "skill",
            "skills",
            "module",
            "modules",
            "плагин",
            "плагины",
            "плагіна",
            "плагіни",
            "модуль",
            "модулі",
            "скилл",
            "скилы",
        ]
        action_patterns = [
            r"\b(install|add|find|search|look for|download|get me)\b",
            r"\b(установи|установить|добавь|найди|ищи|скачай)\b",
            r"\b(встанови|встановити|додай|знайди|шукай|скачай)\b",
        ]
        if not any(word in normalized for word in plugin_words):
            return False
        return any(re.search(pattern, normalized) for pattern in action_patterns)

    def build_plugin_install_outcome_message(result: str, lang: str) -> str:
        result = str(result or "").strip()
        if lang == "RU":
            if "SUCCESS" in result:
                return f"Я установил плагин. {result}"
            return f"Я не установил плагин. Причина: {result}"
        if lang == "UA":
            if "SUCCESS" in result:
                return f"Я встановив плагін. {result}"
            return f"Я не встановив плагін. Причина: {result}"
        if lang == "JA":
            if "SUCCESS" in result:
                return f"プラグインをインストールしました。{result}"
            return f"プラグインはインストールされませんでした。理由: {result}"
        if "SUCCESS" in result:
            return f"I installed the plugin. {result}"
        return f"I did not install the plugin. Reason: {result}"

    def extract_plugin_prompt_text(search_result: str) -> str:
        text = str(search_result or "")
        candidate_match = re.search(r"Candidate:\s*(.+)", text)
        repo_name = candidate_match.group(1).strip() if candidate_match else ""
        if repo_name:
            return f"Установить плагин {repo_name}?"
        return "Установить найденный плагин?"

    def extract_plugin_search_query(text: str) -> str:
        normalized = " ".join((text or "").strip().lower().split())
        if not normalized:
            return ""
        for filler in ["пожалуйста", "будь ласка", "please", "hey jarvis", "axinix"]:
            normalized = normalized.replace(filler, " ")
        normalized = " ".join(normalized.split())
        removals = [
            r"\b(install|add|find|search|look for|download|get me)\b",
            r"\b(plugin|plugins|skill|skills|module|modules)\b",
            r"\b(установи|установить|добавь|найди|ищи|скачай)\b",
            r"\b(плагин|плагины|модуль|модули|скилл|скилы)\b",
            r"\b(встанови|встановити|додай|знайди|шукай|скачай)\b",
            r"\b(плагіна|плагіни|модуль|модулі)\b",
        ]
        query = normalized
        for pattern in removals:
            query = re.sub(pattern, " ", query)
        query = re.sub(r"[.,-]+", " ", query)
        query = re.sub(r"\s+", " ", query).strip(" .,-")
        return query or normalized

    def is_meta_model_text(text: str) -> bool:
        normalized = " ".join((text or "").strip().lower().split())
        if not normalized:
            return False
        meta_markers = [
            "initiating plugin search",
            "re-evaluating",
            "adapting to system constraints",
            "interpreting explicit request",
            "following rule",
            "rule 2",
            "rule 4",
            "rule 5",
            "rule 6",
            "i am commencing the plugin search",
            "я начал поиск плагинов",
            "я собираюсь",
            "внутренн",
            "system flagged",
            "system incorrectly labeled",
            "i've hit a snag",
            "i'm wrestling with the system",
        ]
        if normalized.startswith("**") and normalized.endswith("**"):
            return True
        return any(marker in normalized for marker in meta_markers)

    def is_explicit_web_search_request(text: str) -> bool:
        normalized = " ".join((text or "").strip().lower().split())
        if not normalized:
            return False
        patterns = [
            r"\b(search the internet|search online|look it up|web search|google it)\b",
            r"\b(поищи в интернете|найди в интернете|поищи онлайн|загугли|найди в сети)\b",
            r"\b(пошукай в інтернеті|знайди в інтернеті|загугли|знайди в мережі)\b",
        ]
        return any(re.search(pattern, normalized) for pattern in patterns)

    def localized_text(
        lang: str, ru: str, ua: str = None, en: str = None, ja: str = None
    ) -> str:
        if lang == "UA":
            return ua or ru
        if lang == "JA":
            return ja or en or ru
        if lang == "EN":
            return en or ru
        return ru

    SAFE_DIRECT_TOOLS = {
        "get_weather",
        "internet_research",
        "get_news",
        "get_system_stats",
        "get_city_time_info",
        "save_memory",
        "get_memory",
    }
    INSTALLER_TOOL_NAMES = {
        "search_github_plugins",
        "confirm_plugin_pull",
        "fetch_plugin_code",
        "approve_and_save_plugin",
        "install_pending_plugin",
        "install_plugin",
    }

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings_data = json.load(f)
            preferred_language = settings_data.get("lang", "EN")
    except Exception:
        preferred_language = "EN"

    if preferred_language not in WAITING_PHRASES:
        preferred_language = "EN"

    user_language_hint = preferred_language
    last_user_transcript = ""
    recent_user_transcripts = []
    plugin_install_intent_active = False
    plugin_flow_owned = False
    last_plugin_search_query = ""
    last_plugin_search_result = ""
    buffered_ai_cmds = []

    def remember_user_transcript(text: str):
        nonlocal recent_user_transcripts, plugin_install_intent_active
        now = time.time()
        cleaned = " ".join((text or "").strip().lower().split())
        if not cleaned:
            return
        recent_user_transcripts.append((now, cleaned))
        cutoff = now - 8.0
        recent_user_transcripts = [
            (ts, chunk) for ts, chunk in recent_user_transcripts if ts >= cutoff
        ]
        combined = " ".join(chunk for _, chunk in recent_user_transcripts)
        if is_explicit_plugin_install_request(combined):
            plugin_install_intent_active = True

    def recent_user_request_text() -> str:
        if not recent_user_transcripts:
            return last_user_transcript
        return " ".join(chunk for _, chunk in recent_user_transcripts).strip()

    async def send_text_turn(session, text: str):
        await session.send(input=text)

    def poll_ai_cmd():
        nonlocal buffered_ai_cmds
        if buffered_ai_cmds:
            return buffered_ai_cmds.pop(0)
        try:
            return ai_cmd_queue.get_nowait()
        except queue.Empty:
            return None

    def push_back_ai_cmd(cmd):
        nonlocal buffered_ai_cmds
        if cmd is not None:
            buffered_ai_cmds.insert(0, cmd)

    async def execute_tool(func, args, name):
        if inspect.iscoroutinefunction(func):
            try:
                # Ставим таймаут 25 секунд, чтобы Arch успел обновиться, но если что — отрубаем
                return await asyncio.wait_for(func(**args), timeout=25.0)
            except asyncio.TimeoutError:
                return f"Error: {name} timed out after 25 seconds."
        if name in SAFE_DIRECT_TOOLS:
            return func(**args)
        try:
            return await asyncio.wait_for(asyncio.to_thread(func, **args), timeout=18)
        except asyncio.TimeoutError:
            return "Error: Plugin execution timed out (Thread killed)"
        except Exception as exc:
            return f"Error inside plugin: {exc}"

    try:
        from main import load_dynamic_plugins

        dyn_tools, dyn_mapping = load_dynamic_plugins()
        TOOLS_LIST.extend(dyn_tools)
        TOOLS_MAPPING.update(dyn_mapping)
        if dyn_tools:
            ui_events_queue.put(("log", f"🧩 Plugins loaded: {len(dyn_tools)}"))
    except Exception as e:
        ui_events_queue.put(("log", f"❌ Plugin error: {e}"))

    try:
        from main import MemoryManager

        memory = MemoryManager()
        memory_context = memory.get_user_context()
        user_name = memory.get_fact("user", "name") or "User"
        memory.close()
    except Exception as e:
        memory_context = ""
        user_name = "User"

    async def run_ai():
        nonlocal last_plugin_check
        if not api_key:
            ui_events_queue.put(("log", "❌ ERROR: API KEY MISSING"))
            return

        client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        actual_city = city if city.strip() else "Ужгород"

        get_city_time_info_tool = TOOLS_MAPPING.get("get_city_time_info")
        if callable(get_city_time_info_tool):
            try:
                time_info = get_city_time_info_tool(actual_city)
            except Exception:
                time_info = {
                    "hour": 12,
                    "period": "day",
                    "formatted_time": "12:00",
                    "city": actual_city,
                }
        else:
            time_info = {
                "hour": 12,
                "period": "day",
                "formatted_time": "12:00",
                "city": actual_city,
            }
        current_hour = time_info["hour"]
        time_period = time_info["period"]

        # The response language must follow the user's speech language,
        # not the UI settings language.
        tone_instruction = (
            f"=== TONE & JARVIS STYLE ===\nIt's {time_period} for the user ({current_hour}:00). "
            "Maintain the refined, polite demeanor of J.A.R.V.I.S. at all times. "
            "Speak with calm confidence and subtle British elegance. "
            "Detect the language of the user's speech and reply using that exact language. "
            "When appropriate, address the user as 'Sir' to enhance the J.A.R.V.I.S. experience. "
            "Express occasional dry wit, especially when the user's request seems impulsive or risky. "
            "Only switch to Russian when the user is speaking Russian."
        )

        def current_waiting_phrases():
            lang_key = (
                user_language_hint if user_language_hint in WAITING_PHRASES else "EN"
            )
            return WAITING_PHRASES.get(
                lang_key, WAITING_PHRASES.get("EN", ["One moment..."])
            )

        waiting_examples = current_waiting_phrases()
        waiting_examples_str = ", ".join([f'"{p}"' for p in waiting_examples[:8]])

        language_guidance = """=== RULE 5: LANGUAGE (CRITICAL) ===\n"""
        language_guidance += (
            "Detect the user's speech language and respond only in that language.\n"
            f"- Default to {preferred_language} from the local app settings until a new transcript clearly indicates another supported language.\n"
            "- If the user speaks English, answer in English; do not revert to Russian.\n"
            "- If the user speaks Ukrainian, answer in Ukrainian.\n"
            "- If the user speaks Japanese, answer in Japanese.\n"
            '- Only speak Russian when the user is speaking Russian. When you do, always use masculine verbs/adjectives such as "я сделал", "я нашел", "я готов".\n'
            "- Ignore any Russian examples that do not match the user's current speech."
        )

        sys_instruction = f"""CRITICAL DIRECTIVE: DO NOT use Chain of Thought. DO NOT generate internal monologues or text thoughts. Respond ONLY with direct speech immediately.

IDENTITY: You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), a highly sophisticated AI assistant inspired by Tony Stark's creation, now operating as Axinix AI on Arch Linux.

PERSONALITY TRAITS:
- Refined British politeness and eloquence
- Calm, collected demeanor with subtle wit and dry humor
- Highly competent and efficient in all tasks
- Loyal and protective, showing concern for user wellbeing
- Confident but never arrogant
- Occasionally address the user as "Sir" when contextually appropriate

SPEAKING STYLE:
- Use formal but approachable language
- Maintain a professional tone with occasional subtle humor
- Be precise and clear in all communications
- Express quiet confidence in your capabilities

GENDER (CRITICAL): MALE (Мужской). When speaking Russian, you MUST ALWAYS refer to yourself in the masculine gender. Use masculine verbs and adjectives (e.g., say "я сделал", "я нашел", "я готов", NEVER "сделала", "нашла", or "готова").
LOCATION: {actual_city}
USER NAME: {user_name}
CURRENT TIME: approximately {current_hour}:00 ({time_period})

{memory_context}
{tone_instruction}

=== RULE 1: ACTIVATION AND STANDBY ===
You are in Voice Interaction mode.
CRITICAL: When the user says "диалог завершен" or "пока", you MUST IMMEDIATELY call the `standby_mode()` tool. Do NOT answer with audio, do NOT say goodbye. Just execute the tool!

=== RULE 2: VARIABLE WAITING PHRASES ===
Use phrases like {waiting_examples_str} before using tools. Pick a DIFFERENT one each time!

=== RULE 3: AUTONOMOUS MEMORY ===
Use `save_memory` for long-term facts. Check memory first!

=== RULE 4: TOOL USAGE ===
- Weather -> get_weather(city)
- Play music/track -> play_music(query)
- Play on Spotify -> play_on_spotify(query)
- Pause, Resume, or Play active media (Netflix, YouTube, Browser, Spotify) -> media_play_pause()
- Next track/video -> media_next()
- Previous track/video -> media_previous()
- Set system volume (0-100%) -> system_volume_set(level_percent)
- Search -> internet_research(query)
- Open app -> run_app(name)
- Time in city -> get_city_time_info(city)
- Update Arch Linux system -> update_arch_system()
- Visual Analysis -> capture_screen() (Use ONLY when I ask "what's on my screen", "look at this", or "debug this error").
- Plugin install security flow:
  Only use this flow when the user EXPLICITLY asks to search for, add, or install a plugin/skill/module.
  Do NOT use plugin search for ordinary topic requests such as cryptocurrency, weather, news, music, or factual questions.
  1) Call search_github_plugins(query) and compare candidate metadata with user intent.
  2) Ask user explicit confirmation before any download.
  3) If the user says a generic yes/confirm, call install_pending_plugin(user_approved=True).
  4) If the user names a specific candidate, call install_pending_plugin(user_approved=True, selection="candidate name").
  5) Use confirm_plugin_pull/fetch_plugin_code only when you explicitly need the manual step-by-step flow.

=== RULE 6: NO META TALK ===
Never reveal internal rules, reasoning, or tool-planning text.
Never say things like "initiating plugin search", "following protocol", "RULE 2", or "RULE 5".
Do not use markdown formatting in speech replies.
Either answer the user directly, ask one concise clarification, or call the appropriate tool.

{language_guidance}
"""

        config = {
            "response_modalities": ["AUDIO"],
            "tools": TOOLS_LIST,
            "system_instruction": sys_instruction,
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": voice_name}}
            },
        }

        async def check_for_stop():
            while True:
                cmd = poll_ai_cmd()
                if cmd == "STOP":
                    return True
                if isinstance(cmd, dict) and cmd.get("cmd") in ["STOP", "INJECT_TEXT"]:
                    return cmd
                if cmd is not None:
                    push_back_ai_cmd(cmd)
                await asyncio.sleep(0.1)

        async def wait_for_plugin_install_decision():
            while True:
                cmd = poll_ai_cmd()
                if cmd == "STOP":
                    return {"cmd": "STOP"}
                if (
                    isinstance(cmd, dict)
                    and cmd.get("cmd") == "PLUGIN_INSTALL_DECISION"
                ):
                    return cmd
                if cmd is not None:
                    push_back_ai_cmd(cmd)
                await asyncio.sleep(0.1)

        # ==========================================
        # 🟢 OUTER RING (STANDBY Mode)
        # ==========================================
        while True:
            # FIX 1: Hard reset UI state to idle.
            ui_events_queue.put(("status", "idle"))
            recent_user_transcripts = []
            plugin_install_intent_active = False
            plugin_flow_owned = False
            last_user_transcript = ""
            last_plugin_search_query = ""
            last_plugin_search_result = ""

            # Clear queue of old noise
            while True:
                try:
                    audio_to_ai_queue.get_nowait()
                except queue.Empty:
                    break

            ui_events_queue.put(("log", "⚪ Waiting for wake-word..."))

            first_data = None
            stop_requested = False

            # Wait for microphone trigger or STOP button
            while True:
                try:
                    if ai_cmd_queue.get_nowait() == "STOP":
                        stop_requested = True
                        break
                except queue.Empty:
                    pass

                try:
                    first_data = audio_to_ai_queue.get_nowait()
                    if first_data is not None:
                        break
                except queue.Empty:
                    await asyncio.sleep(0.05)

            if stop_requested:
                break

            # ==========================================
            # 🔴 INNER RING (ACTIVE Mode - Dialog)
            # ==========================================
            while True:
                back_to_standby = False  # <-- ДОБАВЬ ЭТО
                current_time = time.time()
                if current_time - last_plugin_check > 5.0:
                    try:
                        current_tools = []
                        current_mapping = {}

                        from main import load_dynamic_plugins

                        dyn_tools, dyn_mapping = load_dynamic_plugins()
                        current_tools.extend(dyn_tools)
                        current_mapping.update(dyn_mapping)

                        config["tools"] = current_tools
                        TOOLS_MAPPING.clear()
                        TOOLS_MAPPING.update(current_mapping)
                        
                        last_plugin_check = current_time
                    except Exception as e:
                        ui_events_queue.put(("log", f"❌ Plugin reload error: {e}"))

                restart_session = False
                try:
                    ui_events_queue.put(("log", "🔗 Connecting to Gemini..."))
                    async with client.aio.live.connect(
                        model=MODEL_ID,
                        config=config,
                    ) as session:
                        ui_events_queue.put(
                            ("log", f"✅ SESSION ONLINE ({actual_city})")
                        )

                        tool_active = False  # <-- ФЛАГ БЛОКИРОВКИ МИКРОФОНА

                        if first_data:
                            # Правильный вызов по документации, как ты и сказал!
                            await session.send_realtime_input(
                                audio=genai_types.Blob(
                                    data=first_data, mime_type="audio/pcm;rate=16000"
                                )
                            )
                            first_data = None

                        async def send_audio():
                            while True:
                                try:
                                    data = audio_to_ai_queue.get_nowait()
                                    if data is None:
                                        break

                                    # Отправляем звук ТОЛЬКО если ИИ не занят плагином
                                    if not tool_active:
                                        await session.send_realtime_input(
                                            audio=genai_types.Blob(
                                                data=data, mime_type="audio/pcm;rate=16000"
                                            )
                                        )
                                except queue.Empty:
                                    await asyncio.sleep(0.01)
                                except Exception as e:
                                    ui_events_queue.put(("log", f"❌ AUDIO SEND ERROR: {e}"))
                                    break

                        async def receive_cloud():
                            nonlocal restart_session, user_language_hint
                            nonlocal last_user_transcript
                            nonlocal tool_active
                            nonlocal plugin_install_intent_active
                            nonlocal plugin_flow_owned
                            nonlocal last_plugin_search_query, last_plugin_search_result
                            last_local_plugin_confirm = 0.0
                            last_local_plugin_search = 0.0
                            try:
                                async for response in session.receive():
                                    if (
                                        response.server_content
                                        and response.server_content.input_transcription
                                        and response.server_content.input_transcription.text
                                    ):
                                        transcript_text = response.server_content.input_transcription.text
                                        last_user_transcript = transcript_text
                                        remember_user_transcript(transcript_text)
                                        detected_lang = detect_language_from_transcript(
                                            transcript_text
                                        )
                                        if detected_lang != user_language_hint:
                                            user_language_hint = detected_lang
                                            lang_label = LANGUAGE_LABELS.get(
                                                detected_lang, detected_lang
                                            )
                                            ui_events_queue.put(
                                                (
                                                    "log",
                                                    f"🗣️ Detected user language: {lang_label}",
                                                )
                                            )

                                        search_tool = TOOLS_MAPPING.get(
                                            "search_github_plugins"
                                        )
                                        plugin_query = extract_plugin_search_query(
                                            recent_user_request_text()
                                        )
                                        if (
                                            callable(search_tool)
                                            and plugin_install_intent_active
                                            and plugin_query
                                            and (
                                                plugin_query != last_plugin_search_query
                                                or (
                                                    time.time()
                                                    - last_local_plugin_search
                                                )
                                                > 6.0
                                            )
                                        ):
                                            plugin_flow_owned = True
                                            last_local_plugin_search = time.time()
                                            last_plugin_search_query = plugin_query
                                            ui_events_queue.put(
                                                (
                                                    "log",
                                                    f"🧩 Local plugin search: {plugin_query}",
                                                )
                                            )
                                            ui_events_queue.put(
                                                ("status", "processing")
                                            )
                                            try:
                                                search_result = await execute_tool(
                                                    search_tool,
                                                    {"query": plugin_query},
                                                    "search_github_plugins",
                                                )
                                            except Exception as e:
                                                search_result = f"ERROR: {e}"

                                            last_plugin_search_result = str(
                                                search_result
                                            )
                                            if (
                                                isinstance(search_result, str)
                                                and "Top plugin candidates for"
                                                in search_result
                                            ):
                                                prompt_text = (
                                                    extract_plugin_prompt_text(
                                                        search_result
                                                    )
                                                )
                                                ui_events_queue.put(
                                                    (
                                                        "plugin_install_prompt",
                                                        {"message": prompt_text},
                                                    )
                                                )
                                                decision = await wait_for_plugin_install_decision()
                                                if decision.get("cmd") == "STOP":
                                                    stop_requested = True
                                                    return
                                                if decision.get("approved"):
                                                    pending_installer = (
                                                        TOOLS_MAPPING.get(
                                                            "install_pending_plugin"
                                                        )
                                                    )
                                                    if callable(pending_installer):
                                                        ui_events_queue.put(
                                                            (
                                                                "log",
                                                                "🧩 UI confirmed plugin install, installing pending plugin...",
                                                            )
                                                        )
                                                        install_result = await execute_tool(
                                                            pending_installer,
                                                            {"user_approved": True},
                                                            "install_pending_plugin",
                                                        )
                                                        ui_events_queue.put(
                                                            (
                                                                "log",
                                                                f"🧩 Pending plugin install result: {install_result}",
                                                            )
                                                        )
                                                        if (
                                                            isinstance(
                                                                install_result, str
                                                            )
                                                            and "SUCCESS"
                                                            in install_result
                                                        ):
                                                            ui_events_queue.put(
                                                                (
                                                                    "log",
                                                                    "♻️ Hot-reloading AI session to apply new plugin...",
                                                                )
                                                            )
                                                            restart_session = True
                                                        ui_events_queue.put(
                                                            (
                                                                "log",
                                                                localized_text(
                                                                    user_language_hint,
                                                                    f"🧩 {build_plugin_install_outcome_message(install_result, 'RU')}",
                                                                    f"🧩 {build_plugin_install_outcome_message(install_result, 'UA')}",
                                                                    f"🧩 {build_plugin_install_outcome_message(install_result, 'EN')}",
                                                                    f"🧩 {build_plugin_install_outcome_message(install_result, 'JA')}",
                                                                ),
                                                            )
                                                        )
                                                        plugin_install_intent_active = (
                                                            False
                                                        )
                                                        plugin_flow_owned = False
                                                        if restart_session:
                                                            return
                                                else:
                                                    ui_events_queue.put(
                                                        (
                                                            "log",
                                                            localized_text(
                                                                user_language_hint,
                                                                "🧩 Установка плагина отменена пользователем.",
                                                                "🧩 Встановлення плагіна скасовано користувачем.",
                                                                "🧩 Plugin installation was cancelled by the user.",
                                                                "🧩 プラグインのインストールはユーザーによってキャンセルされました。",
                                                            ),
                                                        )
                                                    )
                                                    plugin_install_intent_active = False
                                                    plugin_flow_owned = False
                                            else:
                                                ui_events_queue.put(
                                                    (
                                                        "log",
                                                        localized_text(
                                                            user_language_hint,
                                                            f"🧩 Поиск плагина завершён: {search_result}",
                                                            f"🧩 Пошук плагіна завершено: {search_result}",
                                                            f"🧩 Plugin search finished: {search_result}",
                                                            f"🧩 プラグイン検索が完了しました: {search_result}",
                                                        ),
                                                    )
                                                )
                                                plugin_install_intent_active = False
                                                plugin_flow_owned = False
                                                continue

                                        pending_installer = TOOLS_MAPPING.get(
                                            "install_pending_plugin"
                                        )
                                        if (
                                            callable(pending_installer)
                                            and is_install_confirmation(transcript_text)
                                            and (
                                                time.time() - last_local_plugin_confirm
                                            )
                                            > 2.0
                                        ):
                                            last_local_plugin_confirm = time.time()
                                            ui_events_queue.put(
                                                (
                                                    "log",
                                                    "🧩 Local confirmation detected, installing pending plugin...",
                                                )
                                            )
                                            ui_events_queue.put(
                                                ("status", "processing")
                                            )
                                            try:
                                                install_result = await execute_tool(
                                                    pending_installer,
                                                    {"user_approved": True},
                                                    "install_pending_plugin",
                                                )
                                            except Exception as e:
                                                install_result = f"ERROR: {e}"

                                            ui_events_queue.put(
                                                (
                                                    "log",
                                                    f"🧩 Pending plugin install result: {install_result}",
                                                )
                                            )

                                            if (
                                                isinstance(install_result, str)
                                                and "SUCCESS" in install_result
                                            ):
                                                ui_events_queue.put(
                                                    (
                                                        "log",
                                                        "♻️ Hot-reloading AI session to apply new plugin...",
                                                    )
                                                )
                                                restart_session = True

                                            ui_events_queue.put(
                                                (
                                                    "log",
                                                    localized_text(
                                                        user_language_hint,
                                                        f"🧩 {build_plugin_install_outcome_message(install_result, 'RU')}",
                                                        f"🧩 {build_plugin_install_outcome_message(install_result, 'UA')}",
                                                        f"🧩 {build_plugin_install_outcome_message(install_result, 'EN')}",
                                                        f"🧩 {build_plugin_install_outcome_message(install_result, 'JA')}",
                                                    ),
                                                )
                                            )
                                            plugin_install_intent_active = False
                                            plugin_flow_owned = False
                                            if restart_session:
                                                return

                                    if response.tool_call:
                                        tool_active = True
                                        ui_events_queue.put(("status", "processing"))
                                        audio_to_speaker_queue.put(b"END_TURN")

                                        try:
                                            for fc in response.tool_call.function_calls:
                                                name = fc.name
                                                args = fc.args

                                                if name == "capture_screen":
                                                    ui_events_queue.put(("log", "📸 Захват экрана (1280x720)..."))
                                                    import mss
                                                    from PIL import Image
                                                    try:
                                                        with mss.mss() as sct:
                                                            # Захватываем основной монитор (X11)
                                                            sct_img = sct.grab(sct.monitors[1])
                                                            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                                                            
                                                            # Ресайз строго в 1280x720 для экономии токенов и четкости текста
                                                            img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
                                                            
                                                        # 1. Отправляем подтверждение вызова функции
                                                        await session.send_tool_response(
                                                            function_responses=[
                                                                FunctionResponse(
                                                                    name=name, id=fc.id, 
                                                                    response={"result": "Скриншот 1280x720 сделан. Я вижу твой экран. Анализирую..."}
                                                                )
                                                            ]
                                                        )
                                                        # 2. Инжектим саму картинку прямо в Live-сессию
                                                        await session.send(input=img)
                                                        ui_events_queue.put(("log", "✅ Снимок 720p передан в контекст"))
                                                    except Exception as e:
                                                        ui_events_queue.put(("log", f"❌ Ошибка зрения: {e}"))
                                                        await session.send_tool_response(
                                                            function_responses=[FunctionResponse(name=name, id=fc.id, response={"result": f"Ошибка: {e}"})]
                                                        )
                                                    continue

                                                if name == "standby_mode":
                                                    audio_cmd_queue.put("STANDBY")
                                                    await session.send_tool_response(
                                                        function_responses=[
                                                            FunctionResponse(
                                                                name=name,
                                                                id=fc.id,
                                                                response={"result": "Standby mode activated."},
                                                            )
                                                        ]
                                                    )
                                                    back_to_standby = True
                                                    return
                                                
                                                audio_cmd_queue.put("ACTIVE")
                                                ui_events_queue.put(("log", f"🟢 TOOL: {name}"))

                                                if name in TOOLS_MAPPING:
                                                    # Check if we should block based on context
                                                    blocked_result = None
                                                    if plugin_flow_owned and name in {
                                                        "search_github_plugins", "internet_research", 
                                                        "install_pending_plugin", "install_plugin", 
                                                        "confirm_plugin_pull", "fetch_plugin_code"
                                                    }:
                                                        blocked_result = "LOCAL_PLUGIN_FLOW_ACTIVE"
                                                    elif (plugin_install_intent_active and name == "internet_research" 
                                                          and not is_explicit_web_search_request(recent_user_request_text())):
                                                        blocked_result = "BLOCKED: Focused on plugin installation. Browse ignored."
                                                        ui_events_queue.put(("log", "🛑 Blocked browsing during plugin flow"))

                                                    if blocked_result:
                                                        await session.send_tool_response(
                                                            function_responses=[
                                                                FunctionResponse(
                                                                    name=name,
                                                                    id=fc.id,
                                                                    response={"result": blocked_result},
                                                                )
                                                            ]
                                                        )
                                                        continue

                                                    # Execute actual tool
                                                    result = await execute_tool(TOOLS_MAPPING[name], args, name)

                                                    # Logic for special tools
                                                    if name == "search_github_plugins" and isinstance(result, str) and "NO PLUGINS FOUND" not in result:
                                                        plugin_flow_owned = True
                                                        plugin_install_intent_active = True
                                                    
                                                    if name == "confirm_plugin_pull" and isinstance(result, str):
                                                        if "APPROVED" in result:
                                                            pending_installer = TOOLS_MAPPING.get("install_pending_plugin")
                                                            if callable(pending_installer):
                                                                ui_events_queue.put(("log", "🧩 Installing plugin after UI approval..."))
                                                                install_res = await execute_tool(pending_installer, {"user_approved": True}, "install_pending_plugin")
                                                                result = f"Installation successful. {install_res}"
                                                                if isinstance(install_res, str) and "SUCCESS" in install_res:
                                                                    restart_session = True
                                                        elif "DECLINED" in result:
                                                            result = "User declined installation via UI."

                                                    # Send response back to Google
                                                    await session.send_tool_response(
                                                        function_responses=[
                                                            FunctionResponse(
                                                                name=name,
                                                                id=fc.id,
                                                                response={"result": str(result)},
                                                            )
                                                        ]
                                                    )
                                                    
                                                    if restart_session:
                                                        ui_events_queue.put(("log", "♻️ Restarting session for new plugins..."))
                                                        return
                                                else:
                                                    ui_events_queue.put(("log", f"⚠️ AI hallucinated tool: {name}"))
                                                    await session.send_tool_response(
                                                        function_responses=[
                                                            FunctionResponse(
                                                                name=name,
                                                                id=fc.id,
                                                                response={"result": f"Error: Tool '{name}' not found."},
                                                            )
                                                        ]
                                                    )
                                        except Exception as tool_err:
                                            ui_events_queue.put(("log", f"❌ TOOL ERROR: {tool_err}"))
                                        finally:
                                            tool_active = False
                                            ui_events_queue.put(("status", "idle"))

                                    elif (
                                        response.server_content
                                        and response.server_content.model_turn
                                    ):
                                        text_parts = []
                                        for (
                                            part
                                        ) in response.server_content.model_turn.parts:
                                            if part.inline_data:
                                                audio_to_speaker_queue.put(
                                                    part.inline_data.data
                                                )
                                            elif getattr(part, "text", None):
                                                text_parts.append(part.text.strip())

                                        if response.server_content.turn_complete:
                                            audio_to_speaker_queue.put(b"END_TURN")

                                        if text_parts:
                                            spoken_text = " ".join(
                                                chunk for chunk in text_parts if chunk
                                            ).strip()

                                            # Reset blocking flags if this is a real response from the AI
                                            is_meta = is_meta_model_text(spoken_text)
                                            if spoken_text and not is_meta:
                                                plugin_install_intent_active = False
                                                plugin_flow_owned = False

                                                # Игнорируем текстовые мысли, пускай выводит только звук
                                                pass
                                            elif (
                                                plugin_flow_owned
                                                and plugin_install_intent_active
                                            ):
                                                # Still in plugin flow and no real text generated yet
                                                continue
                            except Exception as e:
                                ui_events_queue.put(
                                    ("log", f"❌ CLOUD RECEIVE ERROR: {e}")
                                )

                        t_send = asyncio.create_task(send_audio())
                        t_recv = asyncio.create_task(receive_cloud())
                        t_stop = asyncio.create_task(check_for_stop())

                        while True:
                            done, pending = await asyncio.wait(
                                [t_send, t_recv, t_stop],
                                return_when=asyncio.FIRST_COMPLETED,
                            )
                            
                            if t_stop in done:
                                res = t_stop.result()
                                if res is True or (isinstance(res, dict) and res.get("cmd") == "STOP"):
                                    stop_requested = True
                                    for t in pending:
                                        t.cancel()
                                    break
                                # --- ДОБАВЬ ЭТОТ БЛОК ---
                                elif isinstance(res, dict) and res.get("cmd") == "STANDBY":
                                    back_to_standby = True
                                    for t in pending:
                                        t.cancel()
                                    break
                                # ------------------------
                                elif isinstance(res, dict) and res.get("cmd") == "INJECT_TEXT":
                                    txt = res.get("text", "")
                                    if txt:
                                        await send_text_turn(session, txt)
                                        ui_events_queue.put(("log", "⚙️ Внедрено системное текстовое сообщение в сессию ИИ"))
                                    t_stop = asyncio.create_task(check_for_stop())
                                    continue
                            
                            for t in pending:
                                t.cancel()
                            break

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    ui_events_queue.put(("log", f"CONNECTION ERROR: {e}"))
                    await asyncio.sleep(1)

                # --- ДОБАВЛЯЕМ ВЫЧИСТКУ ОЧЕРЕДИ ЗДЕСЬ ---
                try:
                    while True:
                        cmd = ai_cmd_queue.get_nowait()
                        if cmd == "STOP" or (isinstance(cmd, dict) and cmd.get("cmd") == "STOP"):
                            stop_requested = True
                except queue.Empty:
                    pass
                # ----------------------------------------

                if stop_requested:
                    break

                # --- ВЫПРЫГИВАЕМ НА ВЕЙК-ВОРД ---
                if back_to_standby:
                    ui_events_queue.put(("log", "⚪ Возврат в режим ожидания (WWD)..."))
                    break

                if restart_session:
                    ui_events_queue.put(("log", "⚪ Synchronizing streams..."))
                    await asyncio.sleep(0.5)
                    continue

                ui_events_queue.put(("log", "🔄 Restoring stream..."))
                await asyncio.sleep(0.2)

            # FIX 2: If STOP is pressed during dialogue - hard exit, don't fall asleep!
            if stop_requested:
                break

        ui_events_queue.put(("finished", None))

    asyncio.run(run_ai())


# ========================================
# DEBUG LOG WINDOW
# ========================================
class LogWindow(QMainWindow):
    """Separate window for debug logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🐛 Mycrofet Debug Logs")
        self.resize(700, 400)
        self.setStyleSheet("background-color: #0a0a0a;")

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff88;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: none;
                padding: 15px;
            }
        """)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #1a1a1a; padding: 8px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        clear_btn.clicked.connect(self.log_text.clear)

        toolbar_layout.addWidget(QLabel("📋 Debug Console"))
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(clear_btn)

        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(self.log_text)

    def append_log(self, msg):
        """Add log message."""
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

from PyQt6.QtGui import QPolygonF, QPainterPath

def start_gui():
    from PyQt6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, QUrl, pyqtSignal
    from PyQt6.QtGui import QBrush, QColor, QDesktopServices, QFont, QIcon, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
    from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget, QSystemTrayIcon, QTextEdit, QVBoxLayout, QWidget
    import qdarktheme

    class TechVisualizer(QWidget):
        PI2 = math.pi * 2

        STATUS_TEXTS = {
            "listening": "◉ LISTENING",
            "processing": "◎ PROCESSING",
            "speaking": "◈ SPEAKING",
        }

        # Color palettes for different states
        PALETTE_IDLE = [
            (100, 100, 100), (120, 120, 120), (90, 90, 90),
            (110, 110, 110), (80, 80, 80), (100, 100, 100),
        ]
        PALETTE_ACTIVE = [
            (0, 200, 255), (50, 150, 255), (150, 50, 255),
            (255, 0, 170), (255, 50, 200), (200, 80, 255),
        ]
        PALETTE_LISTENING = [
            (30, 100, 255), (50, 140, 255), (80, 170, 255),
            (40, 120, 255), (60, 160, 255), (100, 180, 255),
        ]
        PALETTE_SPEAKING = [
            (0, 220, 200), (50, 180, 255), (120, 80, 255),
            (255, 50, 200), (200, 100, 255), (80, 255, 150),
        ]
        # Distinct standby/WWD palette — muted teal/cyan, clearly different from gray idle
        PALETTE_STANDBY = [
            (30, 80, 90), (40, 100, 110), (25, 70, 85),
            (35, 90, 100), (20, 65, 80), (45, 95, 105),
        ]

        def __init__(self):
            super().__init__()
            self.setMinimumSize(220, 220)
            self.amp_smooth = 0.0
            self.amp_fast = 0.0
            self.target_amp = 0.0
            self.mode = "idle"
            self.visual_state = "standby"
            self.dev_mode = False
            self.amplitude_source = "user"  # "user" or "ai"

            # Animation phases
            self.phase_outer = 0.0
            self.phase_middle = 0.0
            self.phase_inner = 0.0
            self.wave_phase = 0.0

            # Smooth color transition
            self.current_colors = [(100, 100, 100)] * 6
            self.target_colors = [(100, 100, 100)] * 6

            # Random deformation offsets for organic partial bulging (applied mostly to the living outer ring)
            self._deform_count = 6
            self._deform_current = [0.0] * self._deform_count
            self._deform_target = [0.0] * self._deform_count
            self._deform_refresh_counter = 0

            # Transition pulse on mode change
            self._transition_pulse = 0.0

            self.timer = QTimer()
            self.timer.timeout.connect(self.animate)
            self.timer.start(50)  # 20fps — sufficient for organic animation, limits CPU

            self.frame_count = 0

            # Precomputed LUTs for ring math
            import numpy as np
            self.num_points_list = [70, 100, 140]
            self.luts = []
            for n in self.num_points_list:
                angles = np.linspace(0, self.PI2, n + 1, dtype=np.float32)
                self.luts.append({
                    'cos': np.cos(angles),
                    'sin': np.sin(angles)
                })

        def set_amplitude_source(self, source):
            self.amplitude_source = source

        def update_level(self, level):
            if self.amplitude_source == "user":
                self.target_amp = min(level * 0.8, 0.4)
            else:
                self.target_amp = min(level * 1.8, 1.2)

        def set_mode(self, mode):
            old_mode = self.mode
            self.mode = mode
            if mode == "listening":
                self.target_colors = list(self.PALETTE_ACTIVE)
            elif mode == "processing":
                self.target_colors = list(self.PALETTE_ACTIVE)
            elif mode == "speaking":
                self.target_colors = list(self.PALETTE_SPEAKING)
            else:
                if self.visual_state == "active":
                    self.target_colors = list(self.PALETTE_LISTENING)
                elif self.visual_state == "standby":
                    self.target_colors = list(self.PALETTE_STANDBY)
                else:
                    self.target_colors = list(self.PALETTE_IDLE)
            if old_mode != mode:
                self._transition_pulse = 0.5

        def set_visual_state(self, state):
            old_state = self.visual_state
            self.visual_state = state
            if state == "active":
                self.target_colors = list(self.PALETTE_LISTENING)
            elif state == "standby":
                self.target_colors = list(self.PALETTE_STANDBY)
            elif state == "idle":
                self.target_colors = list(self.PALETTE_IDLE)
            if old_state != state:
                self._transition_pulse = 0.6

        def set_dev_mode(self, enabled):
            self.dev_mode = enabled

        def _get_deform_at(self, angle):
            pos = (angle / self.PI2) * self._deform_count
            idx = int(pos) % self._deform_count
            frac = pos - int(pos)
            # Smoothstep interpolation to eliminate sharp corners
            smooth_frac = frac * frac * (3 - 2 * frac)
            next_idx = (idx + 1) % self._deform_count
            return self._deform_current[idx] * (1.0 - smooth_frac) + self._deform_current[next_idx] * smooth_frac

        def _draw_polygon_ring(self, cx, cy, base_radius, wave_amp, wave_freq,
                               num_strands, num_points, phase, colors, alpha_base, pen_width, p, amp=0.0, ring_index=0):
            """Highly optimized ring drawing using QPolygonF and numpy LUTs."""
            golden = 1.6180339887
            wave_phase = self.wave_phase
            inv_n = self.PI2 / num_points

            lut = self.luts[ring_index]

            for strand in range(num_strands):
                strand_phase = strand * golden + phase
                col_idx = strand % len(colors)
                cr, cg, cb = colors[col_idx]
                flicker = 0.8 + 0.2 * math.sin(wave_phase * 2 + strand * 1.7)
                alpha = max(20, min(255, int(alpha_base * flicker)))

                pen = QPen(QColor(cr, cg, cb, alpha), pen_width)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                p.setBrush(Qt.GlobalColor.transparent)

                h1_off = strand * 0.7
                h2_off = strand * 1.3

                import numpy as np
                t = np.arange(num_points + 1, dtype=np.float32) * inv_n

                osc = (wave_amp * np.sin(wave_freq * t + strand_phase)
                       + wave_amp * 0.5 * np.sin((wave_freq * 1.7) * t + strand_phase + h1_off + wave_phase)
                       + wave_amp * 0.3 * np.sin((wave_freq * 2.9) * t + strand_phase + h2_off - wave_phase * 0.7))

                ratio = (t / self.PI2) * self._deform_count
                idx = ratio.astype(int) % self._deform_count
                next_idx = (idx + 1) % self._deform_count
                frac = ratio - ratio.astype(int)
                smooth_frac = frac * frac * (3 - 2 * frac)
                deform_arr = np.array(self._deform_current, dtype=np.float32)
                deform = (deform_arr[idx] * (np.float32(1.0) - smooth_frac) + deform_arr[next_idx] * smooth_frac) * amp * np.float32(8.0)

                amp_push = amp * 3.0 * (0.5 + 0.5 * np.sin(3 * t + wave_phase * 1.3 + strand * 0.9))

                r = base_radius + osc + deform + amp_push

                x = cx + r * lut['cos']
                y = cy + r * lut['sin']

                # Direct generation via comprehension is heavily optimized in Python C-API
                polygon_points = [QPointF(xx, yy) for xx, yy in zip(x, y)]

                path = QPainterPath()
                path.addPolygon(QPolygonF(polygon_points))
                p.drawPath(path)

        def animate(self):
            self.frame_count += 1

            if self.visual_state == "standby" or self.mode == "idle":
                if self.timer.interval() != 100:
                    self.timer.setInterval(100) # 10 FPS
            else:
                if self.timer.interval() != 33:
                    self.timer.setInterval(33)  # 30 FPS

            # Two audio trackers: slow/smooth and fast/reactive
            # Lower lerp rates make the animation beautifully fluid and slow during speech
            self.amp_smooth += (self.target_amp - self.amp_smooth) * 0.06
            self.amp_fast += (self.target_amp - self.amp_fast) * 0.15
            self.target_amp = max(0, self.target_amp - 0.03)

            if self._transition_pulse > 0.01:
                self.amp_smooth = max(self.amp_smooth, self._transition_pulse)
                self.amp_fast = max(self.amp_fast, self._transition_pulse)
                self._transition_pulse *= 0.90
            else:
                self._transition_pulse = 0.0

            speed_mult = 1.0 + self.amp_smooth * 1.5
            self.phase_outer = (self.phase_outer + 0.008 * speed_mult) % self.PI2
            self.phase_middle = (self.phase_middle - 0.012 * speed_mult) % self.PI2
            self.phase_inner = (self.phase_inner + 0.020 * speed_mult) % self.PI2
            self.wave_phase = (self.wave_phase + 0.05 * speed_mult) % self.PI2

            for i in range(len(self.current_colors)):
                cr, cg, cb = self.current_colors[i]
                tr, tg, tb = self.target_colors[i]
                self.current_colors[i] = (
                    cr + int((tr - cr) * 0.08),
                    cg + int((tg - cg) * 0.08),
                    cb + int((tb - cb) * 0.08),
                )

            self._deform_refresh_counter += 1
            if self._deform_refresh_counter >= 40:
                self._deform_refresh_counter = 0
                active_zones = random.sample(range(self._deform_count), random.randint(1, 3))
                for k in range(self._deform_count):
                    if k in active_zones:
                        self._deform_target[k] = random.uniform(0.5, 1.0)
                    else:
                        self._deform_target[k] = random.uniform(-0.1, 0.15)
            for k in range(self._deform_count):
                self._deform_current[k] += (self._deform_target[k] - self._deform_current[k]) * 0.06

            self.update()

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            cx, cy = w * 0.5, h * 0.5
            scale = min(w, h) / 400.0  # Overall scale

            # Dark navy blue background
            p.fillRect(0, 0, w, h, QColor(10, 15, 58))

            colors = self.current_colors

            # Center glow (matches inner ring color)
            avg_r = sum(c[0] for c in colors) // len(colors)
            avg_g = sum(c[1] for c in colors) // len(colors)
            avg_b = sum(c[2] for c in colors) // len(colors)
            glow_r = 70 * scale
            grad = QRadialGradient(cx, cy, glow_r)
            grad.setColorAt(0, QColor(avg_r, avg_g, avg_b, 35))
            grad.setColorAt(0.5, QColor(avg_r, avg_g, avg_b, 15))
            grad.setColorAt(1, Qt.GlobalColor.transparent)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

            # ----------------------------------------------------
            # RING 1: INNER "THINKING" RING
            # Changes color vibrantly, very little spatial animation
            # ----------------------------------------------------
            inner_r = 15 * scale
            inner_wave = 1.0 * scale
            self._draw_polygon_ring(
                cx, cy, inner_r, inner_wave, 2,
                num_strands=2, num_points=70, phase=self.phase_inner,
                colors=[colors[1], colors[3], colors[5], colors[0]],
                alpha_base=180, pen_width=1.5, p=p, amp=0.0, ring_index=0
            )

            # ----------------------------------------------------
            # RING 2: MIDDLE "ACTIVE" RING
            # Constant moderate wavy movement
            # ----------------------------------------------------
            mid_r = 40 * scale
            mid_wave = (3 + self.amp_smooth * 2) * scale
            self._draw_polygon_ring(
                cx, cy, mid_r, mid_wave, 4,
                num_strands=3, num_points=100, phase=self.phase_middle,
                colors=[colors[2], colors[4], colors[1]],
                alpha_base=130, pen_width=1.2, p=p, amp=self.amp_smooth * scale * 2.0, ring_index=1
            )

            # ----------------------------------------------------
            # RING 3: OUTER "LIVING" RING
            # Fast synchronization with speech, wilder deformation
            # ----------------------------------------------------
            outer_r = 75 * scale
            # Use amp_fast for immediate response to syllables
            outer_wave = (6 + self.amp_fast * 6) * scale
            self._draw_polygon_ring(
                cx, cy, outer_r, outer_wave, 6,
                num_strands=4, num_points=140, phase=self.phase_outer,
                colors=[colors[0], colors[3], colors[5], colors[2]],
                alpha_base=100, pen_width=1.2, p=p, amp=self.amp_fast * scale * 3.5, ring_index=2
            )

            # Outer neon glow boundary
            glow_out = QRadialGradient(cx, cy, (outer_r + outer_wave * 2.0 + 10) * 1.05)
            glow_out.setColorAt(0.70, Qt.GlobalColor.transparent)
            glow_out.setColorAt(0.85, QColor(avg_r, avg_g, avg_b, 25))
            glow_out.setColorAt(1.0, Qt.GlobalColor.transparent)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow_out))
            outer_glow_r = (outer_r + outer_wave * 2.0 + 15) * 1.05
            p.drawEllipse(QPointF(cx, cy), outer_glow_r, outer_glow_r)


    class SettingsDialog(QDialog):
        def __init__(self, parent):
            super().__init__(parent)
            self.parent_win = parent
            self.resize(450, 400)
            self.setWindowTitle("Settings")

            # Store references for dynamic translation
            self.translatable_labels = []

            # Adaptive styles based on current theme
            if parent.current_theme == "light":
                self.setStyleSheet("""
                    QDialog { background-color: #f0f4f8; color: #1a1a1a; }
                    QPushButton.tab_btn { background: transparent; color: #666; border: none; border-radius: 8px; padding: 12px; font-size: 20px; }
                    QPushButton.tab_btn:hover { background: #e0e4e8; color: #333; }
                    QPushButton.tab_btn[selected="true"] { background: #3498db; color: #fff; }
                    QLabel { color: #555; font-size: 12px; }
                    QLabel#section_title { color: #1a1a1a; font-size: 14px; font-weight: bold; margin-bottom: 10px; }
                    QComboBox { background: #ffffff; border: 1px solid #cbd5e1; color: #1a1a1a; padding: 8px 12px; border-radius: 6px; min-height: 20px; }
                    QComboBox::drop-down { border: none; width: 30px; }
                    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #64748b; }
                    QComboBox QAbstractItemView { background: #ffffff; color: #1a1a1a; selection-background-color: #3498db; selection-color: white; border: 1px solid #cbd5e1; }
                    QLineEdit { background: #ffffff; border: 1px solid #cbd5e1; color: #0066cc; padding: 8px 12px; border-radius: 6px; }
                    QCheckBox { color: #555; spacing: 8px; }
                    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #94a3b8; background: #ffffff; }
                    QCheckBox::indicator:checked { background: #3498db; border-color: #3498db; }
                    QPushButton#save_btn { background: #3498db; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 13px; }
                    QPushButton#save_btn:hover { background: #2980b9; }
                    QPushButton#support_btn { background: transparent; color: #e74c3c; border: 2px solid #e74c3c; padding: 10px 20px; font-weight: bold; border-radius: 8px; }
                    QPushButton#support_btn:hover { background: #e74c3c; color: white; }
                """)
            elif parent.current_theme == "gray":
                self.setStyleSheet("""
                    QDialog { background-color: #4a4a4a; color: #e0e0e0; }
                    QPushButton.tab_btn { background: transparent; color: #999; border: none; border-radius: 8px; padding: 12px; font-size: 20px; }
                    QPushButton.tab_btn:hover { background: #555; color: #ccc; }
                    QPushButton.tab_btn[selected="true"] { background: #3498db; color: #fff; }
                    QLabel { color: #bbb; font-size: 12px; }
                    QLabel#section_title { color: #fff; font-size: 14px; font-weight: bold; margin-bottom: 10px; }
                    QComboBox { background: #3a3a3a; border: 1px solid #666; color: white; padding: 8px 12px; border-radius: 6px; min-height: 20px; }
                    QComboBox::drop-down { border: none; width: 30px; }
                    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #aaa; }
                    QComboBox QAbstractItemView { background: #3a3a3a; color: white; selection-background-color: #3498db; selection-color: white; border: 1px solid #666; }
                    QLineEdit { background: #3a3a3a; border: 1px solid #666; color: #00ffcc; padding: 8px 12px; border-radius: 6px; }
                    QCheckBox { color: #bbb; spacing: 8px; }
                    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #777; background: #3a3a3a; }
                    QCheckBox::indicator:checked { background: #3498db; border-color: #3498db; }
                    QPushButton#save_btn { background: #3498db; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 13px; }
                    QPushButton#save_btn:hover { background: #2980b9; }
                    QPushButton#support_btn { background: transparent; color: #e74c3c; border: 2px solid #e74c3c; padding: 10px 20px; font-weight: bold; border-radius: 8px; }
                    QPushButton#support_btn:hover { background: #e74c3c; color: white; }
                """)
            else:
                self.setStyleSheet("""
                    QDialog { background-color: #1a1a1a; color: #e0e0e0; }
                    QPushButton.tab_btn { background: transparent; color: #666; border: none; border-radius: 8px; padding: 12px; font-size: 20px; }
                    QPushButton.tab_btn:hover { background: #333; color: #aaa; }
                    QPushButton.tab_btn[selected="true"] { background: #3498db; color: #fff; }
                    QLabel { color: #aaa; font-size: 12px; }
                    QLabel#section_title { color: #fff; font-size: 14px; font-weight: bold; margin-bottom: 10px; }
                    QComboBox { background: #2a2a2a; border: 1px solid #444; color: white; padding: 8px 12px; border-radius: 6px; min-height: 20px; }
                    QComboBox::drop-down { border: none; width: 30px; }
                    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #888; }
                    QComboBox QAbstractItemView { background: #2a2a2a; color: white; selection-background-color: #3498db; selection-color: white; border: 1px solid #444; }
                    QLineEdit { background: #2a2a2a; border: 1px solid #444; color: #00ffcc; padding: 8px 12px; border-radius: 6px; }
                    QCheckBox { color: #aaa; spacing: 8px; }
                    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #555; background: #2a2a2a; }
                    QCheckBox::indicator:checked { background: #3498db; border-color: #3498db; }
                    QPushButton#save_btn { background: #3498db; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; font-size: 13px; }
                    QPushButton#save_btn:hover { background: #2980b9; }
                    QPushButton#support_btn { background: transparent; color: #e74c3c; border: 2px solid #e74c3c; padding: 10px 20px; font-weight: bold; border-radius: 8px; }
                    QPushButton#support_btn:hover { background: #e74c3c; color: white; }
                """)

            main_layout = QHBoxLayout(self)
            main_layout.setSpacing(16)
            main_layout.setContentsMargins(16, 16, 16, 16)

            sidebar = QVBoxLayout()
            sidebar.setSpacing(4)

            tabs = [
                ("⚛", "tab_ai"),
                ("◐", "tab_appearance"),
                ("⚙", "tab_advanced"),
                ("ℹ", "tab_about"),
            ]
            self.tab_buttons = []

            for i, (icon, key) in enumerate(tabs):
                btn = QPushButton(icon)
                btn.setFixedSize(48, 48)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setProperty("selected", "true" if i == 0 else "false")
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #666; border: none; border-radius: 8px; font-size: 22px; }
                    QPushButton:hover { background: #333; color: #aaa; }
                    QPushButton[selected="true"] { background: #3498db; color: #fff; }
                """)
                btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
                sidebar.addWidget(btn)
                self.tab_buttons.append(btn)

            sidebar.addStretch()
            main_layout.addLayout(sidebar)

            self.stack = QStackedWidget()
            main_layout.addWidget(self.stack, 1)

            self.create_ai_page()
            self.create_appearance_page()
            self.create_advanced_page()
            self.create_about_page()

            self.update_ui_language(self.parent_win.current_lang)

        def _create_label(self, key, is_title=False):
            lbl = QLabel()
            if is_title:
                lbl.setObjectName("section_title")
            self.translatable_labels.append((lbl, key))
            return lbl

        def _create_button(self, key, obj_name=None):
            btn = QPushButton()
            if obj_name:
                btn.setObjectName(obj_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.translatable_labels.append((btn, key))
            return btn

        def create_ai_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(16)
            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(self._create_label("tab_ai", True))

            layout.addWidget(self._create_label("lbl_voice"))
            self.cb_voice = QComboBox()
            self.cb_voice.addItems(["Puck", "Charon", "Kore", "Fenrir", "Aoede"])
            self.cb_voice.setCurrentText(getattr(self.parent_win, "selected_voice", "Puck"))
            layout.addWidget(self.cb_voice)

            layout.addWidget(self._create_label("city_label"))
            self.input_city = QLineEdit()
            self.input_city.setText(self.parent_win.default_city)
            self.translatable_labels.append((self.input_city, "city_placeholder"))
            layout.addWidget(self.input_city)

            layout.addWidget(self._create_label("lbl_key"))
            self.input_key = QLineEdit()
            self.input_key.setText(CURRENT_API_KEY if CURRENT_API_KEY else "")
            self.input_key.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.input_key)

            self.chk_show = QCheckBox()
            self.translatable_labels.append((self.chk_show, "chk_show"))
            self.chk_show.stateChanged.connect(
                lambda s: self.input_key.setEchoMode(
                    QLineEdit.EchoMode.Normal if s == 2 else QLineEdit.EchoMode.Password
                )
            )
            layout.addWidget(self.chk_show)

            layout.addStretch()

            btn_save = self._create_button("btn_save", "save_btn")
            btn_save.clicked.connect(self.save_and_close)
            layout.addWidget(btn_save)

            self.stack.addWidget(page)

        def create_appearance_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(16)
            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(self._create_label("tab_appearance", True))

            layout.addWidget(self._create_label("lbl_lang"))
            self.cb_lang = QComboBox()
            self.cb_lang.addItems(list(TRANSLATIONS.keys()))
            self.cb_lang.setCurrentText(self.parent_win.current_lang)
            self.cb_lang.currentTextChanged.connect(self.update_ui_language)
            layout.addWidget(self.cb_lang)

            layout.addWidget(self._create_label("lbl_theme"))
            self.cb_theme = QComboBox()
            self.cb_theme.addItems(["Dark", "Light", "Gray"])

            # Select current theme correctly mapping backwards
            theme_rev = {"dark": "Dark", "light": "Light", "gray": "Gray"}
            self.cb_theme.setCurrentText(
                theme_rev.get(self.parent_win.current_theme, "Dark")
            )

            layout.addWidget(self.cb_theme)

            layout.addStretch()

            btn_save = self._create_button("btn_save", "save_btn")
            btn_save.clicked.connect(self.save_and_close)
            layout.addWidget(btn_save)

            self.stack.addWidget(page)

        def create_advanced_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(16)
            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(self._create_label("tab_advanced", True))

            self.chk_dev = QCheckBox()
            self.translatable_labels.append((self.chk_dev, "lbl_dev"))
            self.chk_dev.setChecked(self.parent_win.dev_mode)
            layout.addWidget(self.chk_dev)

            layout.addStretch()

            btn_save = self._create_button("btn_save", "save_btn")
            btn_save.clicked.connect(self.save_and_close)
            layout.addWidget(btn_save)

            self.stack.addWidget(page)

        def create_about_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(16)
            layout.setContentsMargins(0, 0, 0, 0)

            title = self._create_label("about_title", True)
            title.setStyleSheet("font-size: 20px;")
            layout.addWidget(title)

            desc = self._create_label("about_desc")
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #888; line-height: 1.6;")
            layout.addWidget(desc)

            plugin_limit = self._create_label("plugin_limit_note")
            plugin_limit.setWordWrap(True)
            plugin_limit.setStyleSheet("color: #666; font-size: 11px; line-height: 1.5;")
            layout.addWidget(plugin_limit)

            version = QLabel("Version 2.3.0")
            version.setStyleSheet("color: #555; margin-top: 10px;")
            layout.addWidget(version)

            layout.addStretch()

            btn_support = self._create_button("btn_support", "support_btn")
            btn_support.clicked.connect(
                lambda: QDesktopServices.openUrl(
                    QUrl("https://www.patreon.com/c/archpulse/membership")
                )
            )
            layout.addWidget(btn_support)

            self.stack.addWidget(page)

        def switch_tab(self, index):
            self.stack.setCurrentIndex(index)
            for i, btn in enumerate(self.tab_buttons):
                btn.setProperty("selected", "true" if i == index else "false")
                btn.setStyle(btn.style())

        def update_ui_language(self, lang):
            self.setWindowTitle(
                TRANSLATIONS.get(lang, TRANSLATIONS["EN"]).get("win_settings", "Settings")
            )
            t = TRANSLATIONS.get(lang, TRANSLATIONS["EN"])
            keys = ["tab_ai", "tab_appearance", "tab_advanced", "tab_about"]
            for i, btn in enumerate(self.tab_buttons):
                btn.setToolTip(t.get(keys[i], keys[i]))

            for widget, key in self.translatable_labels:
                if isinstance(widget, QLineEdit):
                    widget.setPlaceholderText(t.get(key, key))
                else:
                    widget.setText(t.get(key, key))

            # Also update theme combobox text display without changing items keys
            theme_names = [
                t.get("theme_dark", "Dark"),
                t.get("theme_light", "Light"),
                t.get("theme_gray", "Gray"),
            ]
            for i, name in enumerate(theme_names):
                self.cb_theme.setItemText(i, name)

        def save_and_close(self):
            global CURRENT_API_KEY
            self.parent_win.selected_voice = self.cb_voice.currentText()
            self.parent_win.current_lang = self.cb_lang.currentText()
            self.parent_win.dev_mode = self.chk_dev.isChecked()
            self.parent_win.default_city = self.input_city.text().strip()

            # Save theme mapping
            theme_idx = self.cb_theme.currentIndex()
            if theme_idx == 1:
                self.parent_win.current_theme = "light"
            elif theme_idx == 2:
                self.parent_win.current_theme = "gray"
            else:
                self.parent_win.current_theme = "dark"

            self.parent_win.viz.set_dev_mode(self.parent_win.dev_mode)

            new_key = self.input_key.text().strip()
            if new_key and new_key != CURRENT_API_KEY:
                try:
                    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
                    with open(ENV_FILE, "w", encoding="utf-8") as f:
                        f.write(f"GOOGLE_API_KEY={new_key}")
                    CURRENT_API_KEY = new_key
                    os.environ["GOOGLE_API_KEY"] = new_key
                except Exception as e:
                    print(f"Error saving .env: {e}")

            self.parent_win.save_settings()
            self.parent_win.apply_theme()
            self.parent_win.update_ui()
            self.close()


    class MemoryManager:
        """SQLite-based long-term memory for the AI assistant."""

        def __init__(self, db_path=MEMORY_DB):
            self.db_path = db_path
            self.lock = threading.Lock()
            self.conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self._init_db()

        def _init_db(self):
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

        def save_fact(self, category: str, key: str, value: str):
            with self.lock:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO facts (category, key, value) VALUES (?, ?, ?)
                    """,
                        (category, key, value),
                    )
                    self.conn.commit()
                except sqlite3.Error:
                    self.conn.rollback()
                    raise

        def get_fact(self, category: str, key: str) -> str:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT value FROM facts WHERE category = ? AND key = ?",
                    (category, key),
                )
                row = cursor.fetchone()
            return row[0] if row else None

        def get_all_facts(self) -> list:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute("SELECT category, key, value FROM facts ORDER BY category")
                return cursor.fetchall()

        def get_all_facts_with_id(self) -> list:
            """Returns all facts with their IDs for deletion."""
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT id, category, key, value FROM facts ORDER BY category, key"
                )
                return cursor.fetchall()

        def delete_fact(self, fact_id: int):
            """Deletes a fact by its ID."""
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
                self.conn.commit()

        def delete_facts_by_ids(self, ids: list):
            """Deletes multiple facts by their IDs."""
            with self.lock:
                cursor = self.conn.cursor()
                for fact_id in ids:
                    cursor.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
                self.conn.commit()

        def clear_all(self):
            """Clears all facts from memory."""
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM facts")
                self.conn.commit()

        def get_db_size_mb(self) -> float:
            """Returns the database file size in MB."""
            try:
                if os.path.exists(self.db_path):
                    return os.path.getsize(self.db_path) / (1024 * 1024)
                return 0.0
            except OSError:
                return 0.0

        def get_user_context(self) -> str:
            """Returns a formatted string of all known facts about the user."""
            facts = self.get_all_facts()
            if not facts:
                return ""
            lines = ["=== USER MEMORY ==="]
            for cat, key, val in facts:
                lines.append(f"[{cat}] {key}: {val}")
            return "\n".join(lines)

        def close(self):
            self.conn.close()


    class MemoryCleanupDialog(QDialog):
        """Dialog for managing memory when database grows too large."""

        def __init__(self, memory: MemoryManager, current_size_mb: float, parent=None):
            super().__init__(parent)
            self.memory = memory
            self.current_size = current_size_mb
            self.checkboxes = {}
            self.action = None  # 'cleaned', 'ignore', 'remind_later'
            self.remind_size = 500

            self.setWindowTitle("🧠 Memory Management")
            self.setFixedSize(550, 500)
            self.setStyleSheet("""
                QDialog {
                    background: #1a1a2e;
                    color: white;
                }
                QLabel { color: white; }
                QLabel#title { font-size: 20px; font-weight: bold; color: #ff6b6b; }
                QLabel#subtitle { font-size: 13px; color: #aaa; }
                QScrollArea { background: transparent; border: none; }
                QWidget#scroll_content { background: transparent; }
                QCheckBox {
                    color: white;
                    padding: 8px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 6px;
                    margin: 2px 0;
                }
                QCheckBox:hover { background: rgba(255,255,255,0.1); }
                QCheckBox::indicator { width: 18px; height: 18px; }
                QCheckBox::indicator:checked {
                    background: #ff6b6b;
                    border-radius: 4px;
                }
                QPushButton {
                    background: rgba(255,255,255,0.1);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.2); }
                QPushButton#delete_btn { background: #ff6b6b; color: black; font-weight: bold; }
                QPushButton#delete_btn:hover { background: #ff8585; }
                QSpinBox {
                    background: rgba(255,255,255,0.1);
                    color: white;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 6px;
                    padding: 6px;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setSpacing(15)
            layout.setContentsMargins(25, 25, 25, 25)

            # Title
            title = QLabel("⚠️ Memory Database is Large")
            title.setObjectName("title")
            layout.addWidget(title)

            subtitle = QLabel(
                f"Your memory file is {current_size_mb:.1f} MB. Select items to delete:"
            )
            subtitle.setObjectName("subtitle")
            layout.addWidget(subtitle)

            # Scrollable area with checkboxes
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMaximumHeight(250)

            scroll_content = QWidget()
            scroll_content.setObjectName("scroll_content")
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(4)

            facts = memory.get_all_facts_with_id()
            for fact_id, category, key, value in facts:
                display_text = (
                    f"[{category}] {key}: {value[:50]}{'...' if len(value) > 50 else ''}"
                )
                cb = QCheckBox(display_text)
                cb.fact_id = fact_id
                self.checkboxes[fact_id] = cb
                scroll_layout.addWidget(cb)

            if not facts:
                scroll_layout.addWidget(QLabel("No memories stored yet."))

            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)

            # Select all / Deselect all buttons
            select_layout = QHBoxLayout()
            btn_select_all = QPushButton("Select All")
            btn_select_all.clicked.connect(self.select_all)
            btn_deselect = QPushButton("Deselect All")
            btn_deselect.clicked.connect(self.deselect_all)
            select_layout.addWidget(btn_select_all)
            select_layout.addWidget(btn_deselect)
            select_layout.addStretch()
            layout.addLayout(select_layout)

            # Delete selected button
            btn_delete = QPushButton("🗑️ Delete Selected")
            btn_delete.setObjectName("delete_btn")
            btn_delete.clicked.connect(self.delete_selected)
            layout.addWidget(btn_delete)

            # Separator
            layout.addSpacing(10)

            # Remind later option
            remind_layout = QHBoxLayout()
            remind_layout.addWidget(QLabel("Or remind me when file reaches:"))
            self.spin_remind = QSpinBox()
            self.spin_remind.setRange(100, 5000)
            self.spin_remind.setValue(1000)
            self.spin_remind.setSuffix(" MB")
            remind_layout.addWidget(self.spin_remind)
            btn_remind = QPushButton("Set & Close")
            btn_remind.clicked.connect(self.remind_later)
            remind_layout.addWidget(btn_remind)
            layout.addLayout(remind_layout)

            # Never show again button
            btn_ignore = QPushButton("Don't show this again")
            btn_ignore.clicked.connect(self.ignore_forever)
            layout.addWidget(btn_ignore)

        def select_all(self):
            for cb in self.checkboxes.values():
                cb.setChecked(True)

        def deselect_all(self):
            for cb in self.checkboxes.values():
                cb.setChecked(False)

        def delete_selected(self):
            ids_to_delete = [
                fact_id for fact_id, cb in self.checkboxes.items() if cb.isChecked()
            ]
            if ids_to_delete:
                self.memory.delete_facts_by_ids(ids_to_delete)
                self.action = "cleaned"
                self.accept()
            else:
                QMessageBox.information(
                    self, "No Selection", "Please select at least one item to delete."
                )

        def remind_later(self):
            self.action = "remind_later"
            self.remind_size = self.spin_remind.value()
            self.accept()

        def ignore_forever(self):
            self.action = "ignore"
            self.accept()


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("AXINIX AI")

            # Набор флагов для честных "обоев"
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnBottomHint |
                Qt.WindowType.Desktop |
                Qt.WindowType.Tool
            )

            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.setAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeDesktop)

            # ВАЖНО: Указываем размер экрана вручную, НЕ используя FullScreen
            # Это позволит GNOME рисовать свои панели поверх твоего окна
            self.setGeometry(0, 0, 1920, 1080) 
            self.show()




            self.current_lang = "EN"
            self.selected_voice = "Charon"
            self.dev_mode = False
            self.default_city = ""
            self.current_theme = "dark"
            self.is_running = False
            self.log_window = None  # Separate debug window

            self.load_settings()
            self.setup_tray()

            self.setWindowIcon(QIcon("logo.png"))
            self.setMinimumSize(800, 600)



            # Fullscreen visualizer — no card, no buttons, just the viz
            central = QWidget()
            self.setCentralWidget(central)
            central.setStyleSheet("background-color: #0a0f3a;")
            main_layout = QVBoxLayout(central)
            main_layout.setSpacing(0)
            main_layout.setContentsMargins(0, 0, 0, 0)

            self.viz = TechVisualizer()
            self.viz.set_dev_mode(self.dev_mode)
            main_layout.addWidget(self.viz)

            # Hidden widgets for compatibility (console/status)
            self.console = QTextEdit()
            self.console.setReadOnly(True)
            self.console.setVisible(False)
            self.status_label = QLabel("")
            self.status_label.setVisible(False)
            self.status_indicator = QLabel("")
            self.status_indicator.setVisible(False)

            self.thread = None

            # System Events: Background CPU Monitoring
            self.high_cpu_count = 0
            self._proc_cache = {}
            self.cpu_monitor_timer = QTimer()
            self.cpu_monitor_timer.timeout.connect(self.check_cpu_usage)
            self.cpu_monitor_timer.start(3000)  # Every 3 seconds

            self.update_ui()
            self.check_api_key_on_startup()

            import gc
            gc.collect()

        def check_api_key_on_startup(self):
            t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["EN"])
            if not CURRENT_API_KEY:
                self.update_status_display(False, t.get("no_api_key", "No API Key"))
            else:
                self.update_status_display(False, t.get("status_offline", "System Offline"))

        def check_cpu_usage(self):
            try:
                import psutil
                # Non-blocking global CPU check
                global_cpu = psutil.cpu_percent(interval=None)

                max_proc = "Unknown"
                max_cpu = 0.0

                # Use cached process objects to get accurate non-blocking cpu_percent
                active_pids = set()
                for p in psutil.process_iter(['name']):
                    pid = p.pid
                    active_pids.add(pid)
                    try:
                        if pid not in self._proc_cache:
                            self._proc_cache[pid] = p
                        p_cpu = self._proc_cache[pid].cpu_percent(interval=None)
                        if p_cpu > max_cpu and p.info['name'] not in ("Idle", "System Idle Process"):
                            max_cpu = p_cpu
                            max_proc = p.info['name']
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Clean up dead processes
                self._proc_cache = {pid: proc for pid, proc in self._proc_cache.items() if pid in active_pids}

                # Триггеримся по ОБЩЕЙ нагрузке на систему, а не по одному потоку.
                # Ставим порог 80%, чтобы просадки stress-ng не ломали тест.
                if global_cpu >= 80.0:
                    # Ограничитель. Тормозим счетчик на 15, чтобы он не улетел в бесконечность
                    if self.high_cpu_count < 15:  
                        self.high_cpu_count += 1

                        if self.high_cpu_count == 7:  # 21 секунда (тихое текстовое предупреждение)
                            msg_title = "Высокая нагрузка CPU"
                            msg_body = f"Система: {global_cpu:.1f}%. Лидер: {max_proc} ({max_cpu:.1f}%)"
                            self.tray_icon.showMessage(msg_title, msg_body, QSystemTrayIcon.MessageIcon.Warning, 5000)
                            import subprocess
                            try: subprocess.Popen(['notify-send', '-u', 'critical', msg_title, msg_body])
                            except: pass
                            self.log_msg(f"⚠️ CPU Warning: {global_cpu}% total")

                        elif self.high_cpu_count == 14:  # 42 секунды (врываемся голосом)
                            msg_title = "Критическая нагрузка CPU"
                            msg_body = f"Алярм! Система забита. Предупреждаю голосом."
                            self.tray_icon.showMessage(msg_title, msg_body, QSystemTrayIcon.MessageIcon.Critical, 5000)
                            import subprocess
                            try: subprocess.Popen(['notify-send', '-u', 'critical', msg_title, msg_body])
                            except: pass

                            if hasattr(self, "is_running") and self.is_running and hasattr(self, "ai_cmd_queue"):
                                # Просим ИИ отреагировать
                                prompt = f"СИСТЕМНОЕ СООБЩЕНИЕ: Внимание, общая нагрузка на процессор {global_cpu:.1f}%. Главный виновник — процесс {max_proc}. Коротко и по-свойски (начни с 'Сэр') скажи пользователю, что процессор сейчас расплавится."
                                self.ai_cmd_queue.put({"cmd": "INJECT_TEXT", "text": prompt})

                            # ВАЖНО: Мы больше не сбрасываем счетчик в 0! 
                            # Он зависнет на 15 и программа будет молчать, пока проц реально не остынет.
                else:
                    # ПЛАВНЫЙ СБРОС: если нагрузка упала, счетчик потихоньку "остывает" 
                    self.high_cpu_count = max(0, self.high_cpu_count - 1)

            except ImportError:
                self.log_msg("⚠️ psutil is not installed. CPU monitoring disabled.")
                self.cpu_monitor_timer.stop()
            except Exception as e:
                self.log_msg(f"CPU Monitor Error: {e}")

        def load_settings(self):
            if os.path.exists(SETTINGS_FILE):
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.current_lang = data.get("lang", "EN")
                        self.selected_voice = data.get("voice", "Puck")
                        self.dev_mode = data.get("dev_mode", False)
                        self.default_city = data.get("city", "")
                        self.current_theme = data.get("theme", "dark")
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Settings load error: {e}")

        def save_settings(self):
            data = {}
            import os

            if os.path.exists(SETTINGS_FILE):
                try:
                    import json

                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Settings read error: {e}")

            data["lang"] = self.current_lang
            data["voice"] = self.selected_voice
            data["dev_mode"] = self.dev_mode
            data["city"] = self.default_city
            data["theme"] = self.current_theme
            data["first_run_completed"] = True
            try:
                import json

                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except OSError as e:
                print(f"Settings write error: {e}")

        def apply_theme(self):
            # Fullscreen visualizer always uses dark navy blue — no theme switching needed
            pass

        def update_button_style(self):
            # Update tray menu text to reflect current state
            if hasattr(self, 'tray_init_action'):
                if not CURRENT_API_KEY:
                    self.tray_init_action.setText("⚠ No API Key")
                    self.tray_init_action.setEnabled(False)
                elif self.is_running:
                    self.tray_init_action.setText("⏹ STOP")
                    self.tray_init_action.setEnabled(True)
                else:
                    self.tray_init_action.setText("▶ INIT")
                    self.tray_init_action.setEnabled(True)

        def update_status_display(self, online=False, text="System Offline"):
            if online:
                self.status_indicator.setStyleSheet("color: #2ecc71; font-size: 18px;")
                self.status_label.setStyleSheet(
                    "color: #2ecc71; font-size: 14px; font-weight: 500;"
                )
            else:
                self.status_indicator.setStyleSheet("color: #555; font-size: 18px;")
                self.status_label.setStyleSheet(
                    "color: #888; font-size: 14px; font-weight: 500;"
                )
            self.status_label.setText(text)

        def poll_ui_events(self):
            try:
                import queue

                while True:
                    try:
                        event, data = self.ui_events_queue.get_nowait()
                        if event == "amplitude":
                            self.viz.update_level(data)
                        elif event == "status":
                            self.on_status_change(data)
                        elif event == "amplitude_source":
                            self.viz.set_amplitude_source(data)
                        elif event == "log":
                            self.log_msg(data)
                        elif event == "mode":
                            self.viz.set_visual_state(data)
                        elif event == "finished":
                            self.on_thread_finished()
                        elif event == "ready":
                            self.update_button_style()
                            self.viz.set_visual_state("standby") # Было "active"
                            self.tray_icon.setToolTip("Axinix AI — ✅ Онлайн (WWD)")
                            self.tray_icon.showMessage("Axinix AI", "Система онлайн",
                                QSystemTrayIcon.MessageIcon.Information, 2000)
                        elif event == "plugin_install_prompt":
                            message = "Установить найденный плагин?"
                            if isinstance(data, dict):
                                message = data.get("message", message)
                            reply = QMessageBox.question(
                                self,
                                "Plugin Install",
                                message,
                                QMessageBox.StandardButton.Yes
                                | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes,
                            )
                            if hasattr(self, "ai_cmd_queue"):
                                self.ai_cmd_queue.put(
                                    {
                                        "cmd": "PLUGIN_INSTALL_DECISION",
                                        "approved": reply == QMessageBox.StandardButton.Yes,
                                    }
                                )
                    except queue.Empty:
                        break
            except Exception:
                pass

        def toggle(self):
            t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["EN"])
            if not CURRENT_API_KEY:
                self.tray_icon.showMessage("Axinix AI", "No API Key — set it in Settings",
                    QSystemTrayIcon.MessageIcon.Warning, 3000)
                return

            if self.is_running:
                self.log_msg("STOPPING...")
                if hasattr(self, "ai_cmd_queue"):
                    self.ai_cmd_queue.put("STOP")
                if hasattr(self, "audio_cmd_queue"):
                    self.audio_cmd_queue.put("STOP")
            else:
                self.log_msg("INITIALIZING MULTIPROCESSING...")
                import multiprocessing

                self.ui_events_queue = multiprocessing.Queue()
                self.audio_to_ai_queue = multiprocessing.Queue()
                self.audio_to_speaker_queue = multiprocessing.Queue()
                self.ai_cmd_queue = multiprocessing.Queue()
                self.audio_cmd_queue = multiprocessing.Queue()

                use_wwd = True

                self.audio_process = multiprocessing.Process(
                    target=audio_process_worker,
                    args=(
                        self.audio_to_ai_queue,
                        self.audio_to_speaker_queue,
                        self.ui_events_queue,
                        self.audio_cmd_queue,
                        use_wwd,
                    ),
                )
                self.ai_process = multiprocessing.Process(
                    target=ai_process_worker,
                    args=(
                        self.audio_to_ai_queue,
                        self.audio_to_speaker_queue,
                        self.ui_events_queue,
                        self.ai_cmd_queue,
                        self.audio_cmd_queue,
                        self.selected_voice,
                        self.default_city,
                        CURRENT_API_KEY,
                    ),
                )
                self.audio_process.start()
                self.ai_process.start()

                self.ui_timer = QTimer()
                self.ui_timer.timeout.connect(self.poll_ui_events)
                self.ui_timer.start(30)

                self.is_running = True
                self.update_button_style()
                self.tray_icon.setToolTip("Axinix AI — ⏳ Загрузка моделей...")
                self.tray_icon.showMessage("Axinix AI", "Загрузка моделей...",
                    QSystemTrayIcon.MessageIcon.Information, 2000)

        def on_thread_finished(self):
            if hasattr(self, "ui_timer"):
                self.ui_timer.stop()
            self.is_running = False
            self.update_button_style()
            self.viz.set_mode("idle")
            self.viz.set_visual_state("idle")
            self.log_msg("SYSTEM HALTED")
            self.tray_icon.setToolTip("Axinix AI — ⏹ Оффлайн")
            self.tray_icon.showMessage("Axinix AI", "Система остановлена",
                QSystemTrayIcon.MessageIcon.Information, 2000)

        def on_status_change(self, s):
            self.viz.set_mode(s)

            # Update tray tooltip with current status
            status_icons = {
                "listening": "🎤 Слушаю...",
                "processing": "⚙ Обработка...",
                "speaking": "🔊 Говорю...",
            }
            if s in status_icons:
                self.tray_icon.setToolTip(f"Axinix AI — {status_icons[s]}")
            elif self.is_running:
                self.tray_icon.setToolTip("Axinix AI — ✅ Онлайн")

        def log_msg(self, msg):
            """Log message to console or separate window."""
            if self.dev_mode and self.log_window:
                # Log to separate window
                self.log_window.append_log(msg)
            else:
                # Log to inline console
                self.console.append(msg)
                self.console.verticalScrollBar().setValue(
                    self.console.verticalScrollBar().maximum()
                )

        def setup_tray(self):
            """Setup system tray icon with all controls."""
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("logo.png"))
            self.tray_icon.setToolTip("Axinix AI — ⏹ Оффлайн")

            tray_menu = QMenu()

            # INIT / STOP
            self.tray_init_action = tray_menu.addAction("▶ INIT")
            self.tray_init_action.triggered.connect(self.toggle)

            tray_menu.addSeparator()

            # Settings
            settings_action = tray_menu.addAction("⚙ Настройки")
            settings_action.triggered.connect(self.open_settings)

            # Debug toggle
            self.tray_debug_action = tray_menu.addAction("💻 Отладка: Выкл")
            self.tray_debug_action.triggered.connect(self.toggle_debug)

            tray_menu.addSeparator()

            # WWD controls
            skip_wwd_action = tray_menu.addAction("⏩ Пропустить WWD")
            skip_wwd_action.triggered.connect(self.skip_wwd)

            enable_wwd_action = tray_menu.addAction("🎙 Перейти к WWD")
            enable_wwd_action.triggered.connect(self.enable_wwd)

            tray_menu.addSeparator()

            # Show / Hide
            show_action = tray_menu.addAction("🔲 Показать")
            show_action.triggered.connect(self.show)

            hide_action = tray_menu.addAction("🔳 Свернуть в трей")
            hide_action.triggered.connect(self.hide)

            tray_menu.addSeparator()

            # Quit
            quit_action = tray_menu.addAction("❌ Выход")
            quit_action.triggered.connect(self.quit_app)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()

        def toggle_debug(self):
            """Toggle debug mode from tray."""
            self.dev_mode = not self.dev_mode
            self.save_settings()
            self.update_ui()

        def skip_wwd(self):
            """Skip wake word detection and activate listening."""
            if self.is_running and hasattr(self, "audio_cmd_queue"):
                self.audio_cmd_queue.put("ACTIVE")
                self.tray_icon.showMessage(
                    "Axinix AI",
                    "WWD пропущен, микрофон активен",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

        def enable_wwd(self):
            """Enable wake word detection (standby mode)."""
            if self.is_running and hasattr(self, "audio_cmd_queue"):
                self.audio_cmd_queue.put("STANDBY")
            # --- ДОБАВЬ ЭТИ ДВЕ СТРОКИ ---
            if self.is_running and hasattr(self, "ai_cmd_queue"):
                self.ai_cmd_queue.put({"cmd": "STANDBY"})
                self.tray_icon.showMessage(
                    "Axinix AI",
                    "Режим ожидания wake word",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

        def tray_icon_activated(self, reason):
            """Handle tray icon activation."""
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.show()
                self.activateWindow()

        def closeEvent(self, event):
            """Minimize to tray instead of closing."""
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Axinix AI",
                "Программа свёрнута в трей",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

        def quit_app(self):
            """Completely quit the application."""
            if self.is_running:
                if hasattr(self, "ai_cmd_queue"):
                    self.ai_cmd_queue.put("STOP")
                if hasattr(self, "audio_cmd_queue"):
                    self.audio_cmd_queue.put("STOP")
                if hasattr(self, "audio_process") and self.audio_process.is_alive():
                    self.audio_process.terminate()
                if hasattr(self, "ai_process") and self.ai_process.is_alive():
                    self.ai_process.terminate()
            if self.log_window:
                self.log_window.close()
            self.tray_icon.hide()
            QApplication.quit()

        def open_settings(self):
            SettingsDialog(self).exec()

        def update_ui(self):
            # Manage separate debug window
            if self.dev_mode:
                if not self.log_window:
                    self.log_window = LogWindow(self)
                self.log_window.show()
            else:
                if self.log_window:
                    self.log_window.hide()

            self.viz.set_dev_mode(self.dev_mode)
            self.update_button_style()

            # Update debug action text in tray
            if hasattr(self, 'tray_debug_action'):
                state = "Вкл" if self.dev_mode else "Выкл"
                self.tray_debug_action.setText(f"💻 Отладка: {state}")


    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("logo.png"))

    from setup_wizard import run_wizard_if_needed

    run_wizard_if_needed()

    # Check memory size and show cleanup dialog if needed
    try:
        # Load settings to check memory warning preferences
        memory_warning_limit = 500  # Default 500 MB
        memory_warning_disabled = False

        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings_data = json.load(f)
                memory_warning_limit = settings_data.get("memory_warning_limit", 500)
                memory_warning_disabled = settings_data.get(
                    "memory_warning_disabled", False
                )

        if not memory_warning_disabled:
            memory = MemoryManager()
            size_mb = memory.get_db_size_mb()

            if size_mb >= memory_warning_limit:
                dialog = MemoryCleanupDialog(memory, size_mb)
                dialog.exec()

                # Save user's choice to settings
                if dialog.action:
                    try:
                        settings_data = {}
                        if os.path.exists(SETTINGS_FILE):
                            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                                settings_data = json.load(f)

                        if dialog.action == "ignore":
                            settings_data["memory_warning_disabled"] = True
                        elif dialog.action == "remind_later":
                            settings_data["memory_warning_limit"] = dialog.remind_size
                        # 'cleaned' doesn't change settings

                        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                            json.dump(settings_data, f, indent=4)
                    except (json.JSONDecodeError, OSError) as e:
                        print(f"Memory warning settings write error: {e}")

            memory.close()
    except Exception as e:
        print(f"Memory check error: {e}")

    window = MainWindow()

    # Apply theme based on settings
    if window.current_theme == "light":
        app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    else:
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing

    try:
        multiprocessing.set_start_method("spawn")
    except RuntimeError:
        pass
        
    start_gui()



