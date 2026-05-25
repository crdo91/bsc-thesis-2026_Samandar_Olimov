"""
Experiment runner.

Runs all 4 prompt strategies on all 30 synthetic personas.
Saves the results to experiment/results.json and experiment/results.csv.

Usage:
    python -m experiment.run_experiment
"""

import asyncio
import csv
import json
import time
from pathlib import Path

from grok_client import call_grok
from prompts.builder import build_prompt, STRATEGIES

PERSONAS_PATH = Path("experiment/personas.json")
RESULTS_JSON = Path("experiment/results.json")
RESULTS_CSV = Path("experiment/results.csv")

# Pause between API calls (seconds) - be nice to the API
PAUSE = 1.0


async def run_one(persona: dict, strategy: str) -> dict:
    prompt = build_prompt(strategy, persona)
    t0 = time.time()
    try:
        answer = await call_grok(prompt)
        error = ""
    except Exception as exc:
        answer = ""
        error = str(exc)
    elapsed = time.time() - t0
    return {
        "persona_id": persona["id"],
        "strategy": strategy,
        "elapsed_seconds": round(elapsed, 2),
        "answer": answer,
        "error": error,
    }


async def main() -> None:
    personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
    results: list[dict] = []

    total = len(personas) * len(STRATEGIES)
    done = 0

    for persona in personas:
        for strategy in STRATEGIES:
            done += 1
            print(f"[{done}/{total}] persona={persona['id']} strategy={strategy} ...", flush=True)
            row = await run_one(persona, strategy)
            results.append(row)
            await asyncio.sleep(PAUSE)
            # Save after every call so we don't lose progress
            RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also save as CSV
    with RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["persona_id", "strategy", "elapsed_seconds", "answer", "error"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\nDone. {len(results)} test cases saved to:")
    print(f"  {RESULTS_JSON}")
    print(f"  {RESULTS_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
