import csv
import json
import os
import time

from llm import classify_lead, personalize_email

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_PATH = os.path.join(HERE, "data", "leads.csv")
OUTBOX_DIR = os.path.join(HERE, "outbox", "agent")
MEMORY_PATH = os.path.join(HERE, "memory", "contacted.json")
TRAJ_DIR = os.path.join(HERE, "trajectories", "agent")


def load_leads():
    with open(LEADS_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_memory():
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"contacted_ids": []}


def save_memory(mem):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def verify(lead, classification, memory):
    flags = []
    approved = True
    if not lead.get("contact_email") or "@" not in lead["contact_email"]:
        flags.append("missing_or_invalid_email")
        approved = False
    if lead["id"] in memory.get("contacted_ids", []):
        flags.append("already_contacted_per_memory")
        approved = False
    score = classification.get("fit_score", 0)
    evidence = classification.get("evidence", [])
    if score >= 0.5 and not evidence:
        flags.append("high_score_no_evidence_contradiction")
        approved = False
    if score < 0.5:
        flags.append("below_fit_threshold")
        approved = False
    return {"approved": approved, "flags": flags}


def run():
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    os.makedirs(TRAJ_DIR, exist_ok=True)
    leads = load_leads()
    memory = load_memory()
    results = []
    t0 = time.time()

    for lead in leads:
        trajectory = {"lead_id": lead["id"], "company": lead["company"], "steps": []}
        classification = classify_lead(lead)
        trajectory["steps"].append({"step": "classify", "output": classification})
        verdict = verify(lead, classification, memory)
        trajectory["steps"].append({"step": "verify", "output": verdict})
        email_text = None
        if verdict["approved"]:
            email_text = personalize_email(lead, classification)
            with open(os.path.join(OUTBOX_DIR, f"{lead['id']}.txt"), "w", encoding="utf-8") as f:
                f.write(email_text)
            memory.setdefault("contacted_ids", []).append(lead["id"])
            trajectory["steps"].append({"step": "personalize", "output": "draft written to outbox"})
        trajectory["steps"].append({"step": "memory", "output": {"contacted": email_text is not None}})
        trajectory["steps"].append({"step": "human_approval_gate", "output": "dry-run only; nothing sent"})
        with open(os.path.join(TRAJ_DIR, f"{lead['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(trajectory, f, indent=2)
        results.append({
            "id": lead["id"], "company": lead["company"],
            "fit_score": classification.get("fit_score", 0),
            "approved": verdict["approved"], "flags": verdict["flags"],
        })

    save_memory(memory)
    elapsed = time.time() - t0
    summary = {
        "pipeline": "agent", "total_leads": len(leads),
        "approved_and_emailed": sum(r["approved"] for r in results),
        "rejected_by_guardrail": sum(not r["approved"] for r in results),
        "elapsed_seconds": round(elapsed, 3), "results": results,
    }
    with open(os.path.join(HERE, "trajectories", "agent_run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[agent] {summary['approved_and_emailed']}/{summary['total_leads']} approved; dry-run only")
    return summary


if __name__ == "__main__":
    run()
