"""Doodle2Design's build-free, cross-platform local launcher."""
import hashlib
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent


def choose_port():
    for port in (8000, 8001):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Ports 8000 and 8001 are busy. Close the other server and try again.")


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError("Doodle2Design needs Python 3.10 or newer.")
    os.chdir(ROOT)
    env_dir = ROOT / ".venv"
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Creating local Python environment...", flush=True)
        venv.create(env_dir, with_pip=True)
    requirements = ROOT / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = env_dir / ".installed"
    if not marker.exists() or marker.read_text().strip() != digest:
        print("Installing dependencies (first run or updated requirements)...", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
        marker.write_text(digest)
    if not (ROOT / ".env").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
        print("Offline mode is ready. Add an Anthropic key in .env to use the vision model.", flush=True)
    subprocess.run([str(python), "scripts/build_manifest.py"], check=True)
    port = choose_port()
    url = f"http://localhost:{port}"
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {}
    process = subprocess.Popen([str(python), "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)], **options)
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError("The server stopped before becoming ready. See its error above.")
            try:
                with urllib.request.urlopen(f"{url}/healthz", timeout=0.2) as response:
                    if response.status == 200:
                        break
            except (OSError, TimeoutError):
                time.sleep(0.25)
        else:
            raise RuntimeError("Server did not become ready within 20 seconds.")
        print(f"\nDoodle2Design is running at {url}\nPress Ctrl+C to stop.", flush=True)
        if os.getenv("VIBE_NO_BROWSER") != "1":
            webbrowser.open(url)
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping Doodle2Design...", flush=True)
    finally:
        if process.poll() is None:
            if os.name == "nt":
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"\nCould not start Doodle2Design: {error}", file=sys.stderr)
        sys.exit(1)
