import json
import sys
from collections import Counter


def main(run_name="baseline"):
    results = [json.loads(line) for line in open(f"eval/results_{run_name}.jsonl")]
    correct = sum(r["correct"] for r in results)
    print(f"Overall: {correct}/{len(results)} = {correct / len(results):.1%}\n")

    for level in ["simple", "moderate", "challenging"]:
        rs = [r for r in results if r["difficulty"] == level]
        ok = sum(r["correct"] for r in rs)
        print(f"  {level:12} {ok}/{len(rs)} = {ok / len(rs):.1%}")

    wrong = [r for r in results if not r["correct"]]
    errors = [r for r in wrong if r["error"]]
    print(f"\nWrong: {len(wrong)}  ->  SQL error: {len(errors)}, ran but wrong rows: {len(wrong) - len(errors)}")

    print("\nMost common SQL errors:")
    for kind, n in Counter(r["error"].split(":")[0] for r in errors).most_common(5):
        print(f"  {n:3}  {kind}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "baseline")