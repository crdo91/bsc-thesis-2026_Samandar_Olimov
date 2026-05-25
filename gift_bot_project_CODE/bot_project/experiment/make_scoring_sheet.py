"""
Helper to score the experiment results manually.

Reads experiment/results.json and creates an empty scoring sheet
experiment/scoring_sheet.csv. You then open this CSV in Excel or
Google Sheets and fill the scores: relevance, creativity, specificity,
hallucination (yes/no for each idea).

Usage:
    python -m experiment.make_scoring_sheet
"""

import csv
import json
from pathlib import Path

RESULTS_JSON = Path("experiment/results.json")
SHEET_CSV = Path("experiment/scoring_sheet.csv")


def main() -> None:
    results = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    with SHEET_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "persona_id", "strategy", "elapsed_seconds",
            "relevance_1_5", "creativity_1_5", "specificity_1_5",
            "hallucination_count_0_3", "notes", "answer_preview"
        ])
        for r in results:
            preview = (r["answer"] or "")[:200].replace("\n", " ")
            writer.writerow([
                r["persona_id"], r["strategy"], r["elapsed_seconds"],
                "", "", "", "", "", preview
            ])
    print(f"Empty scoring sheet saved to {SHEET_CSV}")
    print("Open it in Excel, score every row, then save.")


if __name__ == "__main__":
    main()
