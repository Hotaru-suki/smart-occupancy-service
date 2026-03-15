import csv
import sys
import os
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check per-run resource CSV and decide whether to trigger breaker."
    )
    parser.add_argument(
        "--resource-file",
        required=True,
        help="Path to per-run resource csv, e.g. monitoring/polling_100_resources.csv",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Scenario label, e.g. polling_100",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to resource breaker summary csv",
    )
    parser.add_argument(
        "--max-system-cpu",
        type=float,
        default=85.0,
        help="Max allowed system CPU percent",
    )
    parser.add_argument(
        "--max-process-cpu",
        type=float,
        default=80.0,
        help="Max allowed process CPU percent",
    )
    parser.add_argument(
        "--max-process-mem-mb",
        type=float,
        default=1024.0,
        help="Max allowed process RSS memory in MB",
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=300,
        help="Max allowed process thread count",
    )
    return parser.parse_args()


def ensure_output_header(path: str) -> None:
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


def read_rows(resource_file: str) -> list[dict]:
    if not os.path.exists(resource_file):
        raise FileNotFoundError(f"resource file not found: {resource_file}")

    with open(resource_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def safe_float(row: dict, key: str) -> float:
    value = row.get(key, 0)
    if value is None or value == "":
        return 0.0
    return float(value)


def safe_int(row: dict, key: str) -> int:
    value = row.get(key, 0)
    if value is None or value == "":
        return 0
    return int(float(value))


def main():
    args = parse_args()
    ensure_output_header(args.output)

    try:
        rows = read_rows(args.resource_file)
    except FileNotFoundError as e:
        print(f"[RESOURCE_BREAKER] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[RESOURCE_BREAKER] failed to read resource file: {e}")
        sys.exit(1)

    if not rows:
        max_system_cpu = 0.0
        max_process_cpu = 0.0
        max_process_mem = 0.0
        max_threads = 0
        triggered = True
        reason = "empty_resource_file"
    else:
        try:
            max_system_cpu = max(safe_float(r, "system_cpu_percent") for r in rows)
            max_process_cpu = max(safe_float(r, "process_cpu_percent") for r in rows)
            max_process_mem = max(safe_float(r, "process_memory_rss_mb") for r in rows)
            max_threads = max(safe_int(r, "process_threads") for r in rows)
        except Exception as e:
            print(f"[RESOURCE_BREAKER] failed to parse resource rows: {e}")
            sys.exit(1)

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

    try:
        with open(args.output, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                args.label,
                round(max_system_cpu, 2),
                round(max_process_cpu, 2),
                round(max_process_mem, 2),
                max_threads,
                "YES" if triggered else "NO",
                reason,
            ])
    except PermissionError as e:
        print(f"[RESOURCE_BREAKER] permission denied when writing output: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[RESOURCE_BREAKER] failed to write output: {e}")
        sys.exit(1)

    print(f"[RESOURCE_BREAKER] label={args.label}")
    print(f"[RESOURCE_BREAKER] max_system_cpu={max_system_cpu}%")
    print(f"[RESOURCE_BREAKER] max_process_cpu={max_process_cpu}%")
    print(f"[RESOURCE_BREAKER] max_process_memory={max_process_mem}MB")
    print(f"[RESOURCE_BREAKER] max_threads={max_threads}")
    print(f"[RESOURCE_BREAKER] triggered={'YES' if triggered else 'NO'}, reason={reason}")

    sys.exit(2 if triggered else 0)


if __name__ == "__main__":
    main()