import csv
import os
import time
import argparse
from datetime import datetime

import psutil


def bytes_to_mb(value: float) -> float:
    return round(value / 1024 / 1024, 2)


def ensure_parent_dir(file_path: str) -> None:
    parent = os.path.dirname(os.path.abspath(file_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def find_processes_by_keyword(keyword: str):
    matched = []
    keyword = keyword.lower()

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            cmdline_list = proc.info["cmdline"] or []
            cmdline = " ".join(cmdline_list).lower()

            if keyword in name or keyword in cmdline:
                matched.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return matched


def collect_system_metrics():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return {
        "system_cpu_percent": psutil.cpu_percent(interval=None),
        "system_memory_percent": vm.percent,
        "system_memory_used_mb": bytes_to_mb(vm.used),
        "system_memory_total_mb": bytes_to_mb(vm.total),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
        "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
    }


def collect_process_metrics(processes):
    total_cpu = 0.0
    total_rss_mb = 0.0
    total_threads = 0
    pids = []
    alive_count = 0

    for proc in processes:
        try:
            cpu = proc.cpu_percent(interval=None)
            mem = proc.memory_info().rss
            threads = proc.num_threads()

            total_cpu += cpu
            total_rss_mb += bytes_to_mb(mem)
            total_threads += threads
            pids.append(str(proc.pid))
            alive_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return {
        "process_count": alive_count,
        "process_pids": ",".join(pids),
        "process_cpu_percent": round(total_cpu, 2),
        "process_memory_rss_mb": round(total_rss_mb, 2),
        "process_threads": total_threads,
    }


def append_summary(summary_output: str, label: str, samples: list):
    if not summary_output or not samples:
        return

    ensure_parent_dir(summary_output)
    file_exists = os.path.exists(summary_output)

    avg_sys_cpu = round(sum(float(x["system_cpu_percent"]) for x in samples) / len(samples), 2)
    max_sys_cpu = round(max(float(x["system_cpu_percent"]) for x in samples), 2)
    avg_proc_cpu = round(sum(float(x["process_cpu_percent"]) for x in samples) / len(samples), 2)
    max_proc_cpu = round(max(float(x["process_cpu_percent"]) for x in samples), 2)
    avg_proc_mem = round(sum(float(x["process_memory_rss_mb"]) for x in samples) / len(samples), 2)
    max_proc_mem = round(max(float(x["process_memory_rss_mb"]) for x in samples), 2)
    max_threads = max(int(x["process_threads"]) for x in samples)
    max_proc_count = max(int(x["process_count"]) for x in samples)

    headers = [
        "label",
        "sample_count",
        "avg_system_cpu_percent",
        "max_system_cpu_percent",
        "avg_process_cpu_percent",
        "max_process_cpu_percent",
        "avg_process_memory_rss_mb",
        "max_process_memory_rss_mb",
        "max_process_threads",
        "max_process_count",
    ]

    row = {
        "label": label,
        "sample_count": len(samples),
        "avg_system_cpu_percent": avg_sys_cpu,
        "max_system_cpu_percent": max_sys_cpu,
        "avg_process_cpu_percent": avg_proc_cpu,
        "max_process_cpu_percent": max_proc_cpu,
        "avg_process_memory_rss_mb": avg_proc_mem,
        "max_process_memory_rss_mb": max_proc_mem,
        "max_process_threads": max_threads,
        "max_process_count": max_proc_count,
    }

    with open(summary_output, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Monitor system and process resources.")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--keyword", type=str, default="uvicorn")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--label", type=str, default="default")
    parser.add_argument("--summary-output", type=str, default="")
    parser.add_argument("--stop-flag", type=str, default="monitor.stop")

    args = parser.parse_args()

    ensure_parent_dir(args.output)
    ensure_parent_dir(args.stop_flag)

    headers = [
        "timestamp",
        "label",
        "system_cpu_percent",
        "system_memory_percent",
        "system_memory_used_mb",
        "system_memory_total_mb",
        "disk_percent",
        "disk_used_gb",
        "disk_total_gb",
        "process_count",
        "process_pids",
        "process_cpu_percent",
        "process_memory_rss_mb",
        "process_threads",
    ]

    samples = []

    if os.path.exists(args.stop_flag):
        os.remove(args.stop_flag)

    psutil.cpu_percent(interval=None)
    for proc in find_processes_by_keyword(args.keyword):
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    start_time = time.time()

    with open(args.output, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            system_metrics = collect_system_metrics()
            processes = find_processes_by_keyword(args.keyword)
            process_metrics = collect_process_metrics(processes)

            row = {
                "timestamp": now,
                "label": args.label,
                **system_metrics,
                **process_metrics,
            }

            samples.append(row)
            writer.writerow(row)
            f.flush()

            if os.path.exists(args.stop_flag):
                break

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break

            time.sleep(args.interval)

    append_summary(args.summary_output, args.label, samples)


if __name__ == "__main__":
    main()