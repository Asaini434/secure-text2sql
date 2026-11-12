import json
import pickle
import sys
from pathlib import Path
from text2sql.db import load_questions, run_sql
from text2sql.pipeline import ask

GOLD_CACHE = Path("eval/gold_cache.pkl")
# Each experiment = a name + the settings it passes to ask()
CONFIGS = {
    "baseline": {"max_retries": 0},
    "selfcorrect": {"max_retries": 2},
}

def gold_results(questions):
    """Run every gold query once and cache the rows; mark ones that time out as None."""
    if GOLD_CACHE.exists():
        return pickle.loads(GOLD_CACHE.read_bytes())
    gold = {}
    for i, q in enumerate(questions, 1):
        try:
            gold[q["question_id"]] = set(run_sql(q["db_id"], q["SQL"], timeout=120))
        except Exception:
            gold[q["question_id"]] = None   # gold query too slow: can't grade this one
        print(f"gold answers: {i}/{len(questions)}", end="\r")
    GOLD_CACHE.write_bytes(pickle.dumps(gold))
    skipped = sum(v is None for v in gold.values())
    print(f"\n{skipped} gold queries timed out and will be skipped")
    return gold


def main(run_name="baseline", limit=None):
    all_questions = load_questions()
    gold = gold_results(all_questions)
    questions = all_questions[:limit]

    out_path = Path(f"eval/results_{run_name}.jsonl")
    done = {json.loads(line)["id"] for line in out_path.open()} if out_path.exists() else set()

    with out_path.open("a") as f:
        for i, q in enumerate(questions, 1):
            if q["question_id"] in done:
                continue  # already graded in an earlier run
            if gold[q["question_id"]] is None:
                continue  # no gold answer to compare against
            out = ask(q["db_id"], q["question"], q["evidence"], **CONFIGS[run_name])
            ok = out["error"] is None and set(out["rows"]) == gold[q["question_id"]]
            f.write(json.dumps({"id": q["question_id"], "difficulty": q["difficulty"],
                                "correct": ok, "sql": out["sql"], "error": out["error"]}) + "\n")
            f.flush()
            print(f"[{i}/{len(questions)}] {'✅' if ok else '❌'}")

    results = [json.loads(line) for line in out_path.open()]
    correct = sum(r["correct"] for r in results)
    print(f"\nExecution accuracy: {correct}/{len(results)} = {correct / len(results):.1%}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(name, limit)