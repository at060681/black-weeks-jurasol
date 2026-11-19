"""Liest den Bestand aus Gambio und schreibt nur die Vorratsstufe je Artikel nach vorrat.json.

Keine Stückzahl verlässt das Skript. Läuft als GitHub-Action im Repo black-weeks-jurasol.
Zugangsdaten kommen aus der Umgebung (GAMBIO_BASE_URL, GAMBIO_API_USER, GAMBIO_API_PASSWORD).
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

# Artikel, deren Bestand zählt -> Artikel, die diese Stufe anzeigen
GRUPPEN = {
    930: [930, 933, 950, 951, 952, 1151, 1152, 1153],  # Jackery SolarVault 3 Pro führt alle SV3-Pro-Sets
    974: [974],    # Jackery BP2500 Zusatzakku
    851: [851],    # Marstek Venus E 3.0
    1150: [1150],  # MOVA LumeGret A4000
}


def stufe(n: float) -> str:
    if n >= 8:
        return "gut"
    if n >= 4:
        return "knapp"
    if n >= 1:
        return "wenig"
    return "aus"


def main() -> int:
    base = os.getenv("GAMBIO_BASE_URL", "").rstrip("/")
    auth = (os.getenv("GAMBIO_API_USER"), os.getenv("GAMBIO_API_PASSWORD"))
    if not base or not auth[0]:
        print("Zugangsdaten fehlen", file=sys.stderr)
        return 1

    stufen = {}
    for quelle, anzeigen in GRUPPEN.items():
        r = requests.get(f"{base}/api.php/v2/products/{quelle}", auth=auth,
                         headers={"Accept": "application/json"}, timeout=30)
        r.raise_for_status()
        s = stufe(float(r.json().get("quantity") or 0))
        for pid in anzeigen:
            stufen[str(pid)] = s

    ziel = sys.argv[1] if len(sys.argv) > 1 else "vorrat.json"
    alt = None
    if os.path.exists(ziel):
        with open(ziel, encoding="utf-8") as f:
            alt = json.load(f).get("stufen")
    if alt == stufen:
        print("unverändert", stufen)
        return 0

    with open(ziel, "w", encoding="utf-8") as f:
        json.dump({"stand": datetime.now(timezone.utc).isoformat(timespec="minutes"), "stufen": stufen}, f, indent=1)
    print("neu", stufen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
