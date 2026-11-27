#!/bin/sh
# Prüft, ob der Updater noch Seiten schreibt. Für den DSM-Aufgabenplaner (Benutzerdefiniertes Skript, Benutzer: root).
# Schlägt fehl (Exit 1), wenn SC_Frachtrechner.html fehlt oder älter als 7 Stunden ist; DSM meldet dann "abnormale Beendigung".
F=/volume1/web/gaming/starcitizen/SC_Frachtrechner.html
if [ -n "$(find "$F" -mmin -420 2>/dev/null)" ]; then
  echo "OK: $F ist aktuell"
  exit 0
fi
echo "FEHLER: $F fehlt oder ist älter als 7 Stunden. Container Manager -> sc-updater -> Protokoll prüfen."
exit 1
