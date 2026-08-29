import csv
import html
import json
import os
from wsgiref.util import setup_testing_defaults

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_leads():
    with open(os.path.join(ROOT, "data", "leads.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify(lead):
    text = lead["raw_snippet"].lower()
    bowl = [x for x in ["singing bowl", "singing bowls", "sound therapy", "sound-therapy", "tibetan bowl", "brass bowl", "bronze bowl"] if x in text]
    intent = [x for x in ["sourcing", "looking for", "expanding", "new suppliers", "supplier", "onboarding", "manufacturer", "actively", "invite", "invites"] if x in text]
    bad = [x for x in ["auto parts", "logistics", "office supplies", "hardware", "toys", "apparel", "pet products", "digital marketing", "seo"] if x in text]
    if bad and not bowl:
        score = 0.05
    elif bowl and intent:
        score = 0.90
    elif bowl:
        score = 0.60
    else:
        score = 0.10
    return score, bowl + intent


def page():
    leads = []
    for lead in load_leads():
        score, evidence = classify(lead)
        lead = dict(lead)
        lead["score"] = score
        lead["evidence"] = evidence
        leads.append(lead)
    good = sum(x["score"] >= 0.5 for x in leads)
    evidence_pct = 100 if good else 0
    cards = []
    for x in leads:
        score = x["score"]
        state = "Qualified" if score >= 0.5 else "Rejected"
        cls = "good" if score >= 0.5 else "bad"
        ev = ", ".join(x["evidence"][:3]) if x["evidence"] else "No supporting signal found"
        cards.append(f'''<article class="lead" data-search="{html.escape((x['company']+' '+x['country']+' '+x['raw_snippet']).lower())}" data-state="{cls}">
          <div class="lead-main"><div class="avatar">{html.escape(x['company'][:1])}</div><div><h3>{html.escape(x['company'])}</h3><p>{html.escape(x['country'])} · {html.escape(x['contact_email'])}</p></div></div>
          <div class="score {cls}">{score:.2f}</div><div class="status {cls}">{state}</div>
          <p class="snippet">{html.escape(x['raw_snippet'])}</p><div class="evidence"><b>Evidence</b> · {html.escape(ev)}</div>
          <button class="review" onclick="openLead(this)" data-company="{html.escape(x['company'])}" data-email="{html.escape(x['contact_email'])}" data-snippet="{html.escape(x['raw_snippet'])}" data-score="{score:.2f}" data-evidence="{html.escape(ev)}">Review draft →</button>
        </article>''')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agentic Lead Outreach</title>
<style>
:root{{--bg:#080d18;--panel:#111a2b;--panel2:#172238;--line:#263553;--text:#f5f7fb;--muted:#91a0b8;--green:#35d0a0;--red:#ff766d;--blue:#79a9ff;--orange:#ffb45e}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 75% -10%,#182a4b 0,#080d18 42%);color:var(--text);font:14px Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}button,input{{font:inherit}}.shell{{max-width:1440px;margin:auto;padding:28px}}header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}}.brand{{display:flex;gap:14px;align-items:center}}.logo{{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#6ea8ff,#35d0a0);display:grid;place-items:center;font-weight:900;color:#07101d}}h1{{font-size:25px;margin:0}}.sub{{color:var(--muted);margin-top:4px}}.pill{{border:1px solid #2c456b;background:#122039;color:#bcd1f5;padding:8px 12px;border-radius:999px}}.hero{{display:grid;grid-template-columns:1.5fr 1fr;gap:18px;margin-bottom:18px}}.hero-card,.panel{{background:rgba(17,26,43,.9);border:1px solid var(--line);border-radius:20px;box-shadow:0 18px 50px #0005}}.hero-card{{padding:28px}}.eyebrow{{color:var(--green);font-weight:800;letter-spacing:.12em;font-size:11px}}.hero h2{{font-size:38px;line-height:1.05;margin:10px 0}}.hero p{{color:var(--muted);max-width:700px;line-height:1.7}}.steps{{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}}.step{{padding:9px 11px;border-radius:10px;background:#1a2942;color:#d9e3f3;border:1px solid #293d5e}}.metrics{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.metric{{padding:22px;background:#0f1727;border:1px solid var(--line);border-radius:16px}}.metric b{{display:block;font-size:30px;margin:6px 0}.metric span{{color:var(--muted)}}.toolbar{{display:flex;gap:12px;align-items:center;padding:18px 20px;border-bottom:1px solid var(--line)}}input{{flex:1;background:#0b1322;border:1px solid #2a3b58;border-radius:11px;padding:12px 14px;color:white;outline:none}}.filter{{border:1px solid #2a3b58;background:#111c30;color:#b9c8dd;border-radius:10px;padding:10px 13px;cursor:pointer}}.filter.active{{background:#223553;color:white}}.leads{{padding:14px;display:grid;gap:10px}}.lead{{position:relative;background:#0e1727;border:1px solid #21314b;border-radius:15px;padding:16px 18px;display:grid;grid-template-columns:1fr 85px 105px;gap:10px;align-items:center}}.lead:hover{{border-color:#3b5a84;transform:translateY(-1px)}}.lead-main{{display:flex;gap:12px;align-items:center}}.avatar{{width:38px;height:38px;border-radius:12px;background:#1c2b45;display:grid;place-items:center;font-weight:800;color:#9fc3ff}}h3{{margin:0 0 4px;font-size:15px}}.lead p{{margin:0;color:var(--muted)}}.score{{font-weight:900;font-size:19px;text-align:right}}.score.good{{color:var(--green)}}.score.bad{{color:var(--red)}}.status{{font-size:11px;font-weight:800;text-align:center;padding:7px;border-radius:8px}}.status.good{{background:#10362d;color:var(--green)}}.status.bad{{background:#3a1b22;color:var(--red)}}.snippet{{grid-column:1/-1!important;line-height:1.55;color:#b8c4d5!important;margin-left:50px!important}}.evidence{{grid-column:1/3;background:#101e31;border-radius:9px;padding:9px 11px;color:#b9c8dc;font-size:12px;margin-left:50px}}.evidence b{{color:#dce8fa}}.review{{grid-column:3;grid-row:3;background:#1d2e49;border:1px solid #355071;color:#d9e7fb;padding:9px;border-radius:9px;cursor:pointer}}.review:hover{{background:#294363}}.empty{{padding:50px;text-align:center;color:var(--muted)}}.modal{{display:none;position:fixed;inset:0;background:#020611aa;backdrop-filter:blur(8px);z-index:5;place-items:center;padding:20px}}.modal.show{{display:grid}}.dialog{{width:min(900px,100%);background:#101a2c;border:1px solid #30425f;border-radius:20px;padding:25px;box-shadow:0 30px 100px #0009}}.dialog-top{{display:flex;justify-content:space-between;gap:20px}}.close{{background:none;border:0;color:#aebbd0;font-size:25px;cursor:pointer}}.draft{{margin-top:18px;background:#0b1321;border:1px solid #253650;border-radius:14px;padding:18px;line-height:1.75;white-space:pre-wrap;color:#d9e2ef}}.actions{{display:flex;gap:10px;margin-top:15px}}.approve{{background:var(--green);color:#06251c;border:0;border-radius:10px;padding:11px 16px;font-weight:800}}.reject{{background:#202d42;color:#d6e1f0;border:1px solid #344963;border-radius:10px;padding:11px 16px}}footer{{color:#687992;text-align:center;padding:25px}}@media(max-width:850px){{.hero{{grid-template-columns:1fr}}.lead{{grid-template-columns:1fr 70px}}.status{{grid-column:2}.review{{grid-column:1/3;grid-row:auto}.snippet,.evidence{{margin-left:0!important;grid-column:1/-1!important}}}}
</style></head><body><main class="shell"><header><div class="brand"><div class="logo">AI</div><div><h1>Agentic Lead Outreach</h1><div class="sub">Evidence-grounded B2B qualification & safe outreach</div></div></div><div class="pill">● DRY RUN · HUMAN APPROVAL</div></header>
<section class="hero"><div class="hero-card"><div class="eyebrow">AGENT WORKFLOW</div><h2>Turn noisy leads into<br>review-ready opportunities.</h2><p>Classify every prospect, verify evidence, protect against duplicates, and draft a specific outreach email — without automatically sending anything.</p><div class="steps"><div class="step">01 Classify</div><div class="step">02 Verify</div><div class="step">03 Memory</div><div class="step">04 Personalize</div><div class="step">05 Human approval</div></div></div><div class="metrics"><div class="metric"><span>Total leads</span><b>{len(leads)}</b><span>synthetic evaluation set</span></div><div class="metric"><span>Qualified</span><b style="color:var(--green)">{good}</b><span>fit score ≥ 0.50</span></div><div class="metric"><span>Evidence coverage</span><b style="color:var(--blue)">{evidence_pct}%</b><span>for qualified leads</span></div><div class="metric"><span>Auto-send</span><b style="color:var(--orange)">OFF</b><span>human gate required</span></div></div></section>
<section class="panel"><div class="toolbar"><input id="search" placeholder="Search company, country, or lead signal…" oninput="filterLeads()"><button class="filter active" data-filter="all" onclick="setFilter('all',this)">All</button><button class="filter" data-filter="good" onclick="setFilter('good',this)">Qualified</button><button class="filter" data-filter="bad" onclick="setFilter('bad',this)">Rejected</button></div><div class="leads" id="leads">{''.join(cards)}</div></section><footer>Agentic B2B Lead Outreach · Claude-ready · Deterministic mock mode · No real emails are sent</footer></main>
<div class="modal" id="modal"><div class="dialog"><div class="dialog-top"><div><div class="eyebrow">HUMAN REVIEW</div><h2 id="mCompany" style="margin:7px 0"></h2><div id="mMeta" class="sub"></div></div><button class="close" onclick="closeModal()">×</button></div><div class="draft" id="draft"></div><div class="actions"><button class="approve" onclick="approve()">✓ Approve draft</button><button class="reject" onclick="closeModal()">Reject</button></div></div></div>
<script>let currentFilter='all';function setFilter(f,b){{currentFilter=f;document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');filterLeads()}}function filterLeads(){{let q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.lead').forEach(x=>x.style.display=((currentFilter==='all'||x.dataset.state===currentFilter)&&x.dataset.search.includes(q))?'grid':'none')}}function openLead(b){{let c=b.dataset.company,e=b.dataset.email,s=b.dataset.snippet,score=b.dataset.score,ev=b.dataset.evidence;document.getElementById('mCompany').textContent=c;document.getElementById('mMeta').textContent=e+' · Fit score '+score+' · '+ev;document.getElementById('draft').textContent='Subject: A tailored wholesale introduction for '+c+'\n\nHi '+c+' team,\n\nI noticed your mention of '+(ev||'your product range')+'. We work with international buyers looking for handcrafted Tibetan singing bowls from India, with wholesale sourcing support.\n\nBased on your current needs, I would be happy to share a short catalog and current MOQ/pricing for your review.\n\nWould you be open to a quick conversation about your range?\n\nBest regards,\nExport Team';document.getElementById('modal').classList.add('show')}}function closeModal(){{document.getElementById('modal').classList.remove('show')}}function approve(){{alert('Draft approved for review. No email was sent.');closeModal()}}</script></body></html>'''


def application(environ, start_response):
    setup_testing_defaults(environ)
    path = environ.get("PATH_INFO", "/")
    if path == "/api/health":
        body = json.dumps({"status": "ok", "service": "agentic-lead-outreach"}).encode()
        start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
        return [body]
    body = page().encode("utf-8")
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


app = application
