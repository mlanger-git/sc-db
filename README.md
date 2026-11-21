# Star Citizen Schiffspreise – Datenbank + Webseite

Ein Container (`sc-updater`) holt täglich Daten, pflegt die SQLite-Datenbank und erzeugt die Seite
`SC_Schiffspreise.html` direkt im Ordner `web/gaming/starcitizen` deines Guides.

## Installation auf der Synology (Container Manager)
1. In File Station Ordner `docker/sc-db` anlegen, den Inhalt dieses Pakets hineinkopieren
   (Dockerfile, docker-compose.yml, requirements.txt, Ordner `app`, Ordner `data`).
2. Container Manager → Projekt → Erstellen → Pfad `docker/sc-db` → vorhandene docker-compose.yml verwenden → Starten.
3. Projekt → sc-updater → Protokoll: Es sollten Zeilen `fx: OK`, `vehicles: OK`, `ingame: OK`, `Webseite: ... Eintraege` erscheinen.
4. Kachel in `index.php` ergänzen (siehe `kachel.html`).

## Befehle (im Container)
`python updater.py once | loop | export | web | status`

## Später erweitern
Neue Themen (Waffen, Missionen …) = neue Tabellen in `app/schema.sql` plus eine weitere `update_*`-Funktion
und ggf. eine weitere Seite in `app/webpage.py`. Die Datenbank bleibt dieselbe Datei `data/starcitizen.db`.

## Frachtrechner
`app/uex.py` holt Terminals, Waren und Verkaufspreise von UEX Corp (Stanton, Pyro, Nyx; kein Token nötig) in die
Tabellen `uex_*`, `app/tradepage.py` erzeugt daraus `SC_Frachtrechner.html`. Die Preise werden alle
`TRADE_INTERVAL_HOURS` (Standard 3) aktualisiert, alles andere weiterhin alle `UPDATE_INTERVAL_HOURS`.
Kachel für `index.php`: `kachel_frachtrechner.html`.

### Entfernungen und Startpunkt
Die Seite fragt einen Startpunkt (Himmelskörper oder Ort) und Streckenkosten (aUEC je Gigameter) ab. Sie wählt unter
1 bis 3 Stopps die Bündel mit dem besten Erlös abzüglich Streckenkosten und zeigt die Reihenfolge samt Teilstrecken.
Mehrere Systeme lassen sich gleichzeitig anhaken; ein Systemwechsel wird pauschal mit einem einstellbaren Gm-Wert (Standard 100) angesetzt.
Die Ortsentfernungen (UEX `terminals_distances`, innerhalb eines Systems) liegen in `uex_distances` und werden je Lauf
bis zu `UEX_DIST_PER_RUN` (Standard 500) nachgeladen, bei Fehlern oder Limit läuft ein neuer Versuch nach 10 Minuten.
Die erste Befüllung braucht deshalb mehrere Läufe; solange Paare fehlen, rechnet die Seite mit den vorhandenen
Entfernungen oder, wenn keine da sind, nur mit dem Erlös. Log-Zeile: `uex-dist: OK - N Entfernungen geladen, M offen`.

## Warenwerte
`app/valuepage.py` erzeugt `SC_Warenwerte.html` aus denselben UEX-Preisen (Median und Durchschnitt je SCU, bester Preis, Spanne,
Terminalanzahl, Alter) in zwei Ansichten: "Mining" (eine Zeile pro Mineral, Raffiniert/verkaufsfertig und Roh nebeneinander,
Schnellwahl Hand/ROC/Schiff) und "Alle Waren" (flache Liste mit Kategorie). Dazu Suche, optionale Mengenangabe und unter "Erweitert"
Systeme, Preisalter, illegale Waren und Terminals ohne Nachfrage.
Die Abbauart (Schiff, ROC, Handmining) liefert UEX nicht, sie steht in `app/mining.py` und muss bei neuen Patches nachgepflegt
werden (Quellen stehen dort im Kopf). Pfad per `VALUE_PATH`, Kachel: `kachel_warenwerte.html`.
