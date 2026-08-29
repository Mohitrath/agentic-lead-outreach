from flask import Flask, Response

from app import page

app = Flask(__name__)


@app.get("/")
def home():
    return Response(page(), mimetype="text/html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "agentic-lead-outreach"}
