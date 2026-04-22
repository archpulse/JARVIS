def help_arch_capabilities():
    """
    Explain the available Arch Linux 'Cheat Code' capabilities and how to use them.
    """
    return (
        "🚀 Arch Linux 'Cheat Codes' are now ACTIVE!\n\n"
        "You can now manage your system with simple commands:\n"
        "1. **Package Manager**: 'Search for package X', 'How do I install Y?', or 'Update my system'.\n"
        "2. **System Health**: 'Check system health' or 'Are there any failed services?' (checks disk, services, and .pacnew files).\n"
        "3. **Arch Wiki Oracle**: 'Search Arch Wiki for [topic]' - gets direct answers from wiki.archlinux.org.\n"
        "4. **Connectivity**: 'List wifi networks', 'Connect to wifi [SSID]', or 'Toggle bluetooth'.\n"
        "5. **System Info**: 'Show fastfetch' or 'System summary'.\n\n"
        "I will use yay, paru, or pacman automatically based on what's installed."
    )

def register_plugin():
    tools = [help_arch_capabilities]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
