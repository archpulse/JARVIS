import asyncio
import shutil

async def update_arch_system():
    """Updates Arch Linux system by opening a terminal window."""
    if not shutil.which("pacman"):
        return "Command 'pacman' not found. This is not Arch Linux."

    terms = ["kitty", "wezterm", "alacritty", "konsole", "gnome-terminal", "xterm"]
    term = next((t for t in terms if shutil.which(t)), None)

    if not term:
        return "Error: Could not find a terminal to launch the update."

    # Removed 'read' at the end - terminal will close itself after pacman completes
    cmd = (
        f"{term} -e sh -c "
        f"'echo \"[J.A.R.V.I.S. OS] Starting system update...\"; "
        f"sudo pacman -Syu; "
        f"echo \"\"; echo \"Update complete.\"'"
    )

    # create_subprocess_shell + await proc.wait() - waiting for completion without timeout
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.wait()

    if proc.returncode == 0:
        return "Sir, the system has been successfully updated."
    else:
        return f"Sir, the update finished with code {proc.returncode}. I recommend checking the terminal."


def register_plugin():
    tools = [update_arch_system]
    mapping = {
        "update_arch_system": update_arch_system
    }
    return tools, mapping
