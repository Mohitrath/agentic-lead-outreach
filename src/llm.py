"""
LLM abstraction used by both the baseline and the agent.

By default this uses a deterministic mock model so the project runs without
API setup. Setting ANTHROPIC_API_KEY switches to real Claude calls.
"""

import os
import re
import json

USE_REAL_LLM = bool(os.environ.get("ANTHROPIC_API_KEY"))

BOWL_SIGNALS = [
    "singing bowl", "singing bowls", "sound therapy", "sound-therapy",
    "sound bath", "tibetan bowl", "brass bowl", "bronze bowl",
    "hand-hammered bowl", "hammered bowl", "meditation accessor",
]
BUYER_INTENT_SIGNALS = [
    "sourcing", "looking for", "expanding our", "new suppliers",
    "supplier page", "onboarding new", "manufacturer inquiries",
    "manufacturing partners", "become a supplier", "vendor page",
    "actively", "invite", "invites",
]
DISQUALIFY_SIGNALS = [
    "auto parts", "logistics", "freight forwarding", "office supplies",
    "hardware", "toys", "apparel wholesaler", "pet food", "digital marketing",
    "seo", "construction supplies",
]


def _mock_classify(lead: dict) -> dict:
    text = lead["raw_snippet"].lower()
    bowl_hits = [s for s in BOWL_SIGNALS if s in text]
    intent_hits = [s for s in BUYER_INTENT_SIGNALS if s in text]
    disqualifiers = [s for s in DISQUALIFY_SIGNALS if s in text]

    if disqualifiers and not bowl_hits:
        score = 0.05
        reason = f"No singing-bowl or wellness relevance; matches unrelated category signal(s): {disqualifiers}."
    elif bowl_hits and intent_hits:
        score = 0.9
        reason = f"Direct product relevance ({bowl_hits}) plus explicit buying/sourcing intent ({intent_hits})."
    elif bowl_hits:
        score = 0.6
        reason = f"Sells/stocks singing bowls ({bowl_hits}) but no explicit new-supplier intent language found."
    else:
        score = 0.1
        reason = "No singing-bowl-specific or sourcing-intent language detected in snippet."

    return {"fit_score": score, "reasoning": reason, "evidence": bowl_hits + intent_hits}


def _mock_personalize(lead: dict, classification: dict) -> str:
    evidence = classification.get("evidence") or []
    hook = evidence[0] if evidence else "your wellness product range"
    company = lead["company"]
    return (
        f"Subject: Handcrafted Singing Bowls for {company} — Direct from Artisan Workshop\n\n"
        f"Hi {company} team,\n\n"
        f"I came across your listing mentioning \"{hook}\" and wanted to reach out directly. "
        f"We're a small artisan workshop producing hand-hammered brass and bronze singing bowls "
        f"for international wholesale, with full export documentation handled on our end.\n\n"
        f"Given what you've shared about your sourcing needs, I'd love to send a short catalog "
        f"and current MOQ/pricing for your review — no obligation, just want to see if there's a fit.\n\n"
        f"Would a quick reply work, or is there a better contact for sourcing decisions on your side?\n\n"
        f"Best regards,\n[Your Name]\n[Workshop Name] — Singing Bowl Manufacturer & Exporter"
    )


def _real_classify(lead: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    prompt = f"""You are evaluating whether a company is a genuine B2B buyer prospect for a
small singing-bowl manufacturer and exporter.

Company: {lead['company']} ({lead['country']})
Raw scraped info: {lead['raw_snippet']}

Score this prospect on 0.0-1.0 based on product relevance and explicit sourcing intent.
Respond ONLY with JSON: {{"fit_score": <float 0-1>, "reasoning": "<one sentence>", "evidence": ["<short phrase>", ...]}}"""
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = re.sub(r"^```json|```$", "", resp.content[0].text.strip()).strip()
    return json.loads(text)


def _real_personalize(lead: dict, classification: dict) -> str:
    import anthropic
    client = anthropic.Anthropic()
    prompt = f"""Write a short, specific, non-generic cold outreach email from a small singing-bowl
manufacturer/exporter to this prospect. Reference the specific evidence below. Keep it under
150 words, include a subject line, and end with a soft low-pressure call to action.

Company: {lead['company']} ({lead['country']})
Evidence: {classification.get('evidence')}
Why they're a fit: {classification.get('reasoning')}
"""
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _mock_baseline_classify(lead: dict) -> dict:
    text = lead["raw_snippet"].lower()
    is_yes = any(k in text for k in ["wellness", "bowl", "sourcing", "supplier", "import"])
    return {"fit_score": 1.0 if is_yes else 0.0, "reasoning": "keyword match", "evidence": []}


def _real_baseline_classify(lead: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    prompt = (f"Is this company a good lead for a singing bowl seller? "
              f"Company: {lead['company']}. Info: {lead['raw_snippet']}. Answer only yes or no.")
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )
    ans = resp.content[0].text.strip().lower()
    return {"fit_score": 1.0 if ans.startswith("y") else 0.0, "reasoning": ans, "evidence": []}


def baseline_classify_lead(lead: dict) -> dict:
    return _real_baseline_classify(lead) if USE_REAL_LLM else _mock_baseline_classify(lead)


def classify_lead(lead: dict) -> dict:
    return _real_classify(lead) if USE_REAL_LLM else _mock_classify(lead)


def personalize_email(lead: dict, classification: dict) -> str:
    return _real_personalize(lead, classification) if USE_REAL_LLM else _mock_personalize(lead, classification)


def mode_label() -> str:
    return "REAL (Claude API)" if USE_REAL_LLM else "MOCK (rule-based stand-in, no API key set)"
