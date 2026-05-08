import subprocess
from utils import command_exists, run_command

def manage_arch_packages(action: str, query: str = ""):
    """
    Manage Arch Linux packages (Official & AUR).
    Actions: 
    - 'search': Search for packages.
    - 'install': Show command to install packages.
    - 'update': Show command to update system.
    - 'health': Check for failed systemd services and disk space.
    """
    manager = "yay" if command_exists("yay") else "paru" if command_exists("paru") else "pacman"
    
    if action == "search":
        if not query: return "Query is required for search."
        # Use a shorter timeout for search
        result = run_command([manager, "-Ss", query], timeout=5)
        if result.returncode == 0:
            lines = result.stdout.splitlines()[:15] # Limit output
            return "\n".join(lines) + ("\n..." if len(result.stdout.splitlines()) > 15 else "")
        return f"Search failed: {result.stderr}"

    def get_terminal_cmd(cmd_list):
        for term in ["kitty", "alacritty", "konsole", "gnome-terminal", "xfce4-terminal", "xterm"]:
            if command_exists(term):
                if term in ["kitty", "alacritty"]:
                    return [term, "-e"] + cmd_list
                if term == "konsole":
                    return [term, "-e"] + cmd_list
                if term == "gnome-terminal":
                    return [term, "--"] + cmd_list
                if term == "xfce4-terminal":
                    return [term, "-e", " ".join(cmd_list)]
                if term == "xterm":
                    return [term, "-e"] + cmd_list
        return None

    if action == "install":
        if not query: return "Package name is required."
        full_cmd = [manager, "-S", query]
        term_cmd = get_terminal_cmd(full_cmd)
        if term_cmd:
            try:
                subprocess.Popen(term_cmd, start_new_session=True)
                return f"Very well Sir, I've opened a terminal to install {query} via {manager}."
            except Exception as e:
                return f"Failed to open terminal: {e}. Command: {' '.join(full_cmd)}"
        return f"No terminal emulator found. Please run manually: {' '.join(full_cmd)}"

    if action == "update":
        full_cmd = [manager, "-Syu"]
        term_cmd = get_terminal_cmd(full_cmd)
        if term_cmd:
            try:
                subprocess.Popen(term_cmd, start_new_session=True)
                return f"Certainly Sir, launching system update in a new terminal."
            except Exception as e:
                return f"Failed to open terminal: {e}. Command: {' '.join(full_cmd)}"
        return f"No terminal emulator found. Please run manually: {' '.join(full_cmd)}"

    if action == "health":
        health_report = []
        # Check failed services
        failed = run_command(["systemctl", "--failed", "--no-legend"])
        if failed.stdout.strip():
            health_report.append(f"⚠️ Failed services:\n{failed.stdout.strip()}")
        else:
            health_report.append("✅ No failed systemd services.")
        
        # Check disk space
        disk = run_command(["df", "-h", "/"])
        health_report.append(f"💾 Disk Usage (/): {disk.stdout.splitlines()[1].split()[4]} used.")
        
        # Check for .pacnew files
        pacnew = run_command(["find", "/etc", "-name", "*.pacnew"])
        if pacnew.stdout.strip():
            count = len(pacnew.stdout.splitlines())
            health_report.append(f"📦 Found {count} .pacnew files in /etc. Consider merging them.")
            
        return "\n\n".join(health_report)

    return f"Action '{action}' not recognized."

def register_plugin():
    tools = [manage_arch_packages]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
