import csv
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Check JMeter JTL and decide whether to trigger breaker.")
    parser.add_argument("--jtl", required=True, help="Path to JTL file")
    parser.add_argument("--label", required=True, help="Scenario label")
    parser.add_argument("--summary", required=True, help="Path to breaker summary csv")
    parser.add_argument("--max-error-rate", type=float, default=5.0, help="Percent, default 5")
    parser.add_argument("--max-p95-ms", type=float, default=2000.0, help="Milliseconds, default 2000")
    parser.add_argument("--min-samples", type=int, default=20, help="Minimum samples required")
    return parser.parse_args()


def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    idx = (len(sorted_values) - 1) * p
    lower = int(idx)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = idx - lower
    return float(sorted_values[lower]) * (1 - weight) + float(sorted_values[upper]) * weight


def ensure_summary_header(path):
    import os
    if not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "label",
                "samples",
                "error_rate_percent",
                "avg_ms",
                "p95_ms",
                "breaker_triggered",
                "reason",
            ])


def main():
    args = parse_args()

    elapsed_values = []
    success_count = 0
    total_count = 0

    with open(args.jtl, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_count += 1
            try:
                elapsed = float(row.get("elapsed", 0))
            except ValueError:
                elapsed = 0.0
            elapsed_values.append(elapsed)

            success_raw = str(row.get("success", "")).strip().lower()
            if success_raw == "true":
                success_count += 1

    if total_count == 0:
        error_rate = 100.0
        avg_ms = 0.0
        p95_ms = 0.0
        triggered = True
        reason = "empty_jtl"
    else:
        elapsed_values.sort()
        avg_ms = round(sum(elapsed_values) / total_count, 2)
        p95_ms = round(percentile(elapsed_values, 0.95), 2)
        error_rate = round((total_count - success_count) * 100.0 / total_count, 2)

        triggered = False
        reasons = []

        if total_count < args.min_samples:
            triggered = True
            reasons.append("too_few_samples")

        if error_rate >= args.max_error_rate:
            triggered = True
            reasons.append(f"error_rate>={args.max_error_rate}")

        if p95_ms >= args.max_p95_ms:
            triggered = True
            reasons.append(f"p95>={args.max_p95_ms}ms")

        reason = ";".join(reasons) if reasons else "ok"

    ensure_summary_header(args.summary)
    with open(args.summary, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            args.label,
            total_count,
            error_rate,
            avg_ms,
            p95_ms,
            "YES" if triggered else "NO",
            reason,
        ])

    print(f"[BREAKER] label={args.label}")
    print(f"[BREAKER] samples={total_count}, error_rate={error_rate}%, avg={avg_ms}ms, p95={p95_ms}ms")
    print(f"[BREAKER] triggered={'YES' if triggered else 'NO'}, reason={reason}")

    sys.exit(2 if triggered else 0)


if __name__ == "__main__":
    main()