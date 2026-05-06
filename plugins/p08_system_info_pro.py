import psutil
import socket
import time

import jarvis_config as cfg

SYSTEM_SNAPSHOT_ENABLED = cfg.feature_enabled("system_snapshot")
TOP_PROCESS_CACHE_TTL_SECONDS = cfg.top_process_cache_ttl_seconds()
_TOP_PROCESS_CACHE = {}


def _shorten(text: str, limit: int = 90) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")

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


def _collect_top_processes(n: int = 5):
    try:
        n = max(1, int(n))
    except (TypeError, ValueError):
        n = 5

    cache_key = n
    cached = _TOP_PROCESS_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached["ts"] < TOP_PROCESS_CACHE_TTL_SECONDS:
        return cached["value"]

    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                p.cpu_percent(interval=None)
                procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        time.sleep(0.1)

        final_list = []
        for p in procs:
            try:
                cpu = p.cpu_percent(interval=None)
                mem = p.memory_percent()
                final_list.append(
                    {
                        "pid": p.info["pid"],
                        "name": p.info["name"],
                        "cpu": cpu,
                        "mem": mem,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        final_list.sort(key=lambda x: (x["cpu"], x["mem"]), reverse=True)
        top_n = final_list[:n]
        _TOP_PROCESS_CACHE[cache_key] = {"ts": now, "value": top_n}
        return top_n
    except Exception:
        return []


def get_top_processes(n: int = 5):
    """Return the top N processes by CPU and RAM usage."""
    try:
        top_n = _collect_top_processes(n)
        lines = [f"Sir, here are the top {len(top_n)} processes:"]
        for p in top_n:
            lines.append(
                f"  - {p['name']} (PID: {p['pid']}): CPU: {p['cpu']:.1f}%, RAM: {p['mem']:.1f}%"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving processes: {e}"


def get_system_snapshot(n: int = 5):
    """AI DESCRIPTION: Return a combined system health snapshot with cached process pressure."""
    try:
        top_n = _collect_top_processes(n)
        summary = get_detailed_stats()
        lines = ["=== SYSTEM SNAPSHOT ===", summary, "", f"Top {len(top_n)} processes:"]
        if top_n:
            for proc in top_n:
                lines.append(
                    f"  - {proc['name']} (PID: {proc['pid']}): CPU {proc['cpu']:.1f}%, RAM {proc['mem']:.1f}%"
                )
        else:
            lines.append("  No running processes could be sampled.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving system snapshot: {e}"

def register_plugin():
    tools = [get_detailed_stats, get_top_processes]
    if SYSTEM_SNAPSHOT_ENABLED:
        tools.append(get_system_snapshot)
    mapping = {
        "get_detailed_stats": get_detailed_stats,
        "get_top_processes": get_top_processes,
    }
    if SYSTEM_SNAPSHOT_ENABLED:
        mapping["get_system_snapshot"] = get_system_snapshot
    return tools, mapping
