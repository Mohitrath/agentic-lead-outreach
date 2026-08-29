import json
import os

import agent
import baseline

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS_PATH = os.path.join(HERE, "data", "eval_labels.json")


def load_labels():
    with open(LABELS_PATH, encoding="utf-8") as f:
        return json.load(f)["labels"]


def score_classification(results, labels):
    tp = fp = tn = fn = 0
    for r in results:
        gt = labels[r["id"]]["is_good_lead"]
        pred = r.get("classified_good_lead", r.get("approved", False))
        if gt and pred:
            tp += 1
        elif gt and not pred:
            fn += 1
        elif not gt and pred:
            fp += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    return {
        "accuracy": round((tp + tn) / total, 3) if total else 0,
        "precision": round(tp / (tp + fp), 3) if tp + fp else 0,
        "recall": round(tp / (tp + fn), 3) if tp + fn else 0,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }


def personalization_quality(outbox_dir):
    if not os.path.isdir(outbox_dir):
        return {"emails_checked": 0, "specific_pct": 0}
    files = [f for f in os.listdir(outbox_dir) if f.endswith(".txt")]
    generic_marker = "We are a singing bowl manufacturer and exporter. We would like to introduce"
    specific = 0
    for name in files:
        with open(os.path.join(outbox_dir, name), encoding="utf-8") as f:
            text = f.read()
        if generic_marker not in text:
            specific += 1
    return {"emails_checked": len(files), "specific_pct": round(100 * specific / len(files), 1) if files else 0}


def main():
    labels = load_labels()
    print("=" * 60)
    print("Running BASELINE...")
    b_summary = baseline.run()
    print("Running AGENT...")
    a_summary = agent.run()
    print("=" * 60)

    report = {
        "note": "Same 20 leads, same eval labels, used for both pipelines.",
        "baseline": {
            "classification": score_classification(b_summary["results"], labels),
            "personalization": personalization_quality(os.path.join(HERE, "outbox", "baseline")),
            "elapsed_seconds": b_summary["elapsed_seconds"],
            "flagged_rejections": 0,
        },
        "agent": {
            "classification": score_classification(a_summary["results"], labels),
            "personalization": personalization_quality(os.path.join(HERE, "outbox", "agent")),
            "elapsed_seconds": a_summary["elapsed_seconds"],
            "flagged_rejections": a_summary["rejected_by_guardrail"],
        },
    }
    with open(os.path.join(HERE, "trajectories", "evaluation_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
