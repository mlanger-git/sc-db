#!/usr/bin/env python3
"""Starter im Container: haelt das Programm am Laufen und tauscht den Code bei Updates aus, ohne den Container zu beenden.

Gestartet wird bevorzugt der von selfupdate.py nachgeladene Code (<LIVE_DIR>/code), sonst der im Image eingebaute.
- Beendet sich das Programm mit Code 75, wird es sofort mit dem (neuen) Code neu gestartet.
- Stuerzt nachgeladener Code in den ersten 3 Minuten ab, wird er als defekt markiert und der eingebaute Code verwendet.
- Wurde das Image neu gebaut (anderer eingebauter Code), wird nachgeladener Code verworfen.
"""
import os
import signal
import subprocess
import sys
import time

BAKED = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BAKED)
import selfupdate  # noqa: E402

CRASH_WINDOW = 180
child = None
stopping = False


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] start: {msg}", flush=True)


def choose():
    code = os.path.join(selfupdate.LIVE_DIR, "code")
    sha = selfupdate.read_marker("SHA")
    if os.path.isfile(os.path.join(code, "updater.py")) and sha and sha != selfupdate.read_marker("BAD"):
        if selfupdate.read_marker("BAKED_HASH") == selfupdate.tree_hash(BAKED):
            return code, sha, True
        log("Image wurde neu gebaut, nachgeladener Code wird verworfen")
        selfupdate.write_marker("SHA", "")
    return BAKED, "image", False


def _stop(signum, _frame):
    global stopping
    stopping = True
    if child and child.poll() is None:
        child.send_signal(signal.SIGTERM)


def main():
    global child
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    args = sys.argv[1:] or ["loop"]
    while not stopping:
        folder, sha, live = choose()
        env = dict(os.environ, SC_SUPERVISED="1", SC_CODE_VERSION=sha, BAKED_DIR=BAKED, PYTHONUNBUFFERED="1")
        log(f"starte Programm, Code-Stand: {sha[:7] if live else 'Image'}")
        t0 = time.time()
        child = subprocess.Popen([sys.executable, os.path.join(folder, "updater.py"), *args], cwd=folder, env=env)
        rc = child.wait()
        if stopping:
            break
        if rc == selfupdate.EXIT_RESTART:
            continue
        if live and time.time() - t0 < CRASH_WINDOW:
            selfupdate.write_marker("BAD", sha)
            log(f"nachgeladener Code {sha[:7]} ist abgestuerzt (Code {rc}), verwende wieder den eingebauten Code")
            continue
        log(f"Programm beendet (Code {rc}), Neustart in 30 Sekunden")
        time.sleep(30)
    sys.exit(0)


if __name__ == "__main__":
    main()
