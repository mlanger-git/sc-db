"""UEX-Corp-Daten (Waren, Terminals, Verkaufspreise) fuer den Frachtrechner.

Quelle: https://uexcorp.space/api/documentation/ (Community-Daten, Fehler moeglich).
Die benoetigten Endpunkte brauchen laut Dokumentation keinen Token; falls das UEX
spaeter aendert, kann ein Token ueber die Umgebungsvariable UEX_TOKEN gesetzt werden.
"""
import os
import time
import datetime as dt

import requests

UEX_API = os.environ.get("UEX_API", "https://api.uexcorp.uk/2.0").rstrip("/")
UEX_TOKEN = os.environ.get("UEX_TOKEN", "")
SYSTEMS = ("Stanton", "Pyro", "Nyx")
MIN_TERMINALS = 20
MIN_PRICES = 200


def _headers():
    h = {"User-Agent": "sc-price-db/1.0 (privater Gebrauch)", "Accept": "application/json"}
    if UEX_TOKEN:
        h["Authorization"] = "Bearer " + UEX_TOKEN
    return h


def fetch(resource):
    """Holt eine Ressource und gibt die Liste unter "data" zurueck (3 Versuche)."""
    last = None
    for attempt in range(3):
        try:
            r = requests.get(f"{UEX_API}/{resource}", headers=_headers(), timeout=120)
            r.raise_for_status()
            j = r.json()
            if j.get("status") != "ok":
                raise RuntimeError(f"UEX-Status '{j.get('status')}' bei {resource}")
            data = j.get("data")
            if not isinstance(data, list):
                raise RuntimeError(f"Unerwartetes Format bei {resource}")
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (attempt + 1))
    raise last


def _i(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def update(con):
    """Laedt Terminals, Waren und Verkaufspreise und ersetzt die UEX-Tabellen (nur bei Erfolg)."""
    terminals = fetch("terminals")
    commodities = fetch("commodities")
    prices = fetch("commodities_prices_all")

    term_rows = {}
    for t in terminals:
        if t.get("star_system_name") not in SYSTEMS:
            continue
        if t.get("is_player_owned"):
            continue
        if "is_available_live" in t and not _i(t.get("is_available_live")):
            continue
        term_rows[_i(t.get("id"))] = (
            _i(t.get("id")), t.get("name"), t.get("nickname"), t.get("displayname"),
            t.get("star_system_name"), t.get("planet_name"), t.get("orbit_name"), t.get("moon_name"),
            t.get("space_station_name"), t.get("city_name"), t.get("outpost_name"),
            _i(t.get("max_container_size")), _i(t.get("is_nqa")), _i(t.get("is_refinery")),
            _i(t.get("is_cargo_center")), _i(t.get("has_loading_dock")), _i(t.get("has_freight_elevator")))
    if len(term_rows) < MIN_TERMINALS:
        raise RuntimeError(f"Nur {len(term_rows)} Terminals in {', '.join(SYSTEMS)} erhalten, das ist ungewoehnlich wenig")

    com_rows = {
        _i(c.get("id")): (_i(c.get("id")), c.get("name"), c.get("code"), c.get("kind"),
                          _i(c.get("is_illegal")), _i(c.get("is_raw")), _f(c.get("weight_scu")))
        for c in commodities if c.get("id") and c.get("name")}

    price_rows = []
    for p in prices:
        tid, cid = _i(p.get("id_terminal")), _i(p.get("id_commodity"))
        if tid not in term_rows or cid not in com_rows:
            continue
        if _f(p.get("price_sell")) <= 0:
            continue
        price_rows.append((tid, cid, _f(p.get("price_sell")), _f(p.get("price_sell_avg")),
                           _f(p.get("scu_sell")), _f(p.get("scu_sell_avg")), _f(p.get("scu_sell_stock")),
                           _i(p.get("status_sell")), p.get("container_sizes"), _i(p.get("date_modified"))))
    if len(price_rows) < MIN_PRICES:
        raise RuntimeError(f"Nur {len(price_rows)} Verkaufspreise erhalten, das ist ungewoehnlich wenig")

    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with con:
        con.execute("DELETE FROM uex_terminals")
        con.execute("DELETE FROM uex_commodities")
        con.execute("DELETE FROM uex_prices")
        con.executemany("INSERT INTO uex_terminals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", term_rows.values())
        con.executemany("INSERT INTO uex_commodities VALUES (?,?,?,?,?,?,?)", com_rows.values())
        con.executemany("INSERT INTO uex_prices VALUES (?,?,?,?,?,?,?,?,?,?)", price_rows)
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES ('uex_updated_at', ?)", (ts,))
    return f"{len(term_rows)} Terminals, {len(com_rows)} Waren, {len(price_rows)} Verkaufspreise"
