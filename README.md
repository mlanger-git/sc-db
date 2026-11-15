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
