"""cwp.ui.state — état local de l'utilisateur : articles déjà vus, mots-clés d'alerte (fichiers JSON dans data/)."""
from __future__ import annotations

import json
import os

from cwp.config import DATA_DIR

SEEN_FILE = os.path.join(DATA_DIR, "seen_items.json")
ALERT_FILE = os.path.join(DATA_DIR, "alerts.json")


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, value):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False)
    except Exception:
        pass   # disque en lecture seule (certains hébergeurs) : l'état n'est simplement pas conservé


def load_seen() -> set:
    return set(_read(SEEN_FILE, []))


def save_seen(links: set) -> None:
    _write(SEEN_FILE, sorted(links)[-5000:])


def load_keywords() -> list[str]:
    return list(_read(ALERT_FILE, []))


def save_keywords(kws: list[str]) -> None:
    _write(ALERT_FILE, kws)
