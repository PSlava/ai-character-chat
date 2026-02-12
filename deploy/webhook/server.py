"""GitHub webhook receiver for auto-deploy.

Listens on port 9000, verifies webhook signature,
and triggers deploy.sh on push to main.
"""

import hashlib
import hmac
import os
import subprocess
import threading
from datetime import datetime, timezone

from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.environ.get("WEBHOOK_SECRET", "")
REPO_DIR = "/app/repo"
DEPLOY_SCRIPT = os.path.join(REPO_DIR, "deploy", "deploy.sh")

# Track deploy info
_last_deploy: dict = {}
_deploy_lock = threading.Lock()


def verify_signature(payload: bytes, signature: str) -> bool:
    if not SECRET:
        return True  # no secret configured — skip verification
    expected = "sha256=" + hmac.new(
        SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _run_deploy():
    """Run deploy.sh and update status when done."""
    try:
        result = subprocess.run(
            ["bash", DEPLOY_SCRIPT],
            cwd=REPO_DIR,
            stdout=open("/tmp/deploy.log", "a"),
            stderr=subprocess.STDOUT,
            timeout=600,  # 10 min max
        )
        with _deploy_lock:
            _last_deploy["status"] = "done" if result.returncode == 0 else "failed"
            _last_deploy["finished_at"] = datetime.now(timezone.utc).isoformat()
            _last_deploy["exit_code"] = result.returncode
    except subprocess.TimeoutExpired:
        with _deploy_lock:
            _last_deploy["status"] = "timeout"
            _last_deploy["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        with _deploy_lock:
            _last_deploy["status"] = "failed"
            _last_deploy["error"] = str(e)[:200]
            _last_deploy["finished_at"] = datetime.now(timezone.utc).isoformat()


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
            with _deploy_lock:
                _last_deploy.update({
                    "commit": commit.get("id", "")[:7],
                    "message": commit.get("message", "").split("\n")[0],
                    "author": commit.get("author", {}).get("name", ""),
                    "deployed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "deploying",
                })
            # Run deploy in background thread
            thread = threading.Thread(target=_run_deploy, daemon=True)
            thread.start()
            return jsonify({"status": "deploying"})
        return jsonify({"status": "ignored", "ref": ref})

    return jsonify({"status": "ignored", "event": event})


def _get_git_info() -> dict:
    """Read current commit and commit date from repo."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_DIR, text=True, timeout=5
        ).strip()
        message = subprocess.check_output(
            ["git", "log", "-1", "--format=%s"],
            cwd=REPO_DIR, text=True, timeout=5
        ).strip()
        commit_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
            cwd=REPO_DIR, text=True, timeout=5
        ).strip()
        return {"commit": commit, "message": message, "commit_date": commit_date}
    except Exception:
        return {}


_STARTED_AT = datetime.now(timezone.utc).isoformat()


@app.route("/health")
def health():
    info = {"status": "ok", "started_at": _STARTED_AT, **_get_git_info()}
    if _last_deploy:
        with _deploy_lock:
            info["last_deploy"] = dict(_last_deploy)
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
