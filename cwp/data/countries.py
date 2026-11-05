"""Référentiel pays (ISO2/ISO3/noms FR-EN/régions) et normalisation des noms de pays."""
from __future__ import annotations

import os
import re
import unicodedata
from functools import lru_cache

import pandas as pd

from cwp.config import ref_path

REF_FILE = ref_path("ref_pays.csv")  # référentiel ISO 3166 versionné (data/reference/)

# Listes GAFI après la plénière du 30/10/2026 (à confirmer sur fatf-gafi.org avant usage)
GAFI_DATE = "2026-10-30"
GAFI_NOIRE = {"KP", "IR", "MM"}
GAFI_GRISE = {"AO", "BO", "BA", "CM", "HT", "IQ", "KE", "KW", "LA", "LB", "NP", "PG",
              "SS", "SY", "VE", "VN", "VG", "YE"}

# Pays visés par un régime de sanctions majeur (UE, ONU ou États-Unis) — indicatif, à revoir
REGIMES_SANCTIONS = {"RU", "BY", "IR", "KP", "SY", "CU", "VE", "MM", "AF", "IQ", "LY", "SD", "SS", "SO",
                     "YE", "ZW", "NI", "HT", "ML", "CF", "CD", "LB", "GN", "BI", "GT", "MD", "NE"}

ALIASES = {
    "russia": "RU", "russian federation": "RU", "iran": "IR", "iran islamic republic of": "IR",
    "korea north": "KP", "north korea": "KP", "democratic people s republic of korea": "KP", "dprk": "KP",
    "korea south": "KR", "south korea": "KR", "republic of korea": "KR", "syria": "SY",
    "syrian arab republic": "SY", "venezuela": "VE", "venezuela bolivarian republic of": "VE",
    "bolivia": "BO", "laos": "LA", "lao people s democratic republic": "LA", "vietnam": "VN", "viet nam": "VN",
    "burma": "MM", "myanmar": "MM", "united states": "US", "usa": "US", "united states of america": "US",
    "united kingdom": "GB", "uk": "GB", "great britain": "GB", "turkey": "TR", "turkiye": "TR",
    "congo democratic republic of the": "CD", "democratic republic of the congo": "CD", "drc": "CD",
    "congo": "CG", "republic of the congo": "CG", "cote d ivoire": "CI", "ivory coast": "CI",
    "tanzania": "TZ", "moldova": "MD", "palestinian": "PS", "palestine": "PS", "west bank": "PS", "gaza": "PS",
    "british virgin islands": "VG", "virgin islands british": "VG", "virgin islands uk": "VG",
    "us virgin islands": "VI", "virgin islands us": "VI", "virgin islands u s": "VI", "u s virgin islands": "VI",
    "iles vierges britanniques": "VG", "iles vierges americaines": "VI", "iles vierges des etats unis": "VI",
    "uae": "AE", "united arab emirates": "AE", "czech republic": "CZ", "macedonia": "MK", "north macedonia": "MK",
    "crimea": "UA", "region crimea": "UA", "crimea region of ukraine": "UA", "kosovo": "XK", "taiwan": "TW", "hong kong": "HK", "macau": "MO",
    "bosnia and herzegovina": "BA", "bosnia": "BA", "the bahamas": "BS", "bahamas": "BS", "gambia": "GM",
    "the gambia": "GM", "eswatini": "SZ", "swaziland": "SZ", "cape verde": "CV", "cabo verde": "CV",
    "micronesia": "FM", "brunei": "BN", "vatican": "VA", "holy see": "VA",
    "etats unis": "US", "royaume uni": "GB", "coree du nord": "KP", "coree du sud": "KR",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


@lru_cache(maxsize=1)
def ref() -> pd.DataFrame:
    df = pd.read_csv(REF_FILE, dtype=str, keep_default_na=False)
    df["gafi"] = df.iso2.map(lambda c: "Liste noire" if c in GAFI_NOIRE else "Liste grise" if c in GAFI_GRISE else "")
    df["regime_sanctions"] = df.iso2.isin(REGIMES_SANCTIONS)
    return df


@lru_cache(maxsize=1)
def _index() -> dict:
    idx = {}
    for _, r in ref().iterrows():
        for k in (r.nom, r.nom_en, r.iso2, r.iso3):
            idx[_norm(k)] = r.iso2
    idx.update({_norm(k): v for k, v in ALIASES.items()})
    return idx


@lru_cache(maxsize=4096)
def to_iso2(name: str) -> str:
    """Nom de pays (FR/EN, variantes OFAC/ONU/UE) ou code → ISO2 ; '' si inconnu."""
    n = _norm(name)
    if not n:
        return ""
    idx = _index()
    if n in idx:
        return idx[n]
    n2 = re.sub(r"\b(the|of|republic|islamic|federation|state|kingdom)\b", " ", n)
    n2 = re.sub(r"\s+", " ", n2).strip()
    if n2 in idx:
        return idx[n2]
    # Correspondance approchante prudente : ratio simple (pas de correspondance partielle, qui confondait
    # « Dominica » / « Dominican Republic » ou « Niger » / « Nigeria »), et noms d'au moins 5 lettres.
    if len(n) < 5:
        return ""
    try:
        from rapidfuzz import fuzz, process
        m = process.extractOne(n, [k for k in idx if len(k) >= 5], scorer=fuzz.ratio, score_cutoff=92)
        if m:
            return idx[m[0]]
    except Exception:
        pass
    return ""


def iso3(iso2: str) -> str:
    r = ref()
    m = r[r.iso2 == iso2]
    return m.iso3.iloc[0] if len(m) else ""


def nom(iso2: str) -> str:
    r = ref()
    m = r[r.iso2 == iso2]
    return m.nom.iloc[0] if len(m) else iso2


def flag_emoji(iso2: str) -> str:
    if len(iso2 or "") != 2 or not iso2.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in iso2.upper())
