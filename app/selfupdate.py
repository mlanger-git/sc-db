"""Selbstaktualisierung des Programmcodes aus GitHub, ohne den Container neu zu starten.

Laeuft nur unter start.py (SC_SUPERVISED=1). Ablauf:
  1. neuesten Commit von GitHub abfragen (ein kleiner Aufruf, ohne Anmeldung)
  2. ist er neu: Code (Ordner app/) laden, pruefen (Syntax, Pflichtdateien), nach <LIVE_DIR>/code legen
  3. Programm beendet sich mit Code 75, start.py startet es mit dem neuen Code neu - der Container laeuft weiter
Geaendert werden kann so alles in app/. Aendern sich Dockerfile oder requirements.txt, ist ein Neubau des Images noetig;
das wird im Protokoll gemeldet und nicht automatisch eingespielt.
"""
import hashlib
import io
import os
import re
import shutil
import tarfile
import tempfile
import urllib.request

REPO = os.environ.get("SELFUPDATE_REPO", "mlanger-git/sc-db")
BRANCH = os.environ.get("SELFUPDATE_BRANCH", "main")
API_URL = os.environ.get("SELFUPDATE_API", "https://api.github.com/repos/{repo}/commits/{ref}")
TAR_URL = os.environ.get("SELFUPDATE_TARBALL", "https://codeload.github.com/{repo}/tar.gz/{ref}")
LIVE_DIR = os.environ.get("LIVE_DIR", "/data/app_live")
EXIT_RESTART = 75
REQUIRED = ("updater.py", "schema.sql", "selfupdate.py")


def tree_hash(path):
    """Pruefsumme ueber alle Dateien eines Ordners (ohne __pycache__)."""
    h = hashlib.sha1()
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(root, f)
            h.update(os.path.relpath(p, path).encode())
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def read_marker(name):
    try:
        with open(os.path.join(LIVE_DIR, name), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def write_marker(name, value):
    os.makedirs(LIVE_DIR, exist_ok=True)
    with open(os.path.join(LIVE_DIR, name), "w", encoding="utf-8") as f:
        f.write(value)


def _get(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "sc-price-db/1.0 (privater Gebrauch)", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check(log):
    """True, wenn neuer Code eingespielt wurde (dann Programm mit EXIT_RESTART beenden)."""
    if os.environ.get("SC_SUPERVISED") != "1" or os.environ.get("SELFUPDATE", "1") == "0":
        return False
    try:
        latest = _get(API_URL.format(repo=REPO, ref=BRANCH), {"Accept": "application/vnd.github.sha"}, 30).decode().strip()
    except Exception as e:  # noqa: BLE001
        log(f"selfupdate: GitHub nicht erreichbar ({e}), naechster Versuch spaeter")
        return False
    if not re.fullmatch(r"[0-9a-f]{40}", latest):
        log("selfupdate: unerwartete Antwort von GitHub, uebersprungen")
        return False
    if latest == os.environ.get("SC_CODE_VERSION") or latest == read_marker("BAD"):
        return False
    try:
        data = _get(TAR_URL.format(repo=REPO, ref=latest))
        work = tempfile.mkdtemp(prefix=".new-", dir=_ensure_live())
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
                tf.extractall(work, filter="data")
            tops = [d for d in os.listdir(work) if os.path.isdir(os.path.join(work, d))]
            if len(tops) != 1:
                raise RuntimeError("unerwartete Archivstruktur")
            top = os.path.join(work, tops[0])
            app = os.path.join(top, "app")
            for need in REQUIRED:
                if not os.path.isfile(os.path.join(app, need)):
                    raise RuntimeError(f"{need} fehlt im neuen Code")
            for root, _d, files in os.walk(app):
                for f in files:
                    if f.endswith(".py"):
                        p = os.path.join(root, f)
                        with open(p, "rb") as fh:
                            compile(fh.read(), p, "exec")
            baked = os.environ.get("BAKED_DIR", "")
            old_req = os.path.join(baked, "requirements.txt")
            new_req = os.path.join(top, "requirements.txt")
            if baked and os.path.isfile(old_req) and os.path.isfile(new_req):
                if open(old_req, "rb").read() != open(new_req, "rb").read():
                    log("selfupdate: requirements.txt hat sich geaendert, Image-Neubau noetig (Aufgabe 'sc-db aktualisieren' einmal ausfuehren)")
                    return False
            code = os.path.join(LIVE_DIR, "code")
            old = os.path.join(LIVE_DIR, "code.old")
            shutil.rmtree(old, ignore_errors=True)
            if os.path.isdir(code):
                os.rename(code, old)
            shutil.copytree(app, code)
            write_marker("SHA", latest)
            write_marker("BAKED_HASH", tree_hash(baked) if baked else "")
            try:
                os.remove(os.path.join(LIVE_DIR, "BAD"))
            except OSError:
                pass
            shutil.rmtree(old, ignore_errors=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        log(f"selfupdate: Update {latest[:7]} nicht eingespielt ({e})")
        return False
    log(f"selfupdate: neuer Code {latest[:7]} geladen, Programm startet neu (Container laeuft weiter)")
    return True


def _ensure_live():
    os.makedirs(LIVE_DIR, exist_ok=True)
    return LIVE_DIR
