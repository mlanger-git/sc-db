"""Quantum Drives fuer den Frachtrechner (Star Citizen Wiki API v2).

  * quantum_drives  - alle Quantum Drives (Geschwindigkeit, Treibstoff je Gm, Spool-Zeit); bei jedem Lauf
  * ship_qd         - welcher Quantum Drive ab Werk in welchem Schiff steckt; die Schiffsdaten mit Ausruestung
                      sind sehr gross (rund 0,5 MB je Schiff), deshalb nur wenige je Lauf und je Schiff hoechstens
                      alle QD_MAX_AGE_DAYS Tage
  * vehicles.qtank_scu - Fassungsvermoegen des Quantum-Tanks (steht schon in der normalen Schiffsliste)
"""
import os
import time
import datetime as dt

import requests

API = os.environ.get("SC_API_BASE", "https://api.star-citizen.wiki/api/v2").rstrip("/")
HEADERS = {"User-Agent": "sc-price-db/1.0 (privater Gebrauch)", "Accept": "application/json"}
QD_MAX_AGE_DAYS = int(os.environ.get("QD_MAX_AGE_DAYS", "7"))
QD_PER_RUN = int(os.environ.get("QD_PER_RUN", "80"))     # Schiffe je Lauf
QD_PAUSE = float(os.environ.get("QD_PAUSE", "1.0"))      # Sekunden zwischen zwei Schiffsabfragen
MIN_DRIVES = 20


def _get(url, params=None, timeout=120):
    last = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def _num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def parse_drive(m):
    """Eine Zeile fuer quantum_drives aus einem Eintrag der Items-Liste; None, wenn Werte fehlen oder unplausibel sind."""
    qd = m.get("quantum_drive") or {}
    sj = qd.get("standard_jump") or {}
    cls = m.get("class_name")
    speed = _num(sj.get("drive_speed"))
    fuel = _num(qd.get("quantum_fuel_requirement"))
    if not cls or not speed or fuel is None:
        return None
    speed_mms = speed / 1e6                     # m/s -> Mm/s
    if not (20 <= speed_mms <= 5000) or not (0 < fuel < 5):
        return None
    return (cls, m.get("name"), m.get("size"), m.get("grade"), m.get("class"),
            fuel, round(speed_mms, 3), _num(sj.get("spool_up_time")), _num(sj.get("cooldown_time")),
            _num(sj.get("stage_one_accel_rate")), _num(sj.get("stage_two_accel_rate")))


def update_drives(con):
    rows, page, last = {}, 1, 1
    while page <= last:
        data = _get(f"{API}/items", {"filter[type]": "QuantumDrive", "page[size]": 100, "page[number]": page})
        last = int((data.get("meta") or {}).get("last_page") or last)
        for m in data.get("data") or []:
            r = parse_drive(m)
            if r:
                rows[r[0]] = r
        page += 1
    if len(rows) < MIN_DRIVES:
        raise RuntimeError(f"Nur {len(rows)} Quantum Drives von der API erhalten, das ist ungewoehnlich wenig")
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with con:
        con.execute("DELETE FROM quantum_drives")
        con.executemany("INSERT INTO quantum_drives(class_name,name,size,grade,class,fuel_scu_per_gm,speed_mms,"
                        "spool_s,cooldown_s,accel1,accel2) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows.values())
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES ('qd_updated_at',?)", (ts,))
    return f"{len(rows)} Quantum Drives"


def find_drive(obj):
    """Sucht rekursiv den ersten Eintrag mit type == 'QuantumDrive' (Ausruestung des Schiffs); gibt (class_name, name) zurueck."""
    stack = [obj]
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            if x.get("type") == "QuantumDrive" and x.get("class_name"):
                return x["class_name"], x.get("item_name") or x.get("name")
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)
    return None


def _blocked(con):
    r = con.execute("SELECT value FROM settings WHERE key='qd_blocked_until'").fetchone()
    return bool(r and r[0] > dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def update_ship_drives(con, limit=None):
    """Holt fuer Schiffe ohne frischen Eintrag den Standard-Quantum-Drive. Gibt eine Meldung zurueck."""
    limit = QD_PER_RUN if limit is None else limit
    if _blocked(con):
        return "pausiert (zuletzt wurde kein Quantum Drive gefunden), naechster Versuch morgen"
    known = {r[0] for r in con.execute("SELECT class_name FROM quantum_drives")}
    if not known:
        return "keine Quantum Drives in der Datenbank, uebersprungen"
    cutoff = (dt.datetime.now() - dt.timedelta(days=QD_MAX_AGE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    todo = [r[0] for r in con.execute(
        """SELECT v.slug FROM vehicles v LEFT JOIN ship_qd s ON s.slug = v.slug
           WHERE v.is_spaceship = 1 AND v.slug NOT LIKE '%-display' AND v.msrp_usd IS NOT NULL
             AND (s.slug IS NULL OR s.fetched_at < ?)
           ORDER BY (s.slug IS NULL) DESC, s.fetched_at, v.slug""", (cutoff,))]
    total = len(todo)
    done = fail = nodrive = 0
    nodrive_slugs = []
    for slug in todo[:limit]:
        try:
            data = _get(f"{API}/vehicles/{slug}", {"include": "loadout"}, timeout=180)
        except Exception:  # noqa: BLE001
            fail += 1
            # nicht in jedem 10-Minuten-Lauf erneut versuchen: morgen wieder, ein vorhandener Eintrag bleibt erhalten
            retry = (dt.datetime.now() - dt.timedelta(days=max(QD_MAX_AGE_DAYS - 1, 0))).strftime("%Y-%m-%d %H:%M:%S")
            con.execute("INSERT INTO ship_qd(slug,qd_class,qd_name,fetched_at) VALUES (?,NULL,NULL,?) "
                        "ON CONFLICT(slug) DO UPDATE SET fetched_at=excluded.fetched_at", (slug, retry))
            con.commit()
            time.sleep(QD_PAUSE)
            continue
        d = find_drive(data.get("data") if isinstance(data, dict) else data)
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if d and d[0] in known:
            con.execute("INSERT OR REPLACE INTO ship_qd(slug,qd_class,qd_name,fetched_at) VALUES (?,?,?,?)", (slug, d[0], d[1], ts))
            done += 1
        else:
            nodrive_slugs.append(slug)
            nodrive += 1
        con.commit()
        time.sleep(QD_PAUSE)
    # Fand kein einziges Schiff einen Drive, ist wohl das API-Format anders: Fehler melden, nichts vermerken
    if nodrive >= 5 and done == 0:
        until = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES ('qd_blocked_until',?)", (until,))
        con.commit()
        raise RuntimeError(f"Bei {nodrive} Schiffen wurde kein Quantum Drive gefunden, API-Format geaendert?")
    # kein (bekannter) Quantum Drive: Schiff trotzdem vermerken, damit es nicht jeden Lauf neu geholt wird
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con.executemany("INSERT OR REPLACE INTO ship_qd(slug,qd_class,qd_name,fetched_at) VALUES (?,NULL,NULL,?)",
                    [(x, ts) for x in nodrive_slugs])
    con.commit()
    left = max(total - limit, 0)
    return f"{done} Schiffe zugeordnet, {nodrive} ohne Quantum Drive, {fail} Fehler (morgen neu), {left} noch offen"


def open_ships(con):
    """Anzahl Schiffe, deren Quantum Drive noch (oder wieder) geholt werden muss."""
    if _blocked(con):
        return 0
    cutoff = (dt.datetime.now() - dt.timedelta(days=QD_MAX_AGE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    return con.execute(
        """SELECT COUNT(*) FROM vehicles v LEFT JOIN ship_qd s ON s.slug = v.slug
           WHERE v.is_spaceship = 1 AND v.slug NOT LIKE '%-display' AND v.msrp_usd IS NOT NULL
             AND (s.slug IS NULL OR s.fetched_at < ?)""", (cutoff,)).fetchone()[0]
