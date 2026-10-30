import time
import os
import platform
import socket
import threading
import getpass
import logging
from functools import wraps
from datetime import datetime

import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PulseDeck API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get(
        "PULSEDECK_CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
    ).split(",") if origin.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_net_prev = {"counters": None, "time": None}
_disk_prev = {"counters": None, "time": None}

logger = logging.getLogger(__name__)


def optional_metric(reader, default=None):
    """Unsupported or inaccessible OS counters must not break the whole snapshot."""
    try:
        return reader()
    except (OSError, psutil.Error, NotImplementedError, AttributeError):
        logger.debug("Metric unavailable: %s", reader, exc_info=True)
        return default


# Serialize counter updates: simultaneous clients must not race on previous samples.
_metrics_lock = threading.Lock()


def serialized(reader):
    @wraps(reader)
    def wrapped(*args, **kwargs):
        with _metrics_lock:
            return reader(*args, **kwargs)
    return wrapped


_u = platform.uname()
try:
    _current_user = getpass.getuser()
except Exception:
    _current_user = "N/A"

_STATIC = {
    "hostname": socket.gethostname(),
    "os": f"{_u.system} {_u.release}",
    "arch": _u.machine,
    "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%d/%m/%Y %H:%M"),
    "user": _current_user,
    "cpu_model": platform.processor() or "N/A",
    "cpu_physical": psutil.cpu_count(logical=False) or psutil.cpu_count() or 1,
    "cpu_logical": psutil.cpu_count(logical=True) or 1,
    "cpu_arch": platform.machine(),
}

psutil.cpu_percent(interval=None, percpu=True)


def bytes_to_human(n): 
    if n is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


_proc_cache = {"processes": [], "total_threads": 0, "proc_count": 0}
_proc_lock = threading.Lock()


def _refresh_processes():
    proc_list = []
    total_threads = 0
    for p in psutil.process_iter(["pid", "name", "status", "cpu_percent",
                                   "memory_info", "num_threads", "username"]):
        try:
            info = p.info
            proc_list.append(info)
            total_threads += info.get("num_threads") or 0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    proc_count = len(proc_list)
    proc_list.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    top = [
        {
            "pid": p.get("pid"),
            "name": (p.get("name") or "")[:30],
            "status": p.get("status", ""),
            "cpu_percent": round(p.get("cpu_percent") or 0, 1),
            "ram": bytes_to_human(p["memory_info"].rss) if p.get("memory_info") else "—",
            "threads": p.get("num_threads"),
            "user": (p.get("username") or "")[:20],
        }
        for p in proc_list[:35]
    ]

    with _proc_lock:
        _proc_cache["processes"] = top
        _proc_cache["total_threads"] = total_threads
        _proc_cache["proc_count"] = proc_count



def _proc_worker():
    while True:
        try:
            _refresh_processes()
        except (OSError, psutil.Error, NotImplementedError):
            logger.debug("Process snapshot unavailable", exc_info=True)
        time.sleep(2.0)


threading.Thread(target=_proc_worker, daemon=True).start()


def get_uptime():
    secs = time.time() - psutil.boot_time()
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h}h {m}m {s}s"


@app.get("/api/metrics")
@serialized
def get_metrics():
    now = time.monotonic()

    per_core = psutil.cpu_percent(interval=None, percpu=True)
    cpu_total = sum(per_core) / len(per_core) if per_core else 0
    freq = optional_metric(lambda: psutil.cpu_freq())
    cpu_stats = psutil.cpu_stats()
    cpu_times = psutil.cpu_times()

    try:
        load = list(psutil.getloadavg())
    except (AttributeError, OSError, NotImplementedError):
        load = [None, None, None]

    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disk_r_speed = disk_w_speed = "N/A"
    dio = None
    try:
        dio = psutil.disk_io_counters()
        if dio is not None and _disk_prev["counters"] and _disk_prev["time"]:
            dt = now - _disk_prev["time"]
            if dt > 0:
                disk_r_speed = bytes_to_human(max(0, dio.read_bytes - _disk_prev["counters"].read_bytes) / dt) + "/s"
                disk_w_speed = bytes_to_human(max(0, dio.write_bytes - _disk_prev["counters"].write_bytes) / dt) + "/s"
        _disk_prev["counters"] = dio
        _disk_prev["time"] = now
    except Exception:
        pass

    partitions = []
    for p in optional_metric(lambda: psutil.disk_partitions(all=False), []):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            partitions.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
                "total": bytes_to_human(usage.total),
                "used": bytes_to_human(usage.used),
                "free": bytes_to_human(usage.free),
                "percent": usage.percent,
            })
        except Exception:
            pass

    net_up_speed = net_dn_speed = "N/A"
    net = optional_metric(psutil.net_io_counters)
    if net is not None and _net_prev["counters"] and _net_prev["time"]:
        dt = now - _net_prev["time"]
        if dt > 0:
            net_up_speed = bytes_to_human(max(0, net.bytes_sent - _net_prev["counters"].bytes_sent) / dt) + "/s"
            net_dn_speed = bytes_to_human(max(0, net.bytes_recv - _net_prev["counters"].bytes_recv) / dt) + "/s"
    _net_prev["counters"] = net
    _net_prev["time"] = now

    addrs = optional_metric(psutil.net_if_addrs, {})
    if_stats = optional_metric(psutil.net_if_stats, {})
    interfaces = []
    for iface, addr_list in addrs.items():
        ipv4 = next((a.address for a in addr_list if a.family == socket.AF_INET), "—")
        ipv6 = next((a.address for a in addr_list if a.family == socket.AF_INET6), "—")
        mac = next(
            (a.address for a in addr_list if a.family == psutil.AF_LINK),
            "—"
        )
        s = if_stats.get(iface)
        interfaces.append({
            "name": iface,
            "ipv4": ipv4,
            "ipv6": ipv6[:50] if ipv6 != "—" else "—",
            "mac": mac,
            "status": ("Attiva" if s.isup else "Inattiva") if s else "—",
            "speed": (f"{s.speed} Mbps" if s and s.speed else "N/A") if s else "N/A",
            "mtu": str(s.mtu) if s else "—",
        })

    with _proc_lock:
        processes = _proc_cache["processes"]
        proc_count = _proc_cache["proc_count"]
        total_threads = _proc_cache["total_threads"]

    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "hostname": _STATIC["hostname"],
            "os": _STATIC["os"],
            "arch": _STATIC["arch"],
            "boot_time": _STATIC["boot_time"],
            "uptime": get_uptime(),
            "user": _STATIC["user"],
        },
        "cpu": {
            "model": _STATIC["cpu_model"],
            "physical_cores": _STATIC["cpu_physical"],
            "logical_cores": _STATIC["cpu_logical"],
            "arch": _STATIC["cpu_arch"],
            "freq_current": f"{freq.current:.0f} MHz" if freq else "N/A",
            "freq_min": f"{freq.min:.0f} MHz" if freq else "N/A",
            "freq_max": f"{freq.max:.0f} MHz" if freq else "N/A",
            "total_percent": round(cpu_total, 1),
            "per_core": [round(p, 1) for p in per_core],
            "ctx_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "soft_interrupts": cpu_stats.soft_interrupts,
            "times_user": round(cpu_times.user, 1),
            "times_system": round(cpu_times.system, 1),
            "times_idle": round(cpu_times.idle, 1),
            "times_interrupt": round(getattr(cpu_times, "interrupt", 0), 1),
            "times_dpc": round(getattr(cpu_times, "dpc", 0), 1),
            "load_1": load[0],
            "load_5": load[1],
            "load_15": load[2],
            "process_count": proc_count,
            "thread_count": total_threads,
        },
        "memory": {
            "ram_total": bytes_to_human(ram.total),
            "ram_used": bytes_to_human(ram.used),
            "ram_free": bytes_to_human(ram.free),
            "ram_available": bytes_to_human(ram.available),
            "ram_percent": ram.percent,
            "swap_total": bytes_to_human(swap.total),
            "swap_used": bytes_to_human(swap.used),
            "swap_free": bytes_to_human(swap.free),
            "swap_percent": swap.percent,
            "swap_in": bytes_to_human(swap.sin),
            "swap_out": bytes_to_human(swap.sout),
        },
        "storage": {
            "read_speed": disk_r_speed,
            "write_speed": disk_w_speed,
            "read_total": bytes_to_human(dio.read_bytes) if dio else "N/A",
            "write_total": bytes_to_human(dio.write_bytes) if dio else "N/A",
            "partitions": partitions,
        },
        "network": {
            "upload_speed": net_up_speed,
            "download_speed": net_dn_speed,
            "sent_total": bytes_to_human(net.bytes_sent) if net else "N/A",
            "recv_total": bytes_to_human(net.bytes_recv) if net else "N/A",
            "packets_sent": net.packets_sent if net else 0,
            "packets_recv": net.packets_recv if net else 0,
            "err_in": net.errin if net else 0,
            "err_out": net.errout if net else 0,
            "drop_in": net.dropin if net else 0,
            "drop_out": net.dropout if net else 0,
            "interfaces": interfaces,
        },
        "processes": processes,
    }
