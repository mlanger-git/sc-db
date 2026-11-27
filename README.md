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

## Selbstaktualisierung (ohne Container-Neustart)
Der Container startet über `app/start.py`. Das Programm fragt bei jedem Durchlauf (alle 3 Stunden) bei GitHub nach dem neuesten
Commit von `main`. Gibt es einen neuen, lädt `app/selfupdate.py` den Ordner `app/`, prüft ihn (Pflichtdateien, Syntax) und legt ihn
nach `data/app_live/code`. Danach beendet sich nur das Python-Programm (Exit-Code 75), `start.py` startet es mit dem neuen Code
neu, der Container selbst läuft durch. Dadurch entfällt die nächtliche Aufgabe im Aufgabenplaner und damit die DSM-Meldung
„Dienst unerwartet beendet“.
- Stürzt nachgeladener Code in den ersten 3 Minuten ab, wird er in `data/app_live/BAD` vermerkt und der im Image eingebaute Code
  weiterverwendet; der defekte Stand wird nicht erneut geladen, erst ein neuer Commit.
- Wird das Image neu gebaut, wird nachgeladener Code verworfen (der Image-Code ist dann der aktuelle).
- Ändern sich `Dockerfile` oder `requirements.txt`, ist ein Image-Neubau nötig (einmal `sc-db aktualisieren` ausführen);
  das steht im Protokoll („Image-Neubau nötig“) und wird nicht automatisch eingespielt.
- Abschalten: Umgebungsvariable `SELFUPDATE=0`. Anderes Repository/Branch: `SELFUPDATE_REPO`, `SELFUPDATE_BRANCH`.
- Im Protokoll steht beim Start `Code-Stand: <Commit>` (oder `image`).

## Frachtrechner
`app/uex.py` holt Terminals, Waren und Verkaufspreise von UEX Corp (Stanton, Pyro, Nyx; kein Token nötig) in die
Tabellen `uex_*`, `app/tradepage.py` erzeugt daraus `SC_Frachtrechner.html`. Die Preise werden alle
`TRADE_INTERVAL_HOURS` (Standard 3) aktualisiert, alles andere weiterhin alle `UPDATE_INTERVAL_HOURS`.
Kachel für `index.php`: `kachel_frachtrechner.html`.

### Entfernungen, Reisezeit und Startpunkt
Die Seite fragt einen Startpunkt (Himmelskörper oder Ort), Streckenkosten (aUEC je Gigameter) und ein Optimierungsziel ab:
Gewinn je Stunde (Standard), Netto-Erlös oder kürzeste Zeit. Beim Netto-Erlös gelten Routen bis 5 % unter dem besten Erlös
(einstellbar unter „Zeit-Annahmen“) als gleichwertig, dann gewinnt die kürzere, damit keine langen Umwege für ein paar tausend aUEC
empfohlen werden. Terminals, die UEX mit voller Lagerstufe (7) meldet, werden nicht ausgeschlossen, sondern mit dem Hinweis
„laut UEX Lager voll, evtl. keine Nachfrage“ angezeigt, weil UEX dem Spiel oft hinterherhinkt. Sie zeigt Alternativen mit 1 bis 3 Stopps und zusätzlich den
besten Plan nach dem gewählten Ziel, jeweils mit Reihenfolge, Teilstrecken (Gm) und geschätzter Reisezeit.
Die Reihenfolge der Stopps hat erst die wenigsten Systemwechsel (Stopps im selben System werden zusammen angefahren),
dann die kürzeste Zeit.

Systemwechsel laufen über die Gateway-Stationen (UEX-Terminals wie "Pyro Gateway (Stanton)", erkannt am Muster
`<Ziel> Gateway (<Quellsystem>)`): Weg zum Gateway im Startsystem, Sprungtunnel, Weg vom Gateway im Zielsystem zum Stopp.
Die Gateways werden auch ohne Verkaufspreise als Ort geführt, damit ihre Entfernungen geladen werden (`uex.place_reps`).

Die Zeit ist eine grobe Schätzung: Entfernung / Quantum-Geschwindigkeit + Spool-Zeit des Drives + Zuschlag je Flug (0,8 Min)
+ Tunnelzeit je Sprung (5 Min) + Zeit je Verkaufsstopp (5 Min); Geschwindigkeit, Zuschlag, Tunnel- und Stoppzeit sind auf der Seite
unter "Zeit-Annahmen" einstellbar (die Geschwindigkeit nur, wenn man die Reisedaten übersteuern will).
Der Sprungtunnel verbraucht Quantum Fuel (laut CIG eine feste Menge je Jump Point; eine konkrete Zahl ist nicht veröffentlicht).
Standard: 5 % des Quantum-Tanks je Tunnel (Angabe von Mark, Version 4.10.3), einstellbar unter "Zeit-Annahmen". Ohne gewähltes Schiff gilt die
mittlere Tankgröße der Schiffe. Der Wert geht in Treibstoff, Kosten (zum Quantum-Fuel-Preis), Routenbewertung und Reichweitenwarnung ein.

### Reisedaten (Quantum Drive)
Drei Stufen, auswählbar im Frachtrechner und im Browser gemerkt (`sc_fracht_v3`):
1. **Durchschnitt** (Standard): Median über alle Quantum Drives (zuletzt ca. 262 Mm/s, 6,6 s Spool, 0,0167 SCU/Gm).
2. **Mein Schiff**: der ab Werk verbaute Quantum Drive des Schiffs, dazu die Tankgröße (`quantum_fuel_capacity`).
3. **Mein Schiff mit gewähltem Quantum Drive**: genau dieser Drive, die Tankgröße bleibt die des Schiffs. Zur Auswahl stehen nur Drives in der Größe des Standard-Drives des Schiffs (andere passen nicht hinein); ist der Standard-Drive eines Schiffs unbekannt, werden alle Drives angeboten.
Streckenkosten (aUEC je Gm) = Verbrauch des Drives (SCU je Gm) x UEX-Preis für "Quantum Fuel" (`settings.qfuel_price`);
ein eingetragener Wert im Feld übersteuert das. Mit gewähltem Schiff warnt die Seite, wenn ein einzelner Flug weiter ist als
die Tankreichweite, oder wenn die ganze Route mehr Treibstoff braucht, als der Tank fasst.

Daten (`app/qdrive.py`, Star Citizen Wiki API v2):
* `quantum_drives`: alle Drives aus `items?filter[type]=QuantumDrive` (Geschwindigkeit `drive_speed` in m/s -> Mm/s,
  `quantum_fuel_requirement` = SCU je Gm, Spool, Cooldown); bei jedem Vollauf. Unplausible Einträge werden verworfen.
* `ship_qd`: Standard-Drive je Schiff aus `vehicles/<slug>?include=loadout` (rekursive Suche nach `type == QuantumDrive`).
  Diese Antwort ist rund 0,5 MB groß, deshalb höchstens `QD_PER_RUN` (80) Schiffe je Lauf, jedes Schiff nur alle
  `QD_MAX_AGE_DAYS` (7) Tage; ein Fehler wird erst am nächsten Tag wiederholt. Die erste Befüllung braucht einige Läufe
  (Loop-Modus: alle 10 Minuten, solange Schiffe offen sind). Bis dahin ist "Mein Schiff" in der Seite deaktiviert.
* `vehicles.qtank_scu`: Tankgröße aus der normalen Schiffsliste.
* Log-Zeilen: `quantum: OK - N Quantum Drives`, `quantum-schiffe: OK - N Schiffe zugeordnet, ..., M noch offen`.

Fehlt eine Entfernung, schätzt die Seite sie über bekannte dritte Orte (Dreiecksungleichung) und markiert die Etappe als "geschätzt".

Die Ortsentfernungen (UEX `terminals_distances`, innerhalb eines Systems) liegen in `uex_distances` und werden je Lauf
bis zu `UEX_DIST_PER_RUN` (Standard 500) nachgeladen, bei Fehlern oder Limit läuft ein neuer Versuch nach 10 Minuten.
Die erste Befüllung braucht deshalb mehrere Läufe; solange Paare fehlen, rechnet die Seite mit Schätzwerten.
Log-Zeile: `uex-dist: OK - N Entfernungen geladen, M offen`.

## Warenwerte
`app/valuepage.py` erzeugt `SC_Warenwerte.html` aus denselben UEX-Preisen (Median und Durchschnitt je SCU, bester Preis, Spanne,
Terminalanzahl, Alter) in zwei Ansichten: "Mining" (eine Zeile pro Mineral, Raffiniert/verkaufsfertig und Roh nebeneinander,
Schnellwahl Hand/ROC/Schiff) und "Alle Waren" (flache Liste mit Kategorie). Dazu Suche, optionale Mengenangabe und unter "Erweitert"
Systeme, Preisalter, illegale Waren und Terminals ohne Nachfrage.
Die Abbauart (Schiff, ROC, Handmining) liefert UEX nicht, sie steht in `app/mining.py` und muss bei neuen Patches nachgepflegt
werden (Quellen stehen dort im Kopf). Pfad per `VALUE_PATH`, Kachel: `kachel_warenwerte.html`.
