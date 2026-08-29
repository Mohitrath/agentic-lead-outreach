# Demo Video Script

## 1. Problem
Show the `data/leads.csv` file and explain that international buyer discovery produces noisy B2B snippets. The goal is to identify genuine singing-bowl prospects without wasting outreach.

## 2. Baseline
Run:

```bash
cd src
python3 baseline.py
```

Show that the baseline makes a simple classification and creates generic drafts in `outbox/baseline/`.

## 3. Agent
Run:

```bash
python3 agent.py
```

Explain the sequence: classify with evidence, verify with guardrails, personalize, remember contacted leads, then stop at a human-approval dry-run gate.

## 4. Evaluation
Run:

```bash
python3 evaluate.py
```

Open `trajectories/evaluation_report.json` to show the comparison on the same 20 leads. The default mock mode is deterministic, so the demo does not require a paid API key.

## 5. Key insight
Highlight `high_score_no_evidence_contradiction`: confidence without evidence is rejected. This is the core guardrail that makes the pipeline safer and more auditable.
