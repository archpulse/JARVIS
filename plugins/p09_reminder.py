import time
import threading
import subprocess
import shutil

# Try to import global helper from main
try:
    from main import inject_ai_text
except ImportError:
    def inject_ai_text(text: str):
        return False

def _reminder_thread(seconds: float, message: str):
    time.sleep(seconds)
    # 1. Output to console
    print(f"\n🔔 REMINDER: {message}")
    
    # 2. Try system notification (Linux)
    if shutil.which("notify-send"):
        try:
            subprocess.run(["notify-send", "J.A.R.V.I.S. Reminder", message], check=False)
        except:
            pass
    
    # 3. Voice notification via injected AI text
    voice_prompt = f"Sir, your reminder: {message}"
    if not inject_ai_text(voice_prompt):
        # Fallback if injection fails - maybe try to print something the AI loop might catch
        print(f"VOICE_INJECTION_FAILED: {voice_prompt}")

def set_timer(seconds: int = 0, minutes: int = 0, message: str = "Timer finished"):
    """Set a timer for N minutes and/or M seconds with a reminder message."""
    try:
        total_seconds = float(minutes * 60 + seconds)
        if total_seconds <= 0:
            return "Sir, the duration must be greater than zero."
            
        t = threading.Thread(target=_reminder_thread, args=(total_seconds, message), daemon=True)
        t.start()
        
        parts = []
        if minutes > 0: parts.append(f"{minutes} minutes")
        if seconds > 0: parts.append(f"{seconds} seconds")
        duration_str = " and ".join(parts)
        
        return f"Very good, Sir. The timer is set for {duration_str}. I will inform you when it expires."
    except Exception as e:
        return f"Error setting timer: {e}"

def register_plugin():
    tools = [set_timer]
    mapping = {
        "set_timer": set_timer,
    }
    return tools, mapping
