#!/usr/bin/env python3
"""Starts all Space Blasters servers and shuts them down cleanly on Ctrl+C."""

import subprocess
import sys
import signal
import time

SCRIPTS = ["game.py", "login.py", "score.py", "chat.py"]

def main():
    print("Starting Space Blasters servers...")
    processes = []

    for script in SCRIPTS:
        proc = subprocess.Popen([sys.executable, script])
        processes.append(proc)

    print("All servers started!")
    print("Press Ctrl+C to stop all servers.")

    def shutdown(signum, frame):
        print("\nStopping servers...")
        for proc in processes:
            proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep the main process alive while children run
    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"A server process exited unexpectedly (code {proc.returncode}). Stopping the rest...")
                    shutdown(None, None)
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()