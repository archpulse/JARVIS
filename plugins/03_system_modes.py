import os
import subprocess

def dinner_mode():
    """
    Call this when the user asks to activate dinner mode ("Обед").
    Closes Google Chrome and re-opens it with Netflix.
    """
    os.system("killall chrome")
    os.system("killall google-chrome")
    os.system("killall google-chrome-stable")
    os.system("killall chromium")
    
    subprocess.Popen(["google-chrome-stable", "https://netflix.com"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "Режим 'Обед' активирован: браузер перезапущен с Netflix."

def gaming_mode():
    """
    Call this when the user asks to activate gaming mode ("Режим игр").
    Closes kitty terminal, closes Chrome, and opens PortProton.
    """
    os.system("killall kitty")
    os.system("killall chrome")
    os.system("killall google-chrome")
    os.system("killall google-chrome-stable")
    
    subprocess.Popen(["flatpak", "run", "ru.linux_gaming.PortProton"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "Игровой режим активирован: терминал и браузер закрыты, PortProton запущен."

def shutdown_pc():
    """
    Shuts down (turns off) the PC.
    """
    os.system("systemctl poweroff")
    return "Выключаю ПК..."

def reboot_pc():
    """
    Reboots (restarts) the PC.
    """
    os.system("systemctl reboot")
    return "Перезагружаю ПК..."

def reboot_to_boot_menu():
    """
    Reboots the PC directly into the Boot Menu.
    """
    os.system("systemctl reboot --boot-loader-menu=0")
    return "Перезагружаю в Boot Menu..."

def register_plugin():
    tools = [
        dinner_mode,
        gaming_mode,
        shutdown_pc,
        reboot_pc,
        reboot_to_boot_menu,
    ]
    mapping = {
        "dinner_mode": dinner_mode,
        "gaming_mode": gaming_mode,
        "shutdown_pc": shutdown_pc,
        "reboot_pc": reboot_pc,
        "reboot_to_boot_menu": reboot_to_boot_menu,
    }
    return tools, mapping
