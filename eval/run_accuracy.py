import json
import sys
from text2sql.db import load_questions, run_sql
from text2sql.pipeline import ask


def is_correct(q, out):
    """Correct if the model's rows match the gold SQL's rows (BIRD's rule)."""
    if out["error"]:
        return False
    gold = run_sql(q["db_id"], q["SQL"])
    return set(out["rows"]) == set(gold)


def main(limit=None):
    questions = load_questions()[:limit]
    results, correct = [], 0
    for i, q in enumerate(questions, 1):
        out = ask(q["db_id"], q["question"], q["evidence"])
        ok = is_correct(q, out)
        correct += ok
        results.append({"id": q["question_id"], "difficulty": q["difficulty"],
                        "correct": ok, "sql": out["sql"], "error": out["error"]})
        print(f"[{i}/{len(questions)}] {'✅' if ok else '❌'}  running accuracy: {correct / i:.1%}")

    with open("eval/results_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nExecution accuracy: {correct}/{len(questions)} = {correct / len(questions):.1%}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)