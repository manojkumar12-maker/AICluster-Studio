import psutil
import platform
from typing import Optional


class SystemMonitor:
    @staticmethod
    def get_cpu_percent() -> float:
        return psutil.cpu_percent(interval=0.5)

    @staticmethod
    def get_ram_info() -> tuple[float, float]:
        mem = psutil.virtual_memory()
        return mem.total / (1024**3), mem.used / (1024**3)

    @staticmethod
    def get_disk_info() -> tuple[float, float]:
        disk = psutil.disk_usage("/")
        return disk.total / (1024**3), disk.used / (1024**3)

    @staticmethod
    def get_temperature() -> Optional[float]:
        try:
            if platform.system() == "Linux":
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
        except Exception:
            pass
        return None

    @staticmethod
    def get_network_io() -> tuple[int, int]:
        net = psutil.net_io_counters()
        return net.bytes_recv, net.bytes_sent

    @staticmethod
    def get_uptime() -> float:
        import time
        return time.time() - psutil.boot_time()

    @staticmethod
    def get_system_info() -> dict:
        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "python_version": platform.python_version(),
        }

    def collect_all(self) -> dict:
        ram_total, ram_used = self.get_ram_info()
        disk_total, disk_used = self.get_disk_info()
        network_rx, network_tx = self.get_network_io()

        return {
            "cpu_percent": self.get_cpu_percent(),
            "ram_total": ram_total,
            "ram_used": ram_used,
            "disk_total": disk_total,
            "disk_used": disk_used,
            "temperature": self.get_temperature(),
            "network_rx": network_rx,
            "network_tx": network_tx,
            "uptime": self.get_uptime(),
        }
