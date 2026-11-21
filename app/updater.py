#!/usr/bin/env python3
"""Star Citizen Schiffspreise: haelt eine SQLite-Datenbank aktuell.

Quellen
  1. Star Citizen Wiki API    -> Schiffsdaten, USD-Preis (msrp), Status, Rolle
  2. Wiki-Seite "Purchasing ships" (ueber die MediaWiki-API) -> aUEC-Preise, Haendler
  3. EZB-Referenzkurs         -> Umrechnung USD -> EUR

Aufruf:  python updater.py once | loop | export | web | status
"""
import os
import re
import sys
import time
import sqlite3
import datetime as dt
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

DB_PATH = os.environ.get("DB_PATH", "/data/starcitizen.db")
EXPORT_PATH = os.environ.get("EXPORT_PATH", "/data/Star_Citizen_Schiffspreise.xlsx")
WEB_PATH = os.environ.get("WEB_PATH", "/web-out/SC_Schiffspreise.html")
TRADE_PATH = os.environ.get("TRADE_PATH", os.path.join(os.path.dirname(WEB_PATH), "SC_Frachtrechner.html"))
TRADE_INTERVAL_HOURS = float(os.environ.get("TRADE_INTERVAL_HOURS", "3"))
INTERVAL_HOURS = float(os.environ.get("UPDATE_INTERVAL_HOURS", "24"))
DEFAULT_VAT = os.environ.get("VAT_RATE", "0.19")

SC_API = os.environ.get("SC_API", "https://api.star-citizen.wiki/api/v2/vehicles")
WIKI_API = os.environ.get("WIKI_API", "https://starcitizen.tools/api.php")
ECB_URL = os.environ.get("ECB_URL", "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")
HEADERS = {"User-Agent": "sc-price-db/1.0 (privater Gebrauch)"}

SHOPS = ["Astro Armada", "Crusader Showroom", "New Deal", "Teach's", "Buy & Fly"]
MIN_WIKI_ROWS = 100  # darunter wird die Wiki-Tabelle als "Format geaendert" gewertet

# Allgemeine Rolle und Details aus den deutschen API-Bezeichnungen (Foci)
RMAP = {
    'Abfangjäger': ('Jäger', 'Abfangjäger'), 'Abriegelung': ('Jäger', 'Quantum-Abriegelung'),
    'Tarnkappenbomber': ('Bomber', 'Stealth'), 'Tarnkappenjäger': ('Jäger', 'Stealth'),
    'Leichter Jäger': ('Jäger', 'Leicht'), 'Mittlerer Jäger': ('Jäger', 'Mittel'),
    'Schwerer Jäger': ('Jäger', 'Schwer'), 'Schwerer Jäger, Bomber': ('Jäger', 'Schwer, auch Bomber'),
    'Bomber, Schwerer Jäger': ('Bomber', 'Auch schwerer Jäger'), 'Bomber': ('Bomber', ''),
    'Schwerer Bomber': ('Bomber', 'Schwer'), 'Beiboot Jäger': ('Jäger', 'Beiboot (Snub)'),
    'Schweres Kanonenboot': ('Kanonenboot', 'Schwer'), 'Kanonenboot': ('Kanonenboot', ''),
    'Landungsschiff': ('Landungsschiff', ''), 'Schweres Landungsschiff': ('Landungsschiff', 'Schwer'),
    'Leichter Frachter': ('Frachter', 'Leicht'), 'Mittlerer Frachter': ('Frachter', 'Mittel'),
    'Schwertransport': ('Frachter', 'Schwer'),
    'Einsteiger, Leichter Frachter': ('Frachter', 'Leicht, Einsteiger'),
    'Leichter Frachter, Einsteiger': ('Frachter', 'Leicht, Einsteiger'),
    'Fracht': ('Frachter', ''), 'Mittlerer Datentransport': ('Datentransport', 'Mittel'),
    'Großbergung': ('Bergung', 'Groß'), 'Mittlere Bergung': ('Bergung', 'Mittel'),
    'Einfache Bergung': ('Bergung', 'Leicht'), 'Einfache Bergung, Einsteiger': ('Bergung', 'Leicht, Einsteiger'),
    'Bergung': ('Bergung', 'Bergungs-/Abschleppschiff'),
    'Bergbau': ('Bergbau', ''), 'Mittlerer Bergbau': ('Bergbau', 'Mittel'),
    'Leichter Bergbau': ('Bergbau', 'Leicht'), 'Einsteiger, Leichter Bergbau': ('Bergbau', 'Leicht, Einsteiger'),
    'Pfadfinder': ('Erkundung', 'Pfadfinder'), 'Einsteiger, Pfadfinder': ('Erkundung', 'Einsteiger'),
    'Forschungsreisen': ('Erkundung', 'Expedition'), 'Einfache Forschung': ('Forschung', 'Leicht'),
    'Luxus-Reisen': ('Reisen', 'Luxus'), 'Reisen': ('Reisen', ''), 'Passagier': ('Passagier', ''),
    'Medizin': ('Medizin', ''), 'Berichterstattung': ('Berichterstattung', ''),
    'Schweres Betanken': ('Tanker', 'Schwer'), 'Leichtes Betanken': ('Tanker', 'Leicht'),
    'Rennsport': ('Rennen', ''), 'Generalist': ('Mehrzweck', 'Generalist'), 'Modular': ('Mehrzweck', 'Modular'),
    'Leichter Frachter, Mittlerer Jäger': ('Mehrzweck', 'Frachter / Mittlerer Jäger'),
    'Mittlerer Frachter, Kanonenboot': ('Mehrzweck', 'Frachter / Kanonenboot'),
    'Leichter Jäger, Einsteiger': ('Jäger', 'Leicht, Einsteiger'),
    'Luftabwehr': ('Luftabwehr', ''), 'Panzerabwehr': ('Panzerabwehr', ''),
    'Schwerer Panzer': ('Panzer', 'Schwer'), 'Leichter Panzer': ('Panzer', 'Leicht'),
    'Fregatte': ('Kapitalschiff', 'Fregatte'), 'Zerstörer': ('Kapitalschiff', 'Zerstörer'),
    'Korvette': ('Kapitalschiff', 'Korvette'), 'Leichter Träger': ('Träger', 'Leicht'),
    'Snub-Träger': ('Träger', 'Beiboot-Träger'), 'Gefecht': ('Gefechtsfahrzeug', ''),
}


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    print(f"[{now()}] {msg}", flush=True)


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


MANUFACTURERS = {"AEGS": "Aegis", "ANVL": "Anvil", "XNAA": "Aopoa", "ARGO": "Argo", "BANU": "Banu",
                 "CNOU": "Consolidated Outland", "CRUS": "Crusader", "DRAK": "Drake", "ESPR": "Esperia",
                 "GLSN": "Gallenson Tactical", "GAMA": "Gatac", "GREY": "Grey's Market", "GRIN": "Greycat",
                 "KRIG": "Kruger", "MISC": "MISC", "MRAI": "Mirai", "ORIG": "Origin", "RSI": "RSI",
                 "TMBL": "Tumbleweed"}

# Schiffe, die die API nicht kennt (USD-Preise aus aelteren Listen; wirken nur, solange die API sie nicht liefert)
NOTE_OLD = "Status: nicht geprüft; USD-Preis laut Fandom-Wiki (evtl. veraltet)"
MANUAL_SHIPS = [
    # (Name, Hersteller-Kuerzel, USD, Rolle, Sub-Kategorie, Groesse)
    ("Idris-K", "AEGS", 300, "Combat", "Frigate", "Capital"),
    ("Legionnaire", "AEGS", 120, "Combat", "Dropship", "Medium"),
    ("Nautilus", "AEGS", 725, "Combat", "Minelayer", "Large"),
    ("Vulcan", "AEGS", 200, "Support", "Repair, Refuel, Rearm", "Medium"),
    ("Crucible", "ANVL", 350, "Support", "Repair", "Large"),
    ("Merchantman", "BANU", 650, "Transport", "Heavy Freight", "Large"),
    ("Pioneer", "CNOU", 850, "Industrial", "Construction", "Large"),
    ("Genesis Starliner", "CRUS", 400, "Transport", "Passenger", "Large"),
    ("Kraken", "DRAK", 1650, "Multi-role", "Carrier", "Capital"),
    ("Kraken Privateer", "DRAK", 2000, "Multi-role", "Carrier", "Capital"),
    ("Endeavor", "MISC", 350, "Multi-role", "Modular", "Capital"),
    ("Endeavor Discovery", "MISC", 425, "Exploration", "Science", "Capital"),
    ("Endeavor Hope", "MISC", 450, "Support", "Medical", "Capital"),
    ("Hull D", "MISC", 450, "Transport", "Heavy Freight", "Capital"),
    ("Hull E", "MISC", 750, "Transport", "Heavy Freight", "Capital"),
    ("Odyssey", "MISC", 700, "Exploration", "Expedition", "Large"),
    ("Orion", "RSI", 575, "Industrial", "Capital Mining", "Capital"),
]
# SCU laut Star Citizen Wiki (starcitizen.tools, Infobox), Stand 21.11.2026; fehlende Schiffe: keine Angabe auf der Wiki-Seite
MANUAL_SCU = {"Vulcan": 12, "Crucible": 230, "Nautilus": 64, "Merchantman": 2880, "Pioneer": 1000,
              "Genesis Starliner": 300, "Kraken": 3792, "Endeavor": 500, "Hull D": 6912, "Hull E": 12288,
              "Odyssey": 252, "Orion": 384}
REMOVED_MANUAL = ["Endeavor Olympic"]  # gibt es nicht
# API-Schiffe ohne career/role: Name -> (Rolle, Sub-Kategorie)
# Schiffe, die laut Spiel schon fliegbar sind, in der API aber noch als Konzept stehen
FLIGHT_READY = {"Liberator"}
ROLE_OVERRIDES = {"Pitbull": ("Combat", ""), "Paladin": ("Combat", "Gunship")}


def en(x):
    if isinstance(x, dict):
        return x.get("en_EN") or ""
    return x or ""


ROLES = {"combat": "Combat", "destroyer": "Combat", "transporter": "Transport", "transport": "Transport",
         "exploration": "Exploration", "industrial": "Industrial", "support": "Support",
         "competition": "Competition", "racing": "Competition", "ground": "Ground",
         "multi-role": "Multi-role", "multirole": "Multi-role", "generalist": "Multi-role"}


def categorize(career, role, ground=False):
    """Rolle (offizielle RSI-Liste: Combat, Transport, Exploration, Industrial, Support, Competition,
    Ground, Multi-role) und Sub-Kategorie aus den englischen API-Feldern career und role."""
    c = (career or "").strip().lower()
    r = (role or "").strip()
    rl = r.lower()

    def has(*words):
        return any(w in rl for w in words)

    if ground or c == "ground":
        cat = "Ground"
    elif has("racing") or c == "competition":
        cat = "Competition"
    elif has("medical", "refuel"):
        cat = "Support"
    elif has("salvage", "recovery", "mining"):
        cat = "Industrial"
    elif has("pathfinder", "expedition", "science", "touring", "reporting"):
        cat = "Exploration"
    elif c in ROLES:
        cat = ROLES[c]
    elif c == "starter" or has("freight", "carrier", "passenger", "cargo", "data"):
        cat = "Transport"
    else:
        cat = ""
    sub = r.replace(" / ", ", ")
    if sub.lower() in (cat.lower(), "generalist", "transport", "combat", "support", "industrial", "ground"):
        sub = ""
    return cat, sub


def size_label(m):
    s = (en(m.get("size")) or "").strip().lower()
    names = {"small": "Small", "medium": "Medium", "large": "Large", "capital": "Capital",
             "snub": "Snub", "vehicle": "Vehicle"}
    if s in names:
        return names[s]
    if m.get("is_vehicle") or m.get("is_gravlev"):
        return "Vehicle"
    length = ((m.get("sizes") or {}).get("length")) or 0
    if length <= 12:
        return "Snub"
    if length <= 34:
        return "Small"
    if length <= 60:
        return "Medium"
    if length <= 160:
        return "Large"
    return "Capital"


def init_db(con):
    cols = {r[1] for r in con.execute("PRAGMA table_info(vehicles)")}
    if cols:
        for col in ("category", "subcategory", "size_label"):
            if col not in cols:
                con.execute(f"ALTER TABLE vehicles ADD COLUMN {col} TEXT")
        if "cargo_scu" not in cols:
            con.execute("ALTER TABLE vehicles ADD COLUMN cargo_scu REAL")
        con.commit()
    mcols = {r[1] for r in con.execute("PRAGMA table_info(manual_ships)")}
    if mcols:
        for col in ("category", "subcategory", "size_label"):
            if col not in mcols:
                con.execute(f"ALTER TABLE manual_ships ADD COLUMN {col} TEXT")
        if "cargo_scu" not in mcols:
            con.execute("ALTER TABLE manual_ships ADD COLUMN cargo_scu REAL")
        con.commit()
    schema = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema, encoding="utf-8") as f:
        con.executescript(f.read())
    con.execute("INSERT OR IGNORE INTO settings(key, value) VALUES ('vat_rate', ?)", (DEFAULT_VAT,))
    con.executemany("INSERT OR REPLACE INTO manufacturers(code, name) VALUES (?,?)", MANUFACTURERS.items())
    con.executemany(
        """INSERT INTO manual_ships(name, code, msrp_usd, note, category, subcategory, size_label, cargo_scu)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(name) DO UPDATE SET code=excluded.code, category=excluded.category,
               subcategory=excluded.subcategory, size_label=excluded.size_label, cargo_scu=excluded.cargo_scu""",
        [(n, c, p, NOTE_OLD, r, sb, g, MANUAL_SCU.get(n)) for n, c, p, r, sb, g in MANUAL_SHIPS])
    con.executemany("DELETE FROM manual_ships WHERE name = ?", [(n,) for n in REMOVED_MANUAL])
    con.commit()


def log_run(con, source, status, message=""):
    con.execute("INSERT INTO update_log(ran_at, source, status, message) VALUES (?,?,?,?)",
                (now(), source, status, message[:500]))
    con.commit()


def get(url, **kw):
    last = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, **kw)
            r.raise_for_status()
            return r
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


# --------------------------------------------------------------------------- Wechselkurs
def update_fx(con):
    root = ET.fromstring(get(ECB_URL).content)
    for cube in root.iter():
        if cube.tag.endswith("Cube") and cube.get("currency") == "USD":
            rate = float(cube.get("rate"))
            day = None
            for parent in root.iter():
                if parent.tag.endswith("Cube") and parent.get("time"):
                    day = parent.get("time")
            con.execute("INSERT OR REPLACE INTO fx(day, usd_per_eur) VALUES (?,?)",
                        (day or dt.date.today().isoformat(), rate))
            con.commit()
            return f"EZB-Kurs {rate} ({day})"
    raise RuntimeError("USD-Kurs im EZB-Feed nicht gefunden")


# --------------------------------------------------------------------------- Schiffsdaten
def loc(x):
    if isinstance(x, dict):
        return x.get("de_DE") or x.get("en_EN") or ""
    return x or ""


def update_vehicles(con):
    page, last, count = 1, 1, 0
    ts = now()
    while page <= last:
        data = get(SC_API, params={"page[size]": 100, "page[number]": page}).json()
        meta = data.get("meta") or {}
        last = int(meta.get("last_page") or last)
        items = data.get("data") or []
        if not items:
            break
        for m in items:
            slug = m.get("slug")
            if not slug:
                continue
            man = m.get("manufacturer") or {}
            foci = ", ".join(loc(f) for f in (m.get("foci") or []) if loc(f))
            role, details = RMAP.get(foci, (foci, ""))
            status = m.get("production_status")
            status = loc(status) if isinstance(status, dict) else status
            if m.get("name") in FLIGHT_READY:
                status = "Flugbereit"
            cat, sub = categorize(m.get("career"), m.get("role"), bool(m.get("is_vehicle") or m.get("is_gravlev")))
            if not cat and m.get("name") in ROLE_OVERRIDES:
                cat, sub = ROLE_OVERRIDES[m["name"]]
            size = size_label(m)
            try:
                scu = float(m.get("cargo_capacity")) if m.get("cargo_capacity") is not None else None
            except (TypeError, ValueError):
                scu = None
            msrp = m.get("msrp")
            msrp = float(msrp) if msrp not in (None, "", 0) else None
            old = con.execute("SELECT msrp_usd FROM vehicles WHERE slug=?", (slug,)).fetchone()
            if old is not None and old["msrp_usd"] != msrp and msrp is not None:
                con.execute("INSERT INTO price_history(kind,name,old_value,new_value,changed_at) VALUES ('usd',?,?,?,?)",
                            (m.get("name"), old["msrp_usd"], msrp, ts))
            con.execute(
                """INSERT INTO vehicles(slug,name,manufacturer,manufacturer_code,is_spaceship,status,career,
                                        foci,role,details,msrp_usd,updated_at,category,subcategory,size_label,cargo_scu)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(slug) DO UPDATE SET name=excluded.name, manufacturer=excluded.manufacturer,
                     manufacturer_code=excluded.manufacturer_code, is_spaceship=excluded.is_spaceship,
                     status=excluded.status, career=excluded.career, foci=excluded.foci, role=excluded.role,
                     details=excluded.details, msrp_usd=excluded.msrp_usd, updated_at=excluded.updated_at,
                     category=excluded.category, subcategory=excluded.subcategory, size_label=excluded.size_label,
                     cargo_scu=excluded.cargo_scu""",
                (slug, m.get("name"), man.get("name"), man.get("code"),
                 1 if m.get("is_spaceship") else 0, status, loc(m.get("type")) or m.get("career"),
                 foci, role, details, msrp, ts, cat, sub, size, scu))
            count += 1
        page += 1
    con.commit()
    if count < 100:
        raise RuntimeError(f"Nur {count} Fahrzeuge von der API erhalten, das ist ungewoehnlich wenig")
    return f"{count} Fahrzeuge"


# --------------------------------------------------------------------------- aUEC-Preise
def api_candidates(wiki_name):
    n = wiki_name.replace("’", "'")
    c = [n, "HM6 " + n, "MISC " + n]
    m = re.fullmatch(r"Aurora (CL|ES|LN|LX|MR|SE)", n)
    if m:
        c.append(f"Aurora Mk I {m.group(1)}")
    m = re.fullmatch(r"Constellation (Andromeda|Aquila|Phoenix|Taurus)", n)
    if m:
        c.append(f"Constellation Mk IV {m.group(1)}")
    c += {"600i Explorer": ["600i"], "85X": ["85X Limited"], "M50": ["M50 Interceptor"],
          "Ares Inferno": ["Ares Star Fighter Inferno"], "Ares Ion": ["Ares Star Fighter Ion"]}.get(n, [])
    return c


def parse_wiki_table(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        head = table.get_text(" ", strip=True)[:400]
        if "Base Price" not in head:
            continue
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td"])]
            if len(cells) < 8:
                continue
            digits = re.sub(r"\D", "", cells[2])
            if not digits:
                continue
            raw = cells[3:8]
            shops = [SHOPS[i] for i, x in enumerate(raw) if x.strip()]
            notes = []
            if any("***" in x for x in raw):
                notes.append("Teach's: Spezialversion")
            if any(x.rstrip().endswith("*") and "***" not in x for x in raw):
                notes.append("Neu in der aktuellen Alpha-Version (laut Wiki)")
            rows.append((cells[0].strip(), cells[1].replace("(replica)", "").strip(), int(digits),
                         ", ".join(shops), "; ".join(notes)))
        if rows:
            break
    return rows


def update_ingame(con):
    data = get(WIKI_API, params={"action": "parse", "page": "Purchasing_ships", "prop": "text",
                                 "format": "json", "formatversion": 2}).json()
    html = data["parse"]["text"]
    rows = parse_wiki_table(html)
    if len(rows) < MIN_WIKI_ROWS:
        raise RuntimeError(f"Wiki-Tabelle: nur {len(rows)} Zeilen gefunden (erwartet >= {MIN_WIKI_ROWS}). "
                           "Seitenformat vermutlich geaendert, Daten wurden NICHT ueberschrieben.")
    api_names = {r["name"] for r in con.execute("SELECT name FROM vehicles")}
    ts = now()
    old = {r["wiki_name"]: r["price_auec"] for r in con.execute("SELECT wiki_name, price_auec FROM ingame")}
    con.execute("DELETE FROM ingame")
    unmatched = []
    for code, name, price, shops, note in rows:
        api_name = next((c for c in api_candidates(name) if c in api_names), None)
        if api_name is None:
            unmatched.append(name)
        if name in old and old[name] != price:
            con.execute("INSERT INTO price_history(kind,name,old_value,new_value,changed_at) VALUES ('auec',?,?,?,?)",
                        (name, old[name], price, ts))
        con.execute("INSERT OR REPLACE INTO ingame(wiki_name,manufacturer_code,price_auec,shops,note,api_name,fetched_at) "
                    "VALUES (?,?,?,?,?,?,?)", (name, code, price, shops, note, api_name, ts))
    con.commit()
    msg = f"{len(rows)} Preise"
    if unmatched:
        msg += f", ohne API-Zuordnung: {', '.join(unmatched[:10])}"
    return msg


# --------------------------------------------------------------------------- Ablauf
def run_once():
    con = connect()
    init_db(con)
    import uex
    for source, fn in (("fx", update_fx), ("vehicles", update_vehicles), ("ingame", update_ingame),
                       ("uex", uex.update)):
        try:
            msg = fn(con)
            log(f"{source}: OK - {msg}")
            log_run(con, source, "ok", msg)
        except Exception as e:  # noqa: BLE001
            log(f"{source}: FEHLER - {e}")
            log_run(con, source, "fehler", str(e))
    try:
        export_xlsx(con)
    except Exception as e:  # noqa: BLE001
        log(f"export: FEHLER - {e}")
    try:
        import webpage
        n = webpage.build(con, WEB_PATH)
        log(f"Webseite: {n} Eintraege -> {WEB_PATH}")
    except Exception as e:  # noqa: BLE001
        log(f"webseite: FEHLER - {e}")
    try:
        import tradepage
        n = tradepage.build(con, TRADE_PATH)
        log(f"Frachtrechner: {n} Preise -> {TRADE_PATH}")
    except Exception as e:  # noqa: BLE001
        log(f"frachtrechner: FEHLER - {e}")
    con.close()


def run_trade():
    """Nur die UEX-Preise und den Frachtrechner aktualisieren (die Preise aendern sich stuendlich)."""
    import uex
    import tradepage
    con = connect()
    init_db(con)
    try:
        msg = uex.update(con)
        log(f"uex: OK - {msg}")
        log_run(con, "uex", "ok", msg)
    except Exception as e:  # noqa: BLE001
        log(f"uex: FEHLER - {e}")
        log_run(con, "uex", "fehler", str(e))
    try:
        n = tradepage.build(con, TRADE_PATH)
        log(f"Frachtrechner: {n} Preise -> {TRADE_PATH}")
    except Exception as e:  # noqa: BLE001
        log(f"frachtrechner: FEHLER - {e}")
    con.close()


def export_xlsx(con=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    own = con is None
    con = con or connect()
    cur = con.execute("SELECT * FROM ship_prices ORDER BY lower(hersteller), lower(schiff)")
    cols = [d[0] for d in cur.description]
    titles = {"hersteller": "Hersteller", "kuerzel": "Kürzel", "konzept": "Konzept (1=ja)", "schiff": "Schiff", "typ": "Typ", "rolle": "Rolle", "subkategorie": "Sub-Kategorie", "groesse": "Größe", "scu": "SCU",
              "status": "Status", "ingame_kaufbar": "Ingame kaufbar?",
              "preis_auec": "Ingame-Preis (aUEC)", "preis_usd": "Echtgeld (USD)",
              "preis_eur_inkl_mwst": "Echtgeld (EUR, inkl. MwSt.)", "auec_pro_eur": "aUEC pro EUR",
              "haendler": "Händler", "anmerkung": "Anmerkung"}
    wb = Workbook()
    ws = wb.active
    ws.title = "Schiffspreise"
    ws.append([titles.get(c, c) for c in cols])
    for c in ws[1]:
        c.font = Font(name="Arial", bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    for row in cur:
        ws.append(list(row))
    for i, c in enumerate(cols, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = 40 if c in ("haendler", "anmerkung") else 20
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    wb.save(EXPORT_PATH)
    log(f"Excel-Export: {EXPORT_PATH}")
    if own:
        con.close()


def status():
    con = connect()
    init_db(con)
    for r in con.execute("SELECT ran_at, source, status, message FROM update_log ORDER BY id DESC LIMIT 12"):
        print(f"{r['ran_at']}  {r['source']:9} {r['status']:7} {r['message']}")
    print("Kurs:", tuple(con.execute("SELECT day, usd_per_eur FROM fx ORDER BY day DESC LIMIT 1").fetchone() or ()))
    print("Zeilen in ship_prices:", con.execute("SELECT COUNT(*) FROM ship_prices").fetchone()[0])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "loop"
    if cmd == "once":
        run_once()
    elif cmd == "export":
        export_xlsx()
    elif cmd == "web":
        import webpage
        con = connect()
        init_db(con)
        print(webpage.build(con, WEB_PATH), "Eintraege ->", WEB_PATH)
    elif cmd == "trade":
        run_trade()
    elif cmd == "status":
        status()
    elif cmd == "loop":
        last_full = 0.0
        while True:
            if time.time() - last_full >= INTERVAL_HOURS * 3600 - 60:
                run_once()
                last_full = time.time()
            else:
                run_trade()
            log(f"naechste Preisaktualisierung in {TRADE_INTERVAL_HOURS:g} Stunden")
            time.sleep(TRADE_INTERVAL_HOURS * 3600)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
