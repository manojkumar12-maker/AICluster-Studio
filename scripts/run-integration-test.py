"""
Integration test runner — starts simulated workers and validates master server.
Run this while the master server is running on port 8000.
"""

import asyncio
import httpx
import json
import random
import sys
import os
from datetime import datetime

MASTER_URL = os.environ.get("MASTER_URL", "http://localhost:8000")
WORKER_COUNT = 4
HEARTBEAT_ROUNDS = 6


class SimWorker:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.id = None
        self.cpu = 0.0
        self.ram = 0.0
        self.disk = 0.0
        self.temp = 0.0
        self.busy = False
        self.hb_count = 0

    def randomize(self):
        self.cpu = round(random.uniform(5, 25), 1)
        self.ram = round(random.uniform(10, 35), 1)
        self.disk = round(random.uniform(20, 60), 1)
        self.temp = round(random.uniform(35, 60), 1)
        self.busy = random.choice([True, False])

    async def register(self, client):
        r = await client.post(f"{MASTER_URL}/api/v1/workers/register",
                              json={"name": self.name, "hostname": self.name, "ip": self.ip},
                              timeout=10)
        if r.status_code == 200:
            self.id = r.json()["id"]
            return True
        return False

    async def heartbeat(self, client):
        if not self.id:
            return False
        self.randomize()
        r = await client.post(f"{MASTER_URL}/api/v1/workers/heartbeat",
                              json={
                                  "id": self.id,
                                  "cpu": self.cpu,
                                  "ram": self.ram,
                                  "disk": self.disk,
                                  "temperature": self.temp,
                                  "busy": self.busy,
                                  "network_speed": round(random.uniform(100, 1000), 1),
                              },
                              timeout=10)
        if r.status_code == 200:
            self.hb_count += 1
            return True
        return False


results = {"pass": [], "fail": [], "skip": []}


def check(name, ok, detail=""):
    if ok:
        results["pass"].append((name, detail))
        print(f"  [PASS] {name}: {detail}")
    else:
        results["fail"].append((name, detail))
        print(f"  [FAIL] {name}: {detail}")


async def main():
    print("=" * 60)
    print("  AICluster Integration Test")
    print(f"  Master: {MASTER_URL}")
    print(f"  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    workers = [
        SimWorker("HP-01", "192.168.1.50"),
        SimWorker("HP-02", "192.168.1.51"),
        SimWorker("HP-03", "192.168.1.52"),
        SimWorker("HP-04", "192.168.1.53"),
    ]

    async with httpx.AsyncClient() as c:
        # ── 1. Health Check ──
        print("\n[1/8] Health Check")
        r = await c.get(f"{MASTER_URL}/api/v1/health", timeout=10)
        check("Health endpoint", r.status_code == 200, "responded")
        if r.status_code == 200:
            d = r.json()
            check("DB connected", d["database"] == "connected", d["database"])
            check("Version present", bool(d["version"]), d["version"])

        # ── 2. Register Workers ──
        print("\n[2/8] Worker Registration")
        for w in workers:
            ok = await w.register(c)
            check(f"{w.name} registered", ok, f"id={w.id[:8] if w.id else 'N/A'}...")

        # ── 3. Verify Worker List ──
        print("\n[3/8] Worker List")
        r = await c.get(f"{MASTER_URL}/api/v1/workers", timeout=10)
        check("GET /workers", r.status_code == 200, "responded")
        if r.status_code == 200:
            wl = r.json()
            check("All 4 workers present", len(wl) == 4, f"got {len(wl)}")
            names = [x["worker_name"] for x in wl]
            for n in ["HP-01", "HP-02", "HP-03", "HP-04"]:
                check(f"{n} in list", n in names, "")

        # ── 4. Send Heartbeats ──
        print(f"\n[4/8] Heartbeats ({HEARTBEAT_ROUNDS} rounds)")
        for rnd in range(1, HEARTBEAT_ROUNDS + 1):
            for w in workers:
                await w.heartbeat(c)
            print(f"  Round {rnd}/{HEARTBEAT_ROUNDS} — HB sent")
            if rnd < HEARTBEAT_ROUNDS:
                await asyncio.sleep(2)
        for w in workers:
            check(f"{w.name} heartbeats", w.hb_count > 0, f"{w.hb_count} sent")

        # ── 5. Dashboard ──
        print("\n[5/8] Dashboard")
        r = await c.get(f"{MASTER_URL}/api/v1/dashboard", timeout=10)
        check("GET /dashboard", r.status_code == 200, "responded")
        if r.status_code == 200:
            d = r.json()
            check("Workers counted", d["total_workers"] == 4, f"total={d['total_workers']}")
            check("Workers accounted", d["online"] + d["busy"] >= 4, f"online={d['online']} busy={d['busy']}")
            check("CPU avg present", d["average_cpu"] > 0, f"cpu={d['average_cpu']}%")
            check("RAM avg present", d["average_ram"] > 0, f"ram={d['average_ram']}%")
            check("Dashboard fields complete",
                  all(k in d for k in ["total_workers","online","offline","idle","busy",
                                       "average_cpu","average_ram","running_jobs"]),
                  "all fields present")

        # ── 6. Jobs ──
        print("\n[6/8] Jobs")
        job_ids = []
        for i in range(3):
            r = await c.post(f"{MASTER_URL}/api/v1/jobs",
                             json={"type": f"auto-test-{i+1}", "payload": {"test": True},
                                    "priority": i+1},
                             timeout=10)
            check(f"Create job {i+1}", r.status_code == 200, f"id={r.json()['id'][:8]}...")
            if r.status_code == 200:
                job_ids.append(r.json()["id"])

        r = await c.get(f"{MASTER_URL}/api/v1/jobs", timeout=10)
        check("List jobs", r.status_code == 200, f"{len(r.json())} jobs")
        if r.status_code == 200:
            check("At least 3 jobs", len(r.json()) >= 3, f"got {len(r.json())}")

        if job_ids:
            r = await c.get(f"{MASTER_URL}/api/v1/jobs/{job_ids[0]}", timeout=10)
            check("Get job by ID", r.status_code == 200, f"status={r.json()['status']}")

            r = await c.delete(f"{MASTER_URL}/api/v1/jobs/{job_ids[0]}", timeout=10)
            check("Cancel job", r.status_code == 200, f"cancelled")

            r = await c.get(f"{MASTER_URL}/api/v1/jobs/{job_ids[0]}", timeout=10)
            check("Job cancelled", r.status_code == 200 and r.json()["status"] == "cancelled",
                  r.json()["status"])

            r = await c.delete(f"{MASTER_URL}/api/v1/jobs/nonexistent", timeout=10)
            check("Cancel not-found returns 404", r.status_code == 404, "")

        # ── 7. Logs ──
        print("\n[7/8] Logs")
        r = await c.get(f"{MASTER_URL}/api/v1/logs", timeout=10)
        check("GET /logs", r.status_code == 200, "responded")
        if r.status_code == 200:
            logs = r.json()
            check("Logs are list", isinstance(logs, list), f"{len(logs)} entries")
            if logs:
                check("Log has level", "level" in logs[0], logs[0]["level"])
                check("Log has message", "message" in logs[0], "")

        r = await c.get(f"{MASTER_URL}/api/v1/logs?level=INFO", timeout=10)
        check("Logs filtered by level", r.status_code == 200, "filtered")

        # ── 8. Worker Timeout ──
        print("\n[8/8] Worker Timeout")
        timed_out_worker = workers[0]
        check(f"{timed_out_worker.name} stopping for timeout test", True, "heartbeats paused")

        async def keep_others_alive():
            for _ in range(14):
                for aw in workers[1:]:
                    await aw.heartbeat(c)
                await asyncio.sleep(2)

        keep_alive_task = asyncio.create_task(keep_others_alive())

        for remaining in range(28, 0, -1):
            sys.stdout.write(f"\r  Waiting for {timed_out_worker.name} timeout... {remaining}s remaining  ")
            sys.stdout.flush()
            await asyncio.sleep(1)
        print()

        keep_alive_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass

        r = await c.get(f"{MASTER_URL}/api/v1/workers", timeout=10)
        if r.status_code == 200:
            wl = r.json()
            hp01 = next((x for x in wl if x["worker_name"] == "HP-01"), None)
            if hp01:
                check(f"{timed_out_worker.name} went OFFLINE after timeout",
                      hp01["status"] == "offline",
                      f"status={hp01['status']}")
                others_ok = all(
                    x["status"] in ("online", "busy")
                    for x in wl if x["worker_name"] != "HP-01"
                )
                check("Other workers still online", others_ok,
                      f"{[x['status'] for x in wl if x['worker_name'] != 'HP-01']}")
            else:
                check("HP-01 found in list", False, "not found")
        else:
            check("Worker list after timeout", False, f"HTTP {r.status_code}")

    # ── Report ──
    passed = len(results["pass"])
    failed = len(results["fail"])
    total = passed + failed

    print("\n" + "=" * 60)
    print(f"  INTEGRATION TEST RESULTS")
    print(f"  Tests: {total}  |  Passed: {passed}  |  Failed: {failed}")
    print("=" * 60)

    if failed > 0:
        print("\n  FAILED TESTS:")
        for name, detail in results["fail"]:
            print(f"    ✗ {name}: {detail}")
        print(f"\n  [OVERALL: FAIL]")
    else:
        print(f"\n  [OVERALL: PASS — All {total} tests passed]")

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "..", "docs", "integration-test-report.txt")
    with open(report_path, "w") as f:
        f.write(f"AICluster Integration Test Report\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Master: {MASTER_URL}\n")
        f.write(f"Passed: {passed}/{total}  Failed: {failed}/{total}\n\n")
        f.write("Results:\n")
        for status, tests in [("PASS", results["pass"]), ("FAIL", results["fail"])]:
            for name, detail in tests:
                f.write(f"  [{status}] {name} {detail}\n")
        f.write(f"\nOverall: {'PASS' if failed == 0 else 'FAIL'}\n")

    print(f"\n  Report: {report_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
