import csv
import sys
import os
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Check resource summary and decide whether to trigger breaker.")
    parser.add_argument("--summary", required=True, help="Path to monitor_summary.csv")
    parser.add_argument("--label", required=True, help="Scenario label, e.g. status_400")
    parser.add_argument("--output", required=True, help="Path to resource breaker summary csv")
    parser.add_argument("--max-system-cpu", type=float, default=85.0, help="Max allowed system CPU percent")
    parser.add_argument("--max-process-cpu", type=float, default=80.0, help="Max allowed process CPU percent")
    parser.add_argument("--max-process-mem-mb", type=float, default=1024.0, help="Max allowed process RSS memory in MB")
    parser.add_argument("--max-threads", type=int, default=300, help="Max allowed process thread count")
    return parser.parse_args()


def ensure_output_header(path: str):
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "label",
                "max_system_cpu_percent",
                "max_process_cpu_percent",
                "max_process_memory_rss_mb",
                "max_process_threads",
                "breaker_triggered",
                "reason",
            ])


def find_label_row(summary_path: str, label: str):
    with open(summary_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("label", "")).strip() == label:
                return row
    return None


def main():
    args = parse_args()

    ensure_output_header(args.output)

    row = find_label_row(args.summary, args.label)

    if row is None:
        triggered = True
        reason = "label_not_found_in_monitor_summary"
        max_system_cpu = 0.0
        max_process_cpu = 0.0
        max_process_mem = 0.0
        max_threads = 0
    else:
        max_system_cpu = float(row.get("max_system_cpu_percent", 0) or 0)
        max_process_cpu = float(row.get("max_process_cpu_percent", 0) or 0)
        max_process_mem = float(row.get("max_process_memory_rss_mb", 0) or 0)
        max_threads = int(float(row.get("max_process_threads", 0) or 0))

        triggered = False
        reasons = []

        if max_system_cpu >= args.max_system_cpu:
            triggered = True
            reasons.append(f"system_cpu>={args.max_system_cpu}")

        if max_process_cpu >= args.max_process_cpu:
            triggered = True
            reasons.append(f"process_cpu>={args.max_process_cpu}")

        if max_process_mem >= args.max_process_mem_mb:
            triggered = True
            reasons.append(f"process_mem>={args.max_process_mem_mb}MB")

        if max_threads >= args.max_threads:
            triggered = True
            reasons.append(f"threads>={args.max_threads}")

        reason = ";".join(reasons) if reasons else "ok"

    with open(args.output, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            args.label,
            max_system_cpu,
            max_process_cpu,
            max_process_mem,
            max_threads,
            "YES" if triggered else "NO",
            reason,
        ])

    print(f"[RESOURCE_BREAKER] label={args.label}")
    print(f"[RESOURCE_BREAKER] max_system_cpu={max_system_cpu}%")
    print(f"[RESOURCE_BREAKER] max_process_cpu={max_process_cpu}%")
    print(f"[RESOURCE_BREAKER] max_process_memory={max_process_mem}MB")
    print(f"[RESOURCE_BREAKER] max_threads={max_threads}")
    print(f"[RESOURCE_BREAKER] triggered={'YES' if triggered else 'NO'}, reason={reason}")

    sys.exit(2 if triggered else 0)


if __name__ == "__main__":
    main()