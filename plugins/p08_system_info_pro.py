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
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            procs.append(p.info)
        
        procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_n = procs[:n]
        
        lines = [f"Sir, here are the top {n} processes by CPU usage:"]
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
