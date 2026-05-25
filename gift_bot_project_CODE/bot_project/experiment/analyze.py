"""
Read the filled scoring_sheet.csv and produce a summary table.

Usage:
    python -m experiment.analyze
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

SHEET_CSV = Path("experiment/scoring_sheet.csv")
SUMMARY_CSV = Path("experiment/summary.csv")
STRATEGIES = ["naive", "constrained", "cot", "persona"]


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def main() -> None:
    by_strategy: dict[str, dict[str, list[float]]] = {
        s: defaultdict(list) for s in STRATEGIES
    }

    with SHEET_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = row["strategy"]
            if s not in by_strategy:
                continue
            for metric in ["relevance_1_5", "creativity_1_5", "specificity_1_5",
                           "hallucination_count_0_3", "elapsed_seconds"]:
                val = _to_float(row.get(metric, ""))
                if val is not None:
                    by_strategy[s][metric].append(val)

    print(f"{'Strategy':<12} {'Rel':>6} {'Cre':>6} {'Spec':>6} {'Halluc%':>8} {'Time(s)':>8}")
    print("-" * 50)

    summary_rows = []
    for s in STRATEGIES:
        m = by_strategy[s]
        rel = statistics.mean(m["relevance_1_5"]) if m["relevance_1_5"] else 0
        cre = statistics.mean(m["creativity_1_5"]) if m["creativity_1_5"] else 0
        spec = statistics.mean(m["specificity_1_5"]) if m["specificity_1_5"] else 0
        halluc_pct = (
            100 * sum(m["hallucination_count_0_3"]) / (3 * len(m["hallucination_count_0_3"]))
            if m["hallucination_count_0_3"] else 0
        )
        elapsed = statistics.mean(m["elapsed_seconds"]) if m["elapsed_seconds"] else 0
        print(f"{s:<12} {rel:>6.2f} {cre:>6.2f} {spec:>6.2f} {halluc_pct:>7.1f}% {elapsed:>8.2f}")
        summary_rows.append({
            "strategy": s,
            "relevance": round(rel, 2),
            "creativity": round(cre, 2),
            "specificity": round(spec, 2),
            "hallucination_pct": round(halluc_pct, 1),
            "avg_time_s": round(elapsed, 2),
        })

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nSummary saved to {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
