import datetime
import webbrowser
import psutil
import requests
from utils import command_exists, run_command

_http_session = requests.Session()


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
    if command_exists("gtk-launch"):
        result = run_command(["gtk-launch", app])
        if result.returncode == 0:
            return f"Application {app} launched."

    # Try direct binary launch.
    binary = app.lower()
    if command_exists(binary):
        try:
            import subprocess
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
    if command_exists("systemctl"):
        result = run_command(["systemctl", "--user", "start", app])
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
    if not command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = run_command(["playerctl", "play-pause"])
    if result.returncode == 0:
        return "Media: Play/Pause"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def media_next():
    """Switch to the next track via MPRIS/playerctl."""
    if not command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = run_command(["playerctl", "next"])
    if result.returncode == 0:
        return "Media: Next track"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def media_prev():
    """Switch to the previous track via MPRIS/playerctl."""
    if not command_exists("playerctl"):
        return "Media control unavailable: install playerctl."
    result = run_command(["playerctl", "previous"])
    if result.returncode == 0:
        return "Media: Previous track"
    err = (result.stderr or result.stdout or "").strip()
    return f"Media control failed: {err or 'no active player'}"


def set_volume(action: str):
    """Change volume using wpctl (PipeWire) or pactl (PulseAudio)."""
    direction = (action or "").strip().lower()
    if direction not in {"up", "down"}:
        return "Volume action must be 'up' or 'down'."

    if command_exists("wpctl"):
        cmd = [
            "wpctl",
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            "5%+" if direction == "up" else "5%-",
        ]
    elif command_exists("pactl"):
        cmd = [
            "pactl",
            "set-sink-volume",
            "@DEFAULT_SINK@",
            "+5%" if direction == "up" else "-5%",
        ]
    else:
        return "Volume control unavailable: install wpctl or pactl."

    result = run_command(cmd)
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


def enable_wwd_mode():
    """Switch assistant into Wake Word Detection (WWD) mode."""
    return "System switched to WWD mode."


def lock_workstation():
    """Lock current user session via loginctl."""
    if not command_exists("loginctl"):
        return "Screen lock unavailable: install systemd/loginctl."
    result = run_command(["loginctl", "lock-session"])
    if result.returncode == 0:
        return "Screen locked successfully."
    err = (result.stderr or result.stdout or "").strip()
    return f"Screen lock failed: {err or 'unknown error'}"


def turn_off_screen():
    """Turn off display output immediately and lock session when possible."""
    lock_workstation()

    if command_exists("xset"):
        result = run_command(["xset", "dpms", "force", "off"])
        if result.returncode == 0:
            return "Display turned off."
        err = (result.stderr or result.stdout or "").strip()
        return f"Display power-off failed: {err or 'unknown error'}"

    if command_exists("busctl"):
        # KDE/PowerDevil fallback via DBus call can vary by environment.
        return "Display off command unavailable via xset; session lock executed."

    return "Display off unavailable: install xset (or configure desktop DBus power action)."


def manage_system(action: str, url: str = "", app_name: str = "", volume_direction: str = "", city: str = ""):
    """Manage system functions. Actions: 'open_website' (needs url), 'run_app' (needs app_name), 'get_system_stats', 'media_play_pause', 'media_next', 'media_prev', 'set_volume' (needs volume_direction 'up' or 'down'), 'get_city_time_info' (needs city), 'standby_mode', 'lock_workstation', 'turn_off_screen', 'enable_wwd_mode'."""
    if action == "open_website": return open_website(url)
    elif action == "run_app": return run_app(app_name)
    elif action == "get_system_stats": return get_system_stats()
    elif action == "media_play_pause": return media_play_pause()
    elif action == "media_next": return media_next()
    elif action == "media_prev": return media_prev()
    elif action == "set_volume": return set_volume(volume_direction)
    elif action == "get_city_time_info": return get_city_time_info(city)
    elif action == "standby_mode": return enable_wwd_mode()
    elif action == "lock_workstation": return lock_workstation()
    elif action == "turn_off_screen": return turn_off_screen()
    elif action == "enable_wwd_mode": return enable_wwd_mode()
    else: return "Unknown action."

def register_plugin():
    tools = [manage_system]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
