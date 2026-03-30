def capture_screen():
    """
    Captures the user's current screen (resizing to 1280x720). 
    Call this ONLY when the user explicitly asks you to look at their screen, 
    read an error, or analyze visual context.
    """
    return "SCREENSHOT_REQUESTED"

def register_plugin():
    return [capture_screen], {"capture_screen": capture_screen}
