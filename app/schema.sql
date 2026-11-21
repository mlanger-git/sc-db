PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- EZB-Referenzkurs: wie viele USD ergibt 1 EUR
CREATE TABLE IF NOT EXISTS fx (
    day         TEXT PRIMARY KEY,
    usd_per_eur REAL NOT NULL
);

-- Stammdaten aus der Star Citizen Wiki API
CREATE TABLE IF NOT EXISTS vehicles (
    slug              TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    manufacturer      TEXT,
    manufacturer_code TEXT,
    is_spaceship      INTEGER,
    status            TEXT,
    career            TEXT,
    foci              TEXT,
    role              TEXT,
    details           TEXT,
    msrp_usd          REAL,
    updated_at        TEXT,
    category          TEXT,
    subcategory       TEXT,
    size_label        TEXT,
    cargo_scu         REAL
);
CREATE INDEX IF NOT EXISTS idx_vehicles_name ON vehicles(name);

-- Ingame-Preise (aUEC) aus der Wiki-Seite "Purchasing ships"
CREATE TABLE IF NOT EXISTS ingame (
    wiki_name         TEXT PRIMARY KEY,
    manufacturer_code TEXT,
    price_auec        INTEGER NOT NULL,
    shops             TEXT,
    note              TEXT,
    api_name          TEXT,
    fetched_at        TEXT
);

-- Jede Preisaenderung (USD, aUEC) wird hier protokolliert
CREATE TABLE IF NOT EXISTS price_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,      -- 'usd' oder 'auec'
    name       TEXT NOT NULL,
    old_value  REAL,
    new_value  REAL,
    changed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS update_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at  TEXT NOT NULL,
    source  TEXT NOT NULL,
    status  TEXT NOT NULL,
    message TEXT
);

-- Hersteller-Kuerzel -> Anzeigename (wird beim Start befuellt)
CREATE TABLE IF NOT EXISTS manufacturers (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

-- Schiffe, die in der API fehlen (Preise aus aelteren Listen, evtl. veraltet)
CREATE TABLE IF NOT EXISTS manual_ships (
    name     TEXT PRIMARY KEY,
    code     TEXT,
    msrp_usd REAL,
    note     TEXT,
    category    TEXT,
    subcategory TEXT,
    size_label  TEXT,
    cargo_scu   REAL
);

-- UEX-Daten fuer den Frachtrechner (Terminals, Waren, Verkaufspreise je Terminal; Stanton, Pyro, Nyx)
CREATE TABLE IF NOT EXISTS uex_terminals (
    id INTEGER PRIMARY KEY, name TEXT, nickname TEXT, displayname TEXT,
    star_system TEXT, planet TEXT, orbit TEXT, moon TEXT, space_station TEXT, city TEXT, outpost TEXT,
    max_container_size INTEGER, is_nqa INTEGER, is_refinery INTEGER, is_cargo_center INTEGER,
    has_loading_dock INTEGER, has_freight_elevator INTEGER
);
CREATE TABLE IF NOT EXISTS uex_commodities (
    id INTEGER PRIMARY KEY, name TEXT, code TEXT, kind TEXT, is_illegal INTEGER, is_raw INTEGER, weight_scu REAL
);
-- price_sell = Auszahlung an den Spieler je SCU; scu_sell = gemeldete Nachfrage, scu_sell_avg = Durchschnitt;
-- status_sell 7 = keine Nachfrage
CREATE TABLE IF NOT EXISTS uex_prices (
    id_terminal INTEGER, id_commodity INTEGER, price_sell REAL, price_sell_avg REAL,
    scu_sell REAL, scu_sell_avg REAL, scu_sell_stock REAL, status_sell INTEGER,
    container_sizes TEXT, date_modified INTEGER,
    PRIMARY KEY (id_terminal, id_commodity)
);

-- Entfernungen zwischen zwei Terminals (UEX-Schaetzung in Gigametern, id_a < id_b); gm NULL = keine Angabe
CREATE TABLE IF NOT EXISTS uex_distances (
    id_a INTEGER, id_b INTEGER, gm REAL, fetched_at INTEGER,
    PRIMARY KEY (id_a, id_b)
);

-- Fertige Sicht, entspricht der Excel-Liste
DROP VIEW IF EXISTS ship_prices;
CREATE VIEW ship_prices AS
WITH fxr AS (
    SELECT (SELECT usd_per_eur FROM fx ORDER BY day DESC LIMIT 1)                 AS rate,
           (SELECT CAST(value AS REAL) FROM settings WHERE key = 'vat_rate')      AS vat
),
ranked AS (
    SELECT v.*, i.wiki_name AS i_name, i.manufacturer_code AS i_code, i.price_auec AS i_price,
           i.shops AS i_shops, i.note AS i_note,
           ROW_NUMBER() OVER (PARTITION BY v.name
                              ORDER BY (i.wiki_name IS NOT NULL) DESC, v.msrp_usd DESC, v.slug) AS rn
    FROM vehicles v
    LEFT JOIN ingame i ON i.api_name = v.name
    WHERE (v.msrp_usd IS NOT NULL OR i.wiki_name IS NOT NULL)
      AND v.slug NOT LIKE '%-display'
      AND v.name NOT LIKE '%Wikelo%'
      AND v.name NOT LIKE '%PYAM%'
      AND v.name NOT LIKE '%Best In Show%'
      AND v.name NOT LIKE '%BIS%'
)
SELECT COALESCE(m.name, r.manufacturer)                                   AS hersteller,
       COALESCE(r.i_code, r.manufacturer_code)                            AS kuerzel,
       COALESCE(r.i_name, r.name)                                         AS schiff,
       CASE WHEN r.is_spaceship = 0 THEN 'Fahrzeug' ELSE 'Schiff' END     AS typ,
       r.category                                                         AS rolle,
       r.subcategory                                                      AS subkategorie,
       r.size_label                                                       AS groesse,
       r.cargo_scu                                                        AS scu,
       r.status                                                           AS status,
       CASE WHEN r.status = 'Im Konzept' AND r.i_name IS NULL THEN 1 ELSE 0 END AS konzept,
       CASE WHEN r.i_name IS NULL THEN 'Nein' ELSE 'Ja' END               AS ingame_kaufbar,
       r.i_price                                                          AS preis_auec,
       r.msrp_usd                                                         AS preis_usd,
       ROUND(r.msrp_usd / fxr.rate * (1 + fxr.vat), 2)                    AS preis_eur_inkl_mwst,
       CASE WHEN r.i_price IS NOT NULL AND r.msrp_usd IS NOT NULL
            THEN ROUND(r.i_price / (r.msrp_usd / fxr.rate * (1 + fxr.vat)), 0) END AS auec_pro_eur,
       r.i_shops                                                          AS haendler,
       r.i_note                                                           AS anmerkung
FROM ranked r CROSS JOIN fxr
LEFT JOIN manufacturers m ON m.code = COALESCE(r.i_code, r.manufacturer_code)
WHERE r.rn = 1
UNION ALL
-- Schiffe nur aus der manuellen Liste (nicht in der API)
SELECT COALESCE(m.name, ms.code), ms.code, ms.name, 'Schiff', ms.category, ms.subcategory, ms.size_label, ms.cargo_scu,
       'Nicht geprüft', 1, 'Nein', NULL, ms.msrp_usd,
       ROUND(ms.msrp_usd / fxr.rate * (1 + fxr.vat), 2), NULL, NULL, ms.note
FROM manual_ships ms CROSS JOIN fxr
LEFT JOIN manufacturers m ON m.code = ms.code
WHERE NOT EXISTS (SELECT 1 FROM vehicles v WHERE v.name = ms.name)
UNION ALL
-- Eintraege der Wiki-Tabelle ohne Zuordnung zur API
SELECT COALESCE(m.name, i.manufacturer_code), i.manufacturer_code, i.wiki_name, NULL, NULL, NULL, NULL, NULL,
       NULL, 0, 'Ja', i.price_auec, NULL, NULL, NULL, i.shops, 'Keine Zuordnung zur API'
FROM ingame i
LEFT JOIN manufacturers m ON m.code = i.manufacturer_code
WHERE i.api_name IS NULL;
