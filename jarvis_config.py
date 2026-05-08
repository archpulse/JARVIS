"""Centralized env/config helpers for J.A.R.V.I.S."""

from __future__ import annotations

import os

DEFAULT_AI_DATA_DIR = os.path.expanduser("~/.jarvis/.ai")
DEFAULT_SETTINGS_FILE_NAME = "settings.json"
DEFAULT_ENV_FILE_NAME = ".env"
DEFAULT_MEMORY_DB_NAME = "memory.db"

DEFAULT_MODEL_ID = "gemini-3.1-flash-live-preview"
DEFAULT_API_VERSION = "v1alpha"
DEFAULT_VERSION = "1.2.2"
DEFAULT_PLUGIN_DAILY_LIMIT = 250

DEFAULT_AUDIO_IN_RATE = 16000
DEFAULT_AUDIO_OUT_RATE = 48000
DEFAULT_AUDIO_IN_BUFFER_FRAMES = 2048
DEFAULT_AUDIO_OUT_BUFFER_FRAMES = 512

DEFAULT_TOOL_TIMEOUT_SECONDS = 25.0
DEFAULT_SYNC_TOOL_TIMEOUT_SECONDS = 18.0
DEFAULT_PLUGIN_RELOAD_INTERVAL_SECONDS = 5.0
DEFAULT_MEMORY_WARNING_LIMIT_MB = 500
DEFAULT_DEFAULT_CITY = "Ужгород"

DEFAULT_WEB_RESEARCH_CACHE_TTL_SECONDS = 600
DEFAULT_WEB_RESEARCH_CACHE_SIZE = 50
DEFAULT_TOP_PROCESS_CACHE_TTL_SECONDS = 30
DEFAULT_CITY_TIME_CACHE_TTL_SECONDS = 600
DEFAULT_PLUGIN_CONFIRM_TTL_SECONDS = 180
DEFAULT_MAX_DAILY_PLUGIN_REVIEWS = DEFAULT_PLUGIN_DAILY_LIMIT


def _expand_path(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


def env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def env_int(name: str, default: int) -> int:
    try:
        return int(env_str(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(env_str(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on", "y", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "n", "disabled"}:
        return False
    return default


def _resolve_path(env_name: str, default_path: str) -> str:
    return _expand_path(env_str(env_name, default_path))


def ai_data_dir() -> str:
    return _resolve_path("JARVIS_AI_DATA_DIR", DEFAULT_AI_DATA_DIR)


def settings_file() -> str:
    return _resolve_path(
        "JARVIS_SETTINGS_FILE",
        os.path.join(ai_data_dir(), DEFAULT_SETTINGS_FILE_NAME),
    )


def env_file() -> str:
    return _resolve_path(
        "JARVIS_ENV_FILE",
        os.path.join(ai_data_dir(), DEFAULT_ENV_FILE_NAME),
    )


def memory_db_file() -> str:
    return _resolve_path(
        "JARVIS_MEMORY_DB",
        os.path.join(ai_data_dir(), DEFAULT_MEMORY_DB_NAME),
    )


def model_id() -> str:
    return env_str("JARVIS_MODEL_ID", DEFAULT_MODEL_ID)


def api_version() -> str:
    return env_str("JARVIS_API_VERSION", DEFAULT_API_VERSION)


def version() -> str:
    return env_str("JARVIS_VERSION", DEFAULT_VERSION)


def plugin_daily_limit() -> int:
    return env_int("JARVIS_PLUGIN_DAILY_LIMIT", DEFAULT_PLUGIN_DAILY_LIMIT)


def audio_input_rate() -> int:
    return env_int("JARVIS_AUDIO_IN_RATE", DEFAULT_AUDIO_IN_RATE)


def audio_output_rate() -> int:
    return env_int("JARVIS_AUDIO_OUT_RATE", DEFAULT_AUDIO_OUT_RATE)


def audio_input_buffer_frames() -> int:
    return env_int("JARVIS_AUDIO_IN_BUFFER_FRAMES", DEFAULT_AUDIO_IN_BUFFER_FRAMES)


def audio_output_buffer_frames() -> int:
    return env_int("JARVIS_AUDIO_OUT_BUFFER_FRAMES", DEFAULT_AUDIO_OUT_BUFFER_FRAMES)


def tool_timeout_seconds() -> float:
    return env_float("JARVIS_TOOL_TIMEOUT_SECONDS", DEFAULT_TOOL_TIMEOUT_SECONDS)


def sync_tool_timeout_seconds() -> float:
    return env_float("JARVIS_SYNC_TOOL_TIMEOUT_SECONDS", DEFAULT_SYNC_TOOL_TIMEOUT_SECONDS)


def plugin_reload_interval_seconds() -> float:
    return env_float(
        "JARVIS_PLUGIN_RELOAD_INTERVAL_SECONDS",
        DEFAULT_PLUGIN_RELOAD_INTERVAL_SECONDS,
    )


def memory_warning_limit_mb() -> int:
    return env_int("JARVIS_MEMORY_WARNING_LIMIT_MB", DEFAULT_MEMORY_WARNING_LIMIT_MB)


def default_city() -> str:
    return env_str("JARVIS_DEFAULT_CITY", DEFAULT_DEFAULT_CITY)


def web_research_cache_ttl_seconds() -> int:
    return env_int(
        "JARVIS_WEB_RESEARCH_CACHE_TTL_SECONDS",
        DEFAULT_WEB_RESEARCH_CACHE_TTL_SECONDS,
    )


def web_research_cache_size() -> int:
    return env_int(
        "JARVIS_WEB_RESEARCH_CACHE_SIZE",
        DEFAULT_WEB_RESEARCH_CACHE_SIZE,
    )


def top_process_cache_ttl_seconds() -> int:
    return env_int(
        "JARVIS_TOP_PROCESS_CACHE_TTL_SECONDS",
        DEFAULT_TOP_PROCESS_CACHE_TTL_SECONDS,
    )


def city_time_cache_ttl_seconds() -> int:
    return env_int(
        "JARVIS_CITY_TIME_CACHE_TTL_SECONDS",
        DEFAULT_CITY_TIME_CACHE_TTL_SECONDS,
    )


def plugin_confirm_ttl_seconds() -> int:
    return env_int(
        "JARVIS_PLUGIN_CONFIRM_TTL_SECONDS",
        DEFAULT_PLUGIN_CONFIRM_TTL_SECONDS,
    )


def max_daily_plugin_reviews() -> int:
    return env_int(
        "JARVIS_MAX_DAILY_PLUGIN_REVIEWS",
        plugin_daily_limit(),
    )


def feature_enabled(name: str, default: bool = False) -> bool:
    normalized = name.strip().upper()
    if not normalized.startswith("JARVIS_FEATURE_"):
        normalized = f"JARVIS_FEATURE_{normalized}"
    return env_bool(normalized, default)
