import os
import subprocess
import signal
import logging

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

_logger = logging.getLogger("system_modes")

# Browsers that dinner_mode will target
_BROWSER_NAMES = frozenset({"chrome", "chromium", "google-chrome", "google-chrome-stable"})

# Processes to kill in gaming mode
_TERMINAL_NAMES = frozenset({"kitty", "konsole", "gnome-terminal", "xfce4-terminal", "alacritty"})
_BROWSER_NAMES_GAMING = frozenset({"chrome", "chromium", "google-chrome", "google-chrome-stable"})


def _kill_processes_safe(names, own_uid=None):
    """Kill processes by name using psutil with owner check.

    Args:
        names: frozenset of process names to target
        own_uid: if set, only kill processes owned by this UID (default: current user)
    Returns:
        list of (pid, name) tuples that were terminated
    """
    killed = []
    if own_uid is None:
        own_uid = os.getuid()

    for proc in psutil.process_iter(["pid", "name", "uid"]):
        try:
            pinfo = proc.info
            if pinfo["name"] in names and pinfo["uid"] == own_uid:
                proc.terminate()
                killed.append((pinfo["pid"], pinfo["name"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Give them a moment to gracefully exit, then kill stubborn ones
    gone = []
    for pid, name in killed:
        try:
            p = psutil.Process(pid)
            p.wait(timeout=3)
        except psutil.TimeoutExpired:
            try:
                p.kill()
                gone.append((pid, name))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return killed + gone


def _launch_app(cmd, check_exists=None):
    """Launch application with fallback for common paths.

    Args:
        cmd: list of command and arguments
        check_exists: optional path to check before launching
    """
    if check_exists and not os.path.exists(check_exists):
        # Try to find the binary in PATH
        import shutil
        found = shutil.which(cmd[0])
        if found:
            cmd[0] = found
        else:
            _logger.warning(f"Command not found: {cmd[0]}")
            return False

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        _logger.warning(f"Failed to launch: {cmd[0]}")
        return False


def dinner_mode():
    """
    Call this when the user asks to activate dinner mode ("Dinner").
    Closes Google Chrome and re-opens it with Netflix.
    """
    if not _HAS_PSUTIL:
        # Fallback: use pkill if psutil unavailable
        for browser in _BROWSER_NAMES:
            try:
                subprocess.run(["pkill", "-x", browser], timeout=5)
            except Exception:
                pass
    else:
        _kill_processes_safe(_BROWSER_NAMES)

    # Launch Chrome with Netflix
    _launch_app(["google-chrome-stable", "https://netflix.com"])
    return "Dinner mode activated: browser restarted with Netflix."


def gaming_mode():
    """
    Call this when the user asks to activate gaming mode ("Gaming mode").
    Closes kitty terminal, closes Chrome, and opens PortProton.
    """
    targets = _TERMINAL_NAMES | _BROWSER_NAMES_GAMING

    if not _HAS_PSUTIL:
        for name in targets:
            try:
                subprocess.run(["pkill", "-x", name], timeout=5)
            except Exception:
                pass
    else:
        _kill_processes_safe(targets)

    # Launch PortProton via flatpak
    _launch_app(["flatpak", "run", "ru.linux_gaming.PortProton"])
    return "Gaming mode activated: terminal and browser closed, PortProton launched."

def shutdown_pc():
    """
    Shuts down (turns off) the PC.
    """
    try:
        subprocess.run(["systemctl", "poweroff"], timeout=5, check=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        _logger.warning(f"shutdown failed: {e}")
    return "Shutting down PC..."


def reboot_pc():
    """
    Reboots (restarts) the PC.
    """
    try:
        subprocess.run(["systemctl", "reboot"], timeout=5, check=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        _logger.warning(f"reboot failed: {e}")
    return "Rebooting PC..."


def reboot_to_boot_menu():
    """
    Reboots the PC directly into the Boot Menu.
    """
    try:
        subprocess.run(["systemctl", "reboot", "--boot-loader-menu=0"], timeout=5, check=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        _logger.warning(f"reboot to boot menu failed: {e}")
    return "Rebooting to Boot Menu..."

def manage_system_modes(action: str):
    """
    Manage system modes and power state. Actions: 'dinner_mode', 'gaming_mode', 'shutdown_pc', 'reboot_pc', 'reboot_to_boot_menu'.
    """
    if action == "dinner_mode": return dinner_mode()
    elif action == "gaming_mode": return gaming_mode()
    elif action == "shutdown_pc": return shutdown_pc()
    elif action == "reboot_pc": return reboot_pc()
    elif action == "reboot_to_boot_menu": return reboot_to_boot_menu()
    else: return "Unknown action."

def register_plugin():
    tools = [manage_system_modes]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
