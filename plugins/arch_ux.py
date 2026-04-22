from utils import command_exists, run_command

def arch_ux_manager(action: str, ssid: str = "", password: str = ""):
    """
    Manage Arch Linux Connectivity and UI.
    Actions:
    - 'fastfetch': Get system summary.
    - 'wifi_list': Show available WiFi networks.
    - 'wifi_connect': Connect to WiFi (needs ssid and password).
    - 'bluetooth_toggle': Turn Bluetooth on or off.
    - 'bluetooth_status': Check Bluetooth power state.
    """
    if action == "fastfetch":
        if command_exists("fastfetch"):
            res = run_command(["fastfetch", "--pipe"])
            return res.stdout if res.returncode == 0 else "Fastfetch execution error."
        elif command_exists("neofetch"):
            res = run_command(["neofetch", "--stdout"])
            return res.stdout
        return "Fastfetch/Neofetch not installed. Try 'yay -S fastfetch'."

    if action == "wifi_list":
        if not command_exists("nmcli"): return "NetworkManager (nmcli) not installed."
        res = run_command(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi"])
        return res.stdout if res.returncode == 0 else "Could not list WiFi networks."

    if action == "wifi_connect":
        if not ssid: return "SSID is required to connect."
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if password: cmd.extend(["password", password])
        res = run_command(cmd)
        return res.stdout if res.returncode == 0 else f"Failed to connect: {res.stderr}"

    if action == "bluetooth_status":
        if not command_exists("bluetoothctl"): return "bluez-utils (bluetoothctl) not installed."
        res = run_command(["bluetoothctl", "show"])
        status = "ON" if "Powered: yes" in res.stdout else "OFF"
        return f"Bluetooth is currently {status}."

    if action == "bluetooth_toggle":
        if not command_exists("bluetoothctl"): return "bluez-utils (bluetoothctl) not installed."
        res = run_command(["bluetoothctl", "show"])
        new_state = "off" if "Powered: yes" in res.stdout else "on"
        run_command(["bluetoothctl", "power", new_state])
        return f"Bluetooth has been turned {new_state.upper()}."

    return f"Action '{action}' is not supported by Arch UX Manager."

def register_plugin():
    tools = [arch_ux_manager]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
