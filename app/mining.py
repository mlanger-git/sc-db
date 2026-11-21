"""Abbauart je Rohstoff: S = Schiffs-Mining, R = ROC (Bodenfahrzeug), H = Handmining (Multitool).

UEX liefert diese Zuordnung nicht, deshalb steht sie hier und muss bei neuen Patches nachgepflegt werden.
Quelle: Community-Uebersicht starvein.app/en/ores (Methoden je Erz), gegengeprueft mit dem ROC-Guide
dystopiandynasty.org (Stand Alpha 4.10.2), scminer.rocks und citizen-starter-guide.com (Alpha 4.10).
Diamond und Inert Materials stammen aus der alten Wiki-Tabelle (PU 3.11.1, starcitizen.tools/Mineral_resources).
Ein Fragezeichen heisst: die Quellen widersprechen sich (Saldynium und Sadaryx: eine Quelle nennt nur Handmining).
Schluessel ist der Warenname ohne Zusatz wie "(Ore)", "(Raw)" oder "(Pure)".
G = ATLS GEO (Mining-Powersuit): laut CIG-Q&A (Comm-Link 20514) baut er sowohl Handmining- als auch ROC-Vorkommen ab,
also alles mit H oder R, aber keine Schiffs-Erze. Wird aus H und R abgeleitet.
"""
import re

MINING = {
    "Agricium": "S", "Aluminum": "S", "Aphorite": "H", "Aslarite": "S", "Beradom": "R", "Beryl": "S",
    "Bexalite": "S", "Borase": "S", "Carinite": "RH", "Copper": "S", "Corundum": "S", "Diamond": "S",
    "Dolivine": "H", "Feynmaline": "R", "Glacosite": "R", "Gold": "S", "Hadanite": "H", "Hephaestanite": "S",
    "Ice": "S", "Inert Materials": "SR", "Iron": "S", "Jaclium": "RH", "Janalite": "H", "Laranite": "S",
    "Lindinium": "S", "Ouratite": "S", "Quantainium": "S", "Quartz": "S", "Riccite": "S", "Sadaryx": "R?H",
    "Saldynium": "R?H", "Savrilium": "S", "Silicon": "S", "Stileron": "S", "Taranite": "S", "Tin": "S",
    "Titanium": "S", "Torite": "S", "Tungsten": "S",
}


def base_name(name):
    return re.sub(r"\s*\((Ore|Raw|Pure)\)\s*$", "", name or "", flags=re.I).strip()


def methods(name):
    """Liste der Kuerzel, z. B. ['H'] oder ['R?', 'H']."""
    code = MINING.get(base_name(name), "")
    out, i = [], 0
    while i < len(code):
        if i + 1 < len(code) and code[i + 1] == "?":
            out.append(code[i] + "?")
            i += 2
        else:
            out.append(code[i])
            i += 1
    sure = [v for v in out if v in ("H", "R")]
    unsure = [v for v in out if v in ("H?", "R?")]
    if sure:
        out.append("G")
    elif unsure:
        out.append("G?")
    return out
