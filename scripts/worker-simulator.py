"""
AICluster Worker Simulator — Integration Testing Tool

Simulates 4 worker nodes (HP-01 through HP-04) with realistic resource metrics.
Provides a live TUI control panel and automated validation scenarios.

Usage:
    python worker-simulator.py
"""

import asyncio
import httpx
import random
import time
import json
import sys
import os
from datetime import datetime
from typing import Optional
from threading import Thread, Event

try:
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.console import Console, Group
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
except ImportError:
    print("rich library required. Install: pip install rich")
    sys.exit(1)

MASTER_URL = os.environ.get("MASTER_URL", "http://localhost:8000")
HEARTBEAT_INTERVAL = 5
VALIDATION_JOBS_COUNT = 3

console = Console()


class SimulatedWorker:
    def __init__(self, name: str, ip: str, index: int):
        self.name = name
        self.ip = ip
        self.index = index
        self.id: Optional[str] = None
        self.status = "stopped"
        self.cpu = 0.0
        self.ram = 0.0
        self.disk = 0.0
        self.temperature = 0.0
        self.busy = False
        self.heartbeat_count = 0
        self.errors = 0
        self._running = Event()
        self._paused = Event()
        self._paused.set()

    def _randomize_metrics(self):
        self.cpu = round(random.uniform(5, 25), 1)
        self.ram = round(random.uniform(10, 35), 1)
        self.disk = round(random.uniform(20, 60), 1)
        self.temperature = round(random.uniform(35, 60), 1)
        self.busy = random.choice([True, False])

    async def register(self, client: httpx.AsyncClient) -> bool:
        try:
            resp = await client.post(
                f"{MASTER_URL}/api/v1/workers/register",
                json={"name": self.name, "hostname": self.name, "ip": self.ip},
                timeout=10,
            )
            if resp.status_code == 200:
                self.id = resp.json()["id"]
                self.status = "online"
                return True
            self.status = "registration_failed"
            return False
        except httpx.ConnectError:
            self.status = "master_unreachable"
            return False

    async def send_heartbeat(self, client: httpx.AsyncClient) -> bool:
        if not self.id:
            return False
        try:
            resp = await client.post(
                f"{MASTER_URL}/api/v1/workers/heartbeat",
                json={
                    "id": self.id,
                    "cpu": self.cpu,
                    "ram": self.ram,
                    "disk": self.disk,
                    "temperature": self.temperature,
                    "busy": self.busy,
                    "network_speed": round(random.uniform(100, 1000), 1),
                },
                timeout=10,
            )
            if resp.status_code == 200:
                self.heartbeat_count += 1
                self.status = "online"
                return True
            self.errors += 1
            self.status = "error"
            return False
        except httpx.ConnectError:
            self.errors += 1
            self.status = "master_unreachable"
            return False

    async def run(self, client: httpx.AsyncClient, log_callback):
        self._running.set()
        registered = await self.register(client)
        if registered:
            log_callback(f"{self.name} registered (id: {self.id[:8]}...)")
        else:
            log_callback(f"{self.name} registration FAILED (status: {self.status})")
            return

        while self._running.is_set():
            self._paused.wait()
            self._randomize_metrics()
            ok = await self.send_heartbeat(client)
            if ok:
                log_callback(
                    f"{self.name} heartbeat #{self.heartbeat_count} "
                    f"CPU={self.cpu}% RAM={self.ram}% {'BUSY' if self.busy else 'idle'}"
                )
            else:
                log_callback(f"{self.name} heartbeat FAILED (#{self.heartbeat_count})")
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    def start(self):
        self._running.set()
        self._paused.set()
        self.status = "starting"

    def stop(self):
        self._running.clear()
        self._paused.set()
        self.status = "stopped"

    def pause(self):
        self._paused.clear()
        self.status = "paused"

    def resume(self):
        self._paused.set()
        self.status = "online"

    def crash(self):
        self._running.clear()
        self._paused.set()
        self.id = None
        self.status = "offline"

    def restart(self):
        self._running.set()
        self._paused.set()
        self.id = None
        self.status = "starting"

    @property
    def is_running(self):
        return self._running.is_set()

    @property
    def is_paused(self):
        return not self._paused.is_set()


class Simulator:
    def __init__(self):
        self.workers = [
            SimulatedWorker("HP-01", "192.168.1.50", 0),
            SimulatedWorker("HP-02", "192.168.1.51", 1),
            SimulatedWorker("HP-03", "192.168.1.52", 2),
            SimulatedWorker("HP-04", "192.168.1.53", 3),
        ]
        self.events: list[str] = []
        self.selected = 0
        self.running = True
        self.validation_results: list[str] = []
        self._key_queue: list[str] = []

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[{ts}] {msg}")
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def get_worker(self) -> SimulatedWorker:
        return self.workers[self.selected]

    def _make_worker_card(self, w: SimulatedWorker, selected: bool) -> Panel:
        sel = " → " if selected else "   "
        status_colors = {
            "online": "green",
            "offline": "red",
            "paused": "yellow",
            "stopped": "dim",
            "error": "red",
            "starting": "blue",
            "registration_failed": "red",
            "master_unreachable": "red",
        }
        sc = status_colors.get(w.status, "white")
        content = (
            f"{sel}[bold]{w.name}[/]\n"
            f"[{sc}]{w.status.upper():>12}[/]\n"
            f"CPU: [bold]{w.cpu:>5.1f}%[/]\n"
            f"RAM: [bold]{w.ram:>5.1f}%[/]\n"
            f"DSK: [bold]{w.disk:>5.1f}%[/]\n"
            f"TMP: [bold]{w.temperature:>5.1f}°C[/]\n"
            f"{'[red]BUSY[/]' if w.busy else '[dim]idle[/]':>12}\n"
            f"HB: [bold]{w.heartbeat_count}[/] | Err: [bold]{w.errors}[/]\n"
            f"ID: {w.id[:12]+'...' if w.id else '--':>12}"
        )
        border = "blue" if selected else "gray50"
        return Panel(content, box=box.ROUNDED, border_style=border, padding=(1, 2))

    def render_status(self) -> Layout:
        layout = Layout()
        header = Panel(
            Align.center(
                "[bold blue]AICluster Worker Simulator[/]  |  "
                f"Master: [cyan]{MASTER_URL}[/]  |  "
                "[dim]Ctrl+Q: Quit  Space: Validate[/]"
            ),
            box=box.HORIZONTALS,
        )
        cards = Columns(
            [self._make_worker_card(w, i == self.selected) for i, w in enumerate(self.workers)],
            equal=True,
            padding=(0, 1),
        )
        stats_text = (
            f"Total Heartbeats: [bold]{sum(w.heartbeat_count for w in self.workers)}[/]  |  "
            f"Online: [green]{sum(1 for w in self.workers if w.status == 'online')}[/]  |  "
            f"Paused: [yellow]{sum(1 for w in self.workers if w.is_paused)}[/]  |  "
            f"Offline: [red]{sum(1 for w in self.workers if w.status in ('offline','stopped'))}[/]"
        )
        stats_panel = Panel(Align.center(stats_text), box=box.HORIZONTALS)

        events_content = "\n".join(self.events[-20:]) or "[dim]No events yet[/]"
        events_panel = Panel(
            events_content,
            title="Events",
            box=box.ROUNDED,
            height=14,
        )

        controls = (
            "[bold]Keys:[/]  "
            "[bold][1][/][2][/][3][/][4][/] Select Worker  |  "
            "[bold][S][/]tart  [bold][P][/]ause  [bold][R][/]esume  "
            "[bold][C][/]rash  [bold][K][/]ill  "
            "[bold][Space][/] Validate  [bold][Q][/]uit"
        )
        controls_panel = Panel(Align.center(controls), box=box.HORIZONTALS)

        layout.split_column(header, cards, stats_panel, events_panel, controls_panel)
        return layout

    def handle_key(self, key: str):
        key = key.lower()
        if key in "1234":
            idx = int(key) - 1
            if 0 <= idx < 4:
                self.selected = idx
                self.log(f"Selected {self.workers[idx].name}")
        elif key == "s":
            w = self.get_worker()
            if not w.is_running:
                w.start()
                self.log(f"{w.name} started")
        elif key == "p":
            w = self.get_worker()
            if w.is_running:
                w.pause()
                self.log(f"{w.name} paused")
        elif key == "r":
            w = self.get_worker()
            if w.is_running:
                w.resume()
                self.log(f"{w.name} resumed")
        elif key == "c":
            w = self.get_worker()
            w.crash()
            self.log(f"{w.name} crashed (offline)")
        elif key == "k":
            w = self.get_worker()
            w.stop()
            self.log(f"{w.name} killed")
        elif key == " ":
            self.log("=== Starting validation ===")
            asyncio.create_task(self.run_validation())
        elif key == "q":
            self.log("Shutting down...")
            self.running = False

    def _keyboard_listener(self):
        if sys.platform == "win32":
            import msvcrt
            while self.running:
                if msvcrt.kbhit():
                    k = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                    self._key_queue.append(k)
                time.sleep(0.05)
        else:
            import select
            while self.running:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    k = sys.stdin.read(1).lower()
                    self._key_queue.append(k)

    def _process_key_queue(self):
        while self._key_queue:
            self.handle_key(self._key_queue.pop(0))

    async def worker_runner(self):
        async with httpx.AsyncClient() as client:
            tasks = []
            for w in self.workers:
                tasks.append(asyncio.create_task(w.run(client, self.log)))
                await asyncio.sleep(0.2)
            await asyncio.gather(*tasks)

    async def run_validation(self):
        self.validation_results = []
        self.log("=" * 40)
        self.log("VALIDATION STARTED")

        async with httpx.AsyncClient() as client:
            await self._validate_health(client)
            await self._validate_dashboard(client)
            await self._validate_jobs(client)
            await self._validate_logs(client)
            await self._validate_worker_list(client)
            await self._validate_worker_timeout(client)
            await self._validate_websocket(client)

        self.log("VALIDATION COMPLETE")
        self.log("=" * 40)

    async def _validate_health(self, client: httpx.AsyncClient):
        try:
            resp = await client.get(f"{MASTER_URL}/api/v1/health", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"
            self.validation_results.append(("PASS", "Health Check", "API responds, DB connected"))
            self.log("  [VALIDATION] Health Check: PASS")
        except Exception as e:
            self.validation_results.append(("FAIL", "Health Check", str(e)))
            self.log(f"  [VALIDATION] Health Check: FAIL ({e})")

    async def _validate_dashboard(self, client: httpx.AsyncClient):
        try:
            resp = await client.get(f"{MASTER_URL}/api/v1/dashboard", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            online_workers = sum(1 for w in self.workers if w.status == "online")
            total = data["total_workers"]
            online = data["online"]
            self.validation_results.append(("PASS", "Dashboard", f"{total} workers, {online} online"))
            self.log(f"  [VALIDATION] Dashboard: PASS ({total} workers, {online} online)")
        except Exception as e:
            self.validation_results.append(("FAIL", "Dashboard", str(e)))
            self.log(f"  [VALIDATION] Dashboard: FAIL ({e})")

    async def _validate_jobs(self, client: httpx.AsyncClient):
        try:
            job_ids = []
            for i in range(VALIDATION_JOBS_COUNT):
                resp = await client.post(
                    f"{MASTER_URL}/api/v1/jobs",
                    json={"type": f"test-job-{i+1}", "payload": {"sim": True}, "priority": i + 1},
                    timeout=10,
                )
                assert resp.status_code == 200
                jid = resp.json()["id"]
                job_ids.append(jid)
                self.log(f"  Created job {jid[:8]}... (type: test-job-{i+1})")

            list_resp = await client.get(f"{MASTER_URL}/api/v1/jobs", timeout=10)
            assert list_resp.status_code == 200
            jobs = list_resp.json()
            assert len(jobs) >= VALIDATION_JOBS_COUNT
            self.validation_results.append(
                ("PASS", "Jobs", f"Created {VALIDATION_JOBS_COUNT} jobs, list returns {len(jobs)}")
            )
            self.log(f"  [VALIDATION] Jobs: PASS ({len(jobs)} jobs in queue)")

            if job_ids:
                cancel_resp = await client.delete(
                    f"{MASTER_URL}/api/v1/jobs/{job_ids[0]}", timeout=10
                )
                assert cancel_resp.status_code == 200
                self.validation_results.append(("PASS", "Job Cancel", f"Job {job_ids[0][:8]}... cancelled"))
                self.log(f"  [VALIDATION] Job Cancel: PASS")
        except Exception as e:
            self.validation_results.append(("FAIL", "Jobs", str(e)))
            self.log(f"  [VALIDATION] Jobs: FAIL ({e})")

    async def _validate_logs(self, client: httpx.AsyncClient):
        try:
            resp = await client.get(f"{MASTER_URL}/api/v1/logs", timeout=10)
            assert resp.status_code == 200
            logs = resp.json()
            assert isinstance(logs, list)
            self.validation_results.append(("PASS", "Logs", f"{len(logs)} log entries found"))
            self.log(f"  [VALIDATION] Logs: PASS ({len(logs)} entries)")
        except Exception as e:
            self.validation_results.append(("FAIL", "Logs", str(e)))
            self.log(f"  [VALIDATION] Logs: FAIL ({e})")

    async def _validate_worker_list(self, client: httpx.AsyncClient):
        try:
            resp = await client.get(f"{MASTER_URL}/api/v1/workers", timeout=10)
            assert resp.status_code == 200
            workers = resp.json()
            names = [w["worker_name"] for w in workers]
            for expected in ["HP-01", "HP-02", "HP-03", "HP-04"]:
                assert expected in names, f"{expected} not in worker list"
            self.validation_results.append(
                ("PASS", "Worker List", f"All 4 workers registered: {', '.join(names)}")
            )
            self.log(f"  [VALIDATION] Worker List: PASS ({len(workers)} workers)")
        except Exception as e:
            self.validation_results.append(("FAIL", "Worker List", str(e)))
            self.log(f"  [VALIDATION] Worker List: FAIL ({e})")

    async def _validate_worker_timeout(self, client: httpx.AsyncClient):
        self.log("  [VALIDATION] Testing worker timeout (HP-01 will go offline)...")
        w = self.workers[0]
        if w.is_running:
            w.crash()
            self.log("  HP-01 crashed for timeout test")
            await asyncio.sleep(20)
            try:
                resp = await client.get(f"{MASTER_URL}/api/v1/workers?timeout_test", timeout=10)
                assert resp.status_code == 200
                workers = resp.json()
                hp01 = next((x for x in workers if x["worker_name"] == "HP-01"), None)
                if hp01 and hp01["status"] == "offline":
                    self.validation_results.append(("PASS", "Worker Timeout", "HP-01 correctly marked offline"))
                    self.log("  [VALIDATION] Worker Timeout: PASS")
                else:
                    status = hp01["status"] if hp01 else "not found"
                    self.validation_results.append(("FAIL", "Worker Timeout", f"HP-01 status is {status}"))
                    self.log(f"  [VALIDATION] Worker Timeout: FAIL (status={status})")
            except Exception as e:
                self.validation_results.append(("FAIL", "Worker Timeout", str(e)))
                self.log(f"  [VALIDATION] Worker Timeout: FAIL ({e})")

    async def _validate_websocket(self, client: httpx.AsyncClient):
        self.log("  [VALIDATION] Testing WebSocket connection...")
        try:
            import websockets
            async with websockets.connect(
                f"{MASTER_URL.replace('http', 'ws')}/ws", ping_interval=None
            ) as ws:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(msg)
                self.validation_results.append(
                    ("PASS", "WebSocket", f"Received message type: {data.get('type', 'unknown')}")
                )
                self.log(f"  [VALIDATION] WebSocket: PASS")
        except ImportError:
            self.validation_results.append(("SKIP", "WebSocket", "websockets library not installed"))
            self.log("  [VALIDATION] WebSocket: SKIP (websockets library required)")
        except Exception as e:
            self.validation_results.append(("FAIL", "WebSocket", str(e)))
            self.log(f"  [VALIDATION] WebSocket: FAIL ({e})")

    def generate_report(self):
        report = []
        report.append("=" * 60)
        report.append("  AICluster Worker Simulator — Validation Report")
        report.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"  Master URL: {MASTER_URL}")
        report.append("=" * 60)
        report.append("")

        passed = sum(1 for r in self.validation_results if r[0] == "PASS")
        failed = sum(1 for r in self.validation_results if r[0] == "FAIL")
        skipped = sum(1 for r in self.validation_results if r[0] == "SKIP")
        total = len(self.validation_results)

        report.append(f"  Results: [green]{passed} PASS[/]  [red]{failed} FAIL[/]  [yellow]{skipped} SKIP[/]  / {total} total")
        report.append("")
        report.append("-" * 60)
        report.append(f"  {'RESULT':<8} {'TEST':<20} {'DETAILS':<30}")
        report.append("-" * 60)
        for result, test, detail in self.validation_results:
            icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "—"}.get(result, "?")
            report.append(f"  [{result[0]}]{icon} {result:<6}[/] {test:<20} {detail:<30}")

        report.append("")
        report.append("-" * 60)
        report.append("  Worker Statistics:")
        report.append("-" * 60)
        for w in self.workers:
            report.append(
                f"  {w.name:<8} | Status: {w.status:<12} | "
                f"HB: {w.heartbeat_count:<4} | Errors: {w.errors:<3} | "
                f"Last: CPU={w.cpu:>5.1f}% RAM={w.ram:>5.1f}%"
            )

        report.append("")
        report.append("-" * 60)
        overall = "PASS" if failed == 0 else "FAIL"
        report.append(f"  OVERALL: [{'green' if overall == 'PASS' else 'red'}]{overall}[/]")
        report.append("=" * 60)

        return "\n".join(report)

    async def run(self):
        thread = Thread(target=self._keyboard_listener, daemon=True)
        thread.start()

        with Live(self.render_status(), refresh_per_second=4, screen=True) as live:
            worker_task = asyncio.create_task(self.worker_runner())
            try:
                while self.running:
                    self._process_key_queue()
                    live.update(self.render_status())
                    await asyncio.sleep(0.25)
            finally:
                for w in self.workers:
                    w.stop()
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass

        report = self.generate_report()
        console.clear()
        console.print(report)

        with open("simulator-report.txt", "w", encoding="utf-8") as f:
            f.write(report.replace("[green]", "").replace("[/]", "")
                    .replace("[red]", "").replace("[yellow]", ""))
        console.print(f"\nReport saved to: [bold]simulator-report.txt[/]")


def main():
    console.clear()
    console.print("[bold blue]AICluster Worker Simulator[/]")
    console.print(f"Master URL: [cyan]{MASTER_URL}[/]")
    console.print("Make sure the master server is running.")
    console.print("")
    console.print("[dim]Starting in 2 seconds... Press Ctrl+C to abort.[/]")
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        console.print("[red]Aborted.[/]")
        sys.exit(0)

    sim = Simulator()
    try:
        asyncio.run(sim.run())
    except KeyboardInterrupt:
        sim.running = False


if __name__ == "__main__":
    main()
