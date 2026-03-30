import datetime
import shutil
import subprocess
import webbrowser

import psutil
import requests

_http_session = requests.Session()
_http_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _run_command(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=6)


def open_website(url: str):
    """Open a URL in the default browser."""
    webbrowser.open(url)
    return f"Opening link: {url}"


def run_app(app_name: str):
    """Launch an app natively with Linux-first fallbacks."""
    app = (app_name or "").strip()
    if not app:
        return "Application name is required."

    # Try desktop launcher ids first.
    if _command_exists("gtk-launch"):
        result = _run_command(["gtk-launch", app])
        if result.returncode == 0:
            return f"Application {app} launched."

    # Try direct binary launch.
    binary = app.lower()
    if _command_exists(binary):
        try:
            subprocess.Popen(
                [binary],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Application {app} launched."
        except OSError as exc:
            return f"Application launch error: {exc}"

    # Try user service activation as a system-native fallback.
    if _command_exists("systemctl"):
        result = _run_command(["systemctl", "--user", "start", app])
        if result.returncode == 0:
            return f"Started user service: {app}"

    web_alternatives = {
        "spotify": "https://open.spotify.com",
        "discord": "https://discord.com/app",
        "telegram": "https://web.telegram.org",
        "whatsapp": "https://web.whatsapp.com",
        "slack": "https://app.slack.com",
        "notion": "https://www.notion.so",
        "figma": "https://www.figma.com",
        "youtube": "https://www.youtube.com",
        "netflix": "https://www.netflix.com",
        "twitch": "https://www.twitch.tv",
    }
    key = binary
    if key in web_alternatives:
        url = web_alternatives[key]
        webbrowser.open(url)
        return f"Application {app} is not installed. Opening web version: {url}"

    return f"Application {app} not found."


def get_system_stats():
    """Return CPU and RAM usage."""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    return f"System status: CPU: {cpu}%, RAM: {mem}%"


def media_play_pause():
    """Toggle active media playback via MPRIS/playerctl."""
    if not _command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = _run_command(["playerctl", "play-pause"])
    if result.returncode == 0:
        return "Media: Play/Pause"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def media_next():
    """Switch to the next track via MPRIS/playerctl."""
    if not _command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = _run_command(["playerctl", "next"])
    if result.returncode == 0:
        return "Media: Next track"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def media_prev():
    """Switch to the previous track via MPRIS/playerctl."""
    if not _command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = _run_command(["playerctl", "previous"])
    if result.returncode == 0:
        return "Media: Previous track"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def set_volume(action: str):
    """Change volume using wpctl (PipeWire) or pactl (PulseAudio)."""
    direction = (action or "").strip().lower()
    if direction not in {"up", "down"}:
        return "Volume action must be 'up' or 'down'."

    if _command_exists("wpctl"):
        cmd = [
            "wpctl",
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            "5%+" if direction == "up" else "5%-",
        ]
    elif _command_exists("pactl"):
        cmd = [
            "pactl",
            "set-sink-volume",
            "@DEFAULT_SINK@",
            "+5%" if direction == "up" else "-5%",
        ]
    else:
        return "Volume control unavailable: install wpctl or pactl."

    result = _run_command(cmd)
    if result.returncode == 0:
        return f"Volume changed: {direction}"
    err = (result.stderr or result.stdout or "").strip()
    return f"Volume control failed: {err or 'unknown error'}"


def get_city_time_info(city: str):
    """Return city-local hour and day period."""
    city_tz_map = {
        "kyiv": "Europe/Kiev",
        "kiev": "Europe/Kiev",
        "london": "Europe/London",
        "berlin": "Europe/Berlin",
        "paris": "Europe/Paris",
        "warsaw": "Europe/Warsaw",
        "los angeles": "America/Los_Angeles",
        "new york": "America/New_York",
        "chicago": "America/Chicago",
        "tokyo": "Asia/Tokyo",
        "seoul": "Asia/Seoul",
        "beijing": "Asia/Shanghai",
        "dubai": "Asia/Dubai",
    }

    zone = city_tz_map.get((city or "").strip().lower())
    hour = datetime.datetime.now().hour

    if zone:
        try:
            response = _http_session.get(
                f"https://timeapi.io/api/time/current/zone?timeZone={zone}",
                timeout=5,
            )
            if response.status_code == 200:
                hour = int(response.json().get("hour", hour))
        except requests.RequestException:
            pass

    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "day"
    elif 17 <= hour < 22:
        period = "evening"
    else:
        period = "night"

    return {
        "hour": hour,
        "period": period,
        "formatted_time": f"{hour:02d}:00",
        "city": city,
    }


def standby_mode():
    """Switch assistant into standby mode."""
    return "System switched to standby mode."


def lock_workstation():
    """Lock current user session via loginctl."""
    if not _command_exists("loginctl"):
        return "Screen lock unavailable: install systemd/loginctl."
    result = _run_command(["loginctl", "lock-session"])
    if result.returncode == 0:
        return "Screen locked successfully."
    err = (result.stderr or result.stdout or "").strip()
    return f"Screen lock failed: {err or 'unknown error'}"


def turn_off_screen():
    """Turn off display output immediately and lock session when possible."""
    lock_workstation()

    if _command_exists("xset"):
        result = _run_command(["xset", "dpms", "force", "off"])
        if result.returncode == 0:
            return "Display turned off."
        err = (result.stderr or result.stdout or "").strip()
        return f"Display power-off failed: {err or 'unknown error'}"

    if _command_exists("busctl"):
        # KDE/PowerDevil fallback via DBus call can vary by environment.
        return "Display off command unavailable via xset; session lock executed."

    return "Display off unavailable: install xset (or configure desktop DBus power action)."


def register_plugin():
    tools = [
        open_website,
        run_app,
        get_system_stats,
        media_play_pause,
        media_next,
        media_prev,
        set_volume,
        get_city_time_info,
        standby_mode,
        lock_workstation,
        turn_off_screen,
    ]
    mapping = {
        "open_website": open_website,
        "run_app": run_app,
        "get_system_stats": get_system_stats,
        "media_play_pause": media_play_pause,
        "media_next": media_next,
        "media_prev": media_prev,
        "set_volume": set_volume,
        "get_city_time_info": get_city_time_info,
        "standby_mode": standby_mode,
        "lock_workstation": lock_workstation,
        "turn_off_screen": turn_off_screen,
    }
    return tools, mapping
