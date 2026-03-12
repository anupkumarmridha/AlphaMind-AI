import os
import shutil
import subprocess
import sys
import time
import webbrowser


ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "frontend")
BACKEND_APP = "backend.app:app"
BACKEND_PORT = "8000"
FRONTEND_PORT = "5173"


def find_uvicorn():
    venv_dir = os.path.join(ROOT, ".venv")
    if os.name == "nt":
        candidate = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        candidate = os.path.join(venv_dir, "bin", "uvicorn")
    if os.path.exists(candidate):
        return candidate
    return shutil.which("uvicorn")


def run():
    uvicorn_bin = find_uvicorn()
    if not uvicorn_bin:
        print("uvicorn not found. Install it with: uv pip install fastapi uvicorn")
        sys.exit(1)

    backend_cmd = [
        uvicorn_bin,
        BACKEND_APP,
        "--reload",
        "--port",
        BACKEND_PORT,
    ]
    frontend_cmd = ["npm", "run", "dev", "--", "--port", FRONTEND_PORT]

    print("Starting backend...")
    backend = subprocess.Popen(backend_cmd, cwd=ROOT)
    print("Starting frontend...")
    frontend = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)

    time.sleep(2)
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None or frontend.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    run()
