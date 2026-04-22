import psutil
import socket

def get_detailed_stats():
    """Return comprehensive system stats including disk and network info."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        # Network info
        net_io = psutil.net_io_counters()
        sent = net_io.bytes_sent / (1024 * 1024)
        recv = net_io.bytes_recv / (1024 * 1024)
        
        # IP Address
        hostname = socket.gethostname()
        try:
            ip_addr = socket.gethostbyname(hostname)
        except:
            ip_addr = "Unknown"
            
        return (f"Sir, the system is performing as follows:\n"
                f"CPU Load: {cpu}%\n"
                f"RAM Usage: {mem}%\n"
                f"Disk Usage: {disk}%\n"
                f"Network: {sent:.1f} MB sent, {recv:.1f} MB received\n"
                f"Local IP: {ip_addr}")
    except Exception as e:
        return f"Error retrieving detailed stats: {e}"

def get_top_processes(n: int = 5):
    """Return the top N CPU-consuming processes."""
    try:
        import time
        # Initialize CPU tracking for all processes
        procs_objs = []
        for p in psutil.process_iter(['pid', 'name']):
            try:
                p.cpu_percent(interval=None)
                procs_objs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Wait a brief moment to accumulate CPU usage
        time.sleep(0.2)
        
        procs_info = []
        for p in procs_objs:
            try:
                # Get the accumulated CPU percent
                cpu = p.cpu_percent(interval=None)
                info = p.info
                info['cpu_percent'] = cpu
                procs_info.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        procs_info.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        top_n = procs_info[:n]
        
        lines = [f"Sir, here are the top {len(top_n)} processes by CPU usage:"]
        for p in top_n:
            lines.append(f"  - {p['name']} (PID: {p['pid']}): {p['cpu_percent']}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving processes: {e}"

def register_plugin():
    tools = [get_detailed_stats, get_top_processes]
    mapping = {
        "get_detailed_stats": get_detailed_stats,
        "get_top_processes": get_top_processes,
    }
    return tools, mapping
