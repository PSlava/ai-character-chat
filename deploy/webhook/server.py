"""GitHub webhook receiver for auto-deploy.

Listens on port 9000, verifies webhook signature,
and triggers deploy.sh on push to main.
"""

import hashlib
import hmac
import os
import subprocess
import json
from datetime import datetime, timezone

from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.environ.get("WEBHOOK_SECRET", "")
REPO_DIR = "/app/repo"
DEPLOY_SCRIPT = os.path.join(REPO_DIR, "deploy", "deploy.sh")

# Track deploy info
_last_deploy: dict = {}


def verify_signature(payload: bytes, signature: str) -> bool:
    if not SECRET:
        return True  # no secret configured — skip verification
    expected = "sha256=" + hmac.new(
        SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "invalid signature"}), 403

    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return jsonify({"status": "pong"})

    if event == "push":
        payload = request.get_json(silent=True) or {}
        ref = payload.get("ref", "")
        if ref == "refs/heads/main":
            commit = payload.get("head_commit", {})
            _last_deploy.update({
                "commit": commit.get("id", "")[:7],
                "message": commit.get("message", "").split("\n")[0],
                "author": commit.get("author", {}).get("name", ""),
                "deployed_at": datetime.now(timezone.utc).isoformat(),
                "status": "deploying",
            })
            # Run deploy in background
            subprocess.Popen(
                ["bash", DEPLOY_SCRIPT],
                cwd=REPO_DIR,
                stdout=open("/tmp/deploy.log", "a"),
                stderr=subprocess.STDOUT,
            )
            return jsonify({"status": "deploying"})
        return jsonify({"status": "ignored", "ref": ref})

    return jsonify({"status": "ignored", "event": event})


def _get_git_info() -> dict:
    """Read current commit from repo."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_DIR, text=True, timeout=5
        ).strip()
        message = subprocess.check_output(
            ["git", "log", "-1", "--format=%s"],
            cwd=REPO_DIR, text=True, timeout=5
        ).strip()
        return {"commit": commit, "message": message}
    except Exception:
        return {}


@app.route("/health")
def health():
    info = {"status": "ok", **_get_git_info()}
    if _last_deploy:
        info["last_deploy"] = _last_deploy
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
