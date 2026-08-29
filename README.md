# Agentic B2B Lead Qualification & Outreach for a Singing Bowl Exporter

**micro1 Agentic Workflows Hackathon submission**

## Who has this problem?

A small artisan manufacturer/exporter of Tibetan singing bowls (based in India)
selling wholesale to international retailers, wellness stores, and trading
companies. This is a real business I've been building export tooling for
already — this project extends that with an agentic lead-qualification and
outreach layer.

## What bottleneck makes it worth solving?

International buyer discovery happens through directories, trade-show lists,
and LinkedIn/web mentions — noisy, unstructured text snippets, most of which
are **not** relevant (auto parts distributors, toy wholesalers, logistics
companies all show up alongside genuine wellness/sourcing prospects). Today
this is done manually by one person:

- Reading each lead and deciding "is this worth emailing?" — slow, and
  inconsistent under time pressure (easy to over-trigger on the word
  "wellness" or "import" and waste outreach on a bad fit).
- Sending the same generic template to everyone who passes, because writing
  a custom email per lead doesn't scale.
- No memory across sessions — a lead can get emailed twice by accident, which
  reads as unprofessional to an international B2B buyer.

None of this requires new information the business doesn't have — it requires
consistently *applying judgment* across a growing pile of leads. That's a good
fit for an agent: not fully autonomous "send the email" (a human should
approve real outreach — this is a relationship business), but reliable triage,
evidence-grounded reasoning, and personalization.

## Does the agent solve it well?

Yes — see [Evaluation](#evaluation-results) below. Against a fair baseline,
the agent pipeline reaches perfect classification accuracy on the 20-lead eval
set (vs. 95% for the baseline), and every email it drafts references a specific,
real detail about that lead instead of generic boilerplate.

## Can another person reproduce the result?

Yes — see [Reproduction Guide](#reproduction-guide). No API key required to run
the full pipeline end to end (it falls back to a deterministic mock "LLM" so
grading doesn't depend on anyone's API budget); set `ANTHROPIC_API_KEY` to
switch both pipelines to real Claude calls with the exact same code path.

---

## Architecture

```
data/leads.csv          20 synthetic, realistic scraped B2B lead snippets
data/eval_labels.json   hand-labeled ground truth for evaluation only

src/llm.py              LLM abstraction: real Claude API call if
                         ANTHROPIC_API_KEY is set, else deterministic mock
src/baseline.py         BASELINE: one basic classification prompt + generic email
src/agent.py            AGENT: classify -> verify -> personalize -> memory -> approval gate
src/evaluate.py         Runs both pipelines and scores them

memory/contacted.json   persists across runs — no double-contact
outbox/baseline/        dry-run baseline emails
outbox/agent/           dry-run agent emails
trajectories/agent/     one JSON trajectory per lead
trajectories/*.json     run summaries + evaluation report
```

### Agent capabilities used

| Capability | Where | Why |
|---|---|---|
| Structured reasoning + evidence | `classify_lead` | Preserves the *why* for later verification and human review |
| Verification / guardrail | `verify()` | Fails closed on contradictions, missing contact info, or duplicates |
| Memory | `memory/contacted.json` | Prevents accidental double-contact across runs |
| Human-approval gate | end of `agent.py` | Outreach stays in dry-run/outbox and is never auto-sent |

I did **not** add multi-agent orchestration: a single agent with a clear tool
sequence was enough for this task, without adding complexity for its own sake.

---

## Evaluation results

Same 20 leads, same evaluation labels, same threshold (fit_score ≥ 0.5), run
with the default mock LLM:

| Metric | Baseline | Agent | Change |
|---|---|---|---|
| Classification accuracy | 0.95 | **1.0** | +0.05 |
| Precision (good-lead calls) | 0.917 | **1.0** | +0.083 |
| Recall (good-lead calls) | 1.0 | 1.0 | +0.0 |
| Emails with lead-specific evidence | 0% | **100%** | +100 pts |
| False positives (bad leads emailed) | 1 | **0** | -1 |

Full machine-readable report: `trajectories/evaluation_report.json`.
Full changelog: [`CHANGELOG.md`](./CHANGELOG.md).

**Human time per task (estimated, not machine-measured):** manual triage and
writing for 20 leads takes roughly 25–35 minutes; the pipeline runs in under a
second for the mock classification/drafting, leaving only a final human skim
and approval step (~2–3 minutes for 20 leads).

---

## Reproduction guide

Requires Python 3.9+. No paid API key is needed for the default run.

```bash
cd agentic-lead-outreach
pip install -r requirements.txt      # only needed for real Claude calls

cd src
python3 evaluate.py
```

Or run either pipeline alone:

```bash
python3 baseline.py
python3 agent.py
```

Expected output: console summary + `trajectories/evaluation_report.json`,
`outbox/baseline/*.txt`, `outbox/agent/*.txt`, and
`trajectories/agent/*.json`.

### Real Claude mode

Set `ANTHROPIC_API_KEY` in your environment. Do not commit your real key.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 evaluate.py
```

Both pipelines automatically switch to real Claude calls without other code
changes.

### Reset agent memory

```bash
echo '{"contacted_ids": []}' > memory/contacted.json
```

### Real email sending

This project intentionally stops at dry-run/outbox. Real email sending is not
automated: consequential outreach should be reviewed and explicitly approved
by a human first.

---

## Hot take / insight

The most valuable guardrail wasn't a smarter classification prompt — it was
rejecting the model's own high score when it couldn't point to evidence
(`high_score_no_evidence_contradiction` in `verify()`). A confident-sounding
"yes" with no supporting quote is easy to miss in manual review. Forcing the
model to cite evidence, then mechanically checking that the evidence actually
exists, catches a whole class of plausible-but-wrong classifications.
