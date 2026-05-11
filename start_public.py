#!/usr/bin/env python3
"""
Start the AI Interview System with a public tunnel via localhost.run.
Free, no signup, no install — uses SSH which is built into macOS/Linux.

Usage:
    python start_public.py
"""
import sys
import os
import re
import subprocess
import threading
import time
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from config import PORT, GROQ_API_KEY

if not GROQ_API_KEY:
    print("\n⚠️  GROQ_API_KEY is not set in .env")
    sys.exit(1)

public_url = None
tunnel_proc = None
log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
log_path = log_file.name
log_file.close()


def _start_tunnel():
    """Open SSH reverse tunnel, writing output to a temp file to avoid pipe buffering."""
    global public_url, tunnel_proc
    with open(log_path, 'w') as out:
        tunnel_proc = subprocess.Popen(
            [
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=30",
                "-R", f"80:localhost:{PORT}",
                "nokey@localhost.run"
            ],
            stdout=out,
            stderr=subprocess.STDOUT
        )

    # Now tail the file for the URL
    with open(log_path, 'r') as f:
        waited = 0
        while waited < 30:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                waited += 0.5
                continue
            match = re.search(r'https://[a-zA-Z0-9]+\.lhr\.life', line)
            if match:
                public_url = match.group(0)
                os.environ["BASE_URL"] = public_url
                import config as _cfg
                _cfg.BASE_URL = public_url

                print(f"\n{'='*60}")
                print(f"  🌐 PUBLIC URL  →  {public_url}")
                print(f"  Share this URL with anyone for testing.")
                print(f"{'='*60}")
                print(f"  Admin Dashboard → {public_url}/")
                print(f"  Candidates receive interview links by email.")
                print(f"\n  Press Ctrl+C to stop.\n")
                sys.stdout.flush()
                break


print("\n🔌 Opening public tunnel via localhost.run (no signup needed)…")
sys.stdout.flush()

# Start tunnel thread
thread = threading.Thread(target=_start_tunnel, daemon=True)
thread.start()

# Give SSH time to connect before uvicorn starts
time.sleep(5)

import uvicorn

try:
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
except KeyboardInterrupt:
    pass
finally:
    if tunnel_proc:
        tunnel_proc.terminate()
    try:
        os.unlink(log_path)
    except Exception:
        pass
    print("\n⏹  Tunnel closed.")
