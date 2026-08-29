"""Baseline lead classification and generic outreach draft pipeline."""
import csv
import json
import os
import time

from llm import baseline_classify_lead

GENERIC_TEMPLATE = """Subject: Wholesale Singing Bowl Supplier Inquiry

Hello {company},

We are a singing bowl manufacturer and exporter. We would like to introduce
our products to your business and offer a wholesale partnership.

Please let us know if you are interested and we can send our catalog.

Best regards,
Sales Team
"""

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_PATH = os.path.join(HERE, "data", "leads.csv")
OUTBOX_DIR = os.path.join(HERE, "outbox", "baseline")
TRAJ_DIR = os.path.join(HERE, "trajectories")


def load_leads():
    with open(LEADS_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run():
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    os.makedirs(TRAJ_DIR, exist_ok=True)
    leads = load_leads()
    results = []
    t0 = time.time()

    for lead in leads:
        cls = baseline_classify_lead(lead)
        good = cls["fit_score"] >= 0.5
        results.append({
            "id": lead["id"], "company": lead["company"],
            "classified_good_lead": good, "fit_score": cls["fit_score"],
        })
        if good:
            with open(os.path.join(OUTBOX_DIR, f"{lead['id']}.txt"), "w", encoding="utf-8") as f:
                f.write(GENERIC_TEMPLATE.format(company=lead["company"]))

    elapsed = time.time() - t0
    summary = {
        "pipeline": "baseline", "total_leads": len(leads),
        "classified_good": sum(r["classified_good_lead"] for r in results),
        "elapsed_seconds": round(elapsed, 3), "results": results,
    }
    with open(os.path.join(TRAJ_DIR, "baseline_run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[baseline] {summary['classified_good']}/{summary['total_leads']} good leads; dry-run only")
    return summary


if __name__ == "__main__":
    run()
