"""Local live dashboard server for the skillforge pipeline.

Serves the dashboard page and the state/*.json files as static files (so the
page can poll them), and accepts approval clicks at POST /api/approve,
writing them to state/approvals.json for the orchestrator to pick up next
time you talk to it in Claude Code.

Run from anywhere:
    python dashboard/server.py
Then open:
    http://localhost:8420/dashboard/
"""

import json
import subprocess
import http.server
import socketserver
from datetime import datetime, timezone
from pathlib import Path

PORT = 8420
ROOT = Path(__file__).resolve().parent.parent  # skillforge/
APPROVALS_FILE = ROOT / "state" / "approvals.json"
PROJECTS_FILE = ROOT / "state" / "projects.json"
DEMO_TIMEOUT_S = 90


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[dashboard] {self.address_string()} - {fmt % args}")

    def end_headers(self):
        # Prevent the browser from caching the JSON state files between polls.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_POST(self):
        if self.path == "/api/approve":
            self._handle_approve()
        elif self.path == "/api/run-demo":
            self._handle_run_demo()
        else:
            self.send_error(404, "Unknown endpoint")

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def _handle_approve(self):
        try:
            body = self._read_json_body()
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON body")
            return

        kind = body.get("kind")  # "gap" | "project" | "stage" | "general"
        name = body.get("name")
        action = body.get("action")  # "approve-build" | "approve-publish" | "skip" | "cancel" | "retry" | "note"
        message = body.get("message")  # free-text, used by "note" and optionally others
        if not (kind and name and action):
            self.send_error(400, "Body must include kind, name, action")
            return

        data = {"pending": []}
        if APPROVALS_FILE.exists():
            data = json.loads(APPROVALS_FILE.read_text(encoding="utf-8"))

        entry = {
            "kind": kind,
            "name": name,
            "action": action,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        if message:
            entry["message"] = message
        data["pending"].append(entry)
        APPROVALS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

        self._send_json({"ok": True})

    def _handle_run_demo(self):
        """Actually runs a project's demo command and returns real captured output,
        so the dashboard can show proof it works rather than just a claim."""
        try:
            body = self._read_json_body()
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON body")
            return

        slug = body.get("slug")
        if not slug:
            self.send_error(400, "Body must include slug")
            return

        projects = json.loads(PROJECTS_FILE.read_text(encoding="utf-8")) if PROJECTS_FILE.exists() else {"projects": []}
        project = next((p for p in projects.get("projects", []) if p.get("slug") == slug), None)
        if not project or not project.get("demo_cmd") or not project.get("demo_dir"):
            self._send_json({"ok": False, "error": "No runnable demo configured for this project yet."}, status=404)
            return

        demo_dir = ROOT / project["demo_dir"]
        if not demo_dir.is_dir():
            self._send_json({"ok": False, "error": f"Project directory not found: {demo_dir}"}, status=404)
            return

        # Resolve a relative executable (e.g. "./.venv/Scripts/python.exe") to an absolute
        # path — Windows CreateProcess doesn't reliably resolve relative executables against
        # a `cwd` passed to subprocess.run, so leaving it relative can fail with WinError 2.
        cmd = list(project["demo_cmd"])
        exe = Path(cmd[0])
        if not exe.is_absolute():
            exe = (demo_dir / cmd[0]).resolve()
        cmd[0] = str(exe)

        started = datetime.now(timezone.utc)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(demo_dir),
                capture_output=True,
                text=True,
                timeout=DEMO_TIMEOUT_S,
            )
            output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
            ok = proc.returncode == 0
        except subprocess.TimeoutExpired as e:
            output = (e.stdout or "") + f"\n[timed out after {DEMO_TIMEOUT_S}s]"
            ok = False
        except OSError as e:
            output = f"Failed to launch demo command: {e}"
            ok = False
        duration_s = (datetime.now(timezone.utc) - started).total_seconds()

        self._send_json({"ok": ok, "output": output.strip(), "duration_s": round(duration_s, 1)})

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"SkillForge dashboard: http://localhost:{PORT}/dashboard/")
        print("Ctrl+C to stop.")
        httpd.serve_forever()
