import subprocess
import os

def _check_playerctl():
    """Returns True if playerctl is installed, False otherwise."""
    try:
        res = subprocess.run(["which", "playerctl"], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def media_play_pause():
    """
    Toggles play/pause for the currently active media player on the system.
    Use this when the user says "pause", "play", "stop", or "отключи музыку/видео".
    """
    if not _check_playerctl():
        return "ВНИМАНИЕ: Утилита playerctl не установлена. Скажите пользователю установить её через 'sudo dnf install playerctl' или 'sudo apt install playerctl'."
    os.system("playerctl play-pause")
    return "Медиа переключено (плей/пауза)."

def media_next():
    """
    Skips to the next track or video on the active media player.
    Use this when the user says "next", "следующий трек", "дальше".
    """
    if not _check_playerctl():
        return "ВНИМАНИЕ: Утилита playerctl не установлена."
    os.system("playerctl next")
    return "Включен следующий трек/видео."

def media_previous():
    """
    Skips to the previous track or video on the active media player.
    """
    if not _check_playerctl():
        return "ВНИМАНИЕ: Утилита playerctl не установлена."
    os.system("playerctl previous")
    return "Включен предыдущий трек/видео."

def system_volume_set(level_percent: int):
    """
    Sets the system volume to a specific percentage (between 0 and 100).
    Use this when the user says "сделай громкость на X%", "тише", "громче".
    
    Args:
        level_percent: The volume percentage to set (0 to 100).
    """
    if level_percent < 0:
        level_percent = 0
    if level_percent > 100:
        level_percent = 100
        
    # Attempt Pipewire/Wireplumber
    try:
        res = subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{level_percent}%"], capture_output=True)
        if res.returncode == 0:
            return f"Громкость системы успешно установлена на {level_percent}%."
    except Exception:
        pass

    # Attempt PulseAudio/ALSA
    try:
        res = subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level_percent}%"], capture_output=True)
        if res.returncode == 0:
            return f"Громкость системы успешно установлена на {level_percent}%."
    except Exception:
        pass

    return "Не удалось изменить громкость. В системе нет wpctl или amixer."

def register_plugin():
    tools = [
        media_play_pause,
        media_next,
        media_previous,
        system_volume_set,
    ]
    mapping = {
        "media_play_pause": media_play_pause,
        "media_next": media_next,
        "media_previous": media_previous,
        "system_volume_set": system_volume_set,
    }
    return tools, mapping
