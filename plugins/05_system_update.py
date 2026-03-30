import asyncio
import shutil

async def update_arch_system():
    """Обновляет систему Arch Linux, открывая окно терминала."""
    if not shutil.which("pacman"):
        return "Команда 'pacman' не найдена. Это не Arch Linux."

    terms = ["kitty", "wezterm", "alacritty", "konsole", "gnome-terminal", "xterm"]
    term = next((t for t in terms if shutil.which(t)), None)

    if not term:
        return "Ошибка: Не удалось найти терминал для запуска обновления."

    # Убрали `read` в конце — терминал закроется сам после завершения pacman
    cmd = (
        f"{term} -e sh -c "
        f"'echo \"[AxiNix OS] Запуск обновления системы...\"; "
        f"sudo pacman -Syu; "
        f"echo \"\"; echo \"Обновление завершено.\"'"
    )

    # create_subprocess_shell + await proc.wait() — ждём завершения без таймаута
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.wait()

    if proc.returncode == 0:
        return "Сэр, система успешно обновлена."
    else:
        return f"Сэр, обновление завершилось с кодом {proc.returncode}. Рекомендую проверить терминал."


def register_plugin():
    tools = [update_arch_system]
    mapping = {
        "update_arch_system": update_arch_system
    }
    return tools, mapping
