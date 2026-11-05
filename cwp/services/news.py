"""
cwp.services.news — collecte des actualités (Google Actualités RSS) et résumé extractif.

Chaque article porte sa langue (`lang` = fr / en), ce qui permet de fusionner les versions
française et anglaise d'un même fait (cwp.core.dedup) au lieu de les afficher deux fois.
"""
from __future__ import annotations

import re
import time
from urllib.parse import quote_plus

import feedparser
import requests
import streamlit as st

from cwp.core.classify import clean


def gnews(q: str, lang: str = "fr") -> str:
    return (f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={lang}"
            f"&gl={'FR' if lang == 'fr' else 'US'}&ceid={'FR:fr' if lang == 'fr' else 'US:en'}")


# Thèmes de veille : une requête par langue
THEMES = {
    "Sanctions": [("sanctions OFAC OR \"gel des avoirs\" OR \"paquet de sanctions\"", "fr"),
                  ("OFAC sanctions designations", "en")],
    "Embargos": [("embargo OR \"contrôle des exportations\" OR \"double usage\"", "fr"),
                 ("export controls embargo BIS", "en")],
    "LCB-FT / AMLA": [("AMLA autorité européenne blanchiment OR AMLR OR \"LCB-FT\"", "fr"),
                      ("AMLA anti-money laundering authority EU", "en")],
    "GAFI / FATF": [("GAFI liste grise OR FATF grey list", "fr"), ("FATF plenary grey list", "en")],
    "Régulateurs (ACPR/AMF/EBA)": [("ACPR sanction OR AMF sanction conformité", "fr"),
                                   ("EBA ESMA guidelines compliance", "en")],
    "Anticorruption / ESG": [("Sapin II AFA OR corruption OR CSDDD OR CSRD", "fr"), ("FCPA enforcement", "en")],
    "Crypto / DORA / MiCA": [("MiCA OR DORA OR \"travel rule\" crypto conformité", "fr")],
}

# Requêtes ciblées sur des mesures effectivement prononcées (page d'accueil)
ACTION_FEEDS = {
    "Sanctions": [("\"impose des sanctions\" OR \"nouvelles sanctions\" OR \"paquet de sanctions\" adopté", "fr"),
                  ("OFAC designates OR \"imposes sanctions\" OR \"sanctions on\"", "en"),
                  ("\"gel des avoirs\" OR \"asset freeze\" OR \"assets frozen\"", "fr"),
                  ("OFSI OR \"EU Council\" sanctions adopted listing", "en")],
    "Régulateurs (ACPR/AMF/EBA)": [("ACPR \"commission des sanctions\" amende OR blâme", "fr"),
                                   ("AMF \"commission des sanctions\" amende", "fr"),
                                   ("fined million anti-money laundering OR AML failings", "en"),
                                   ("FinCEN OR OFAC settlement penalty million", "en")],
    "Embargos": [("embargo imposé OR \"interdiction d'exportation\" OR \"contrôles à l'exportation\" annonce", "fr"),
                 ("BIS \"entity list\" adds OR \"export ban\" imposed", "en")],
    "GAFI / FATF": [("GAFI ajoute OR retire \"liste grise\"", "fr"), ("FATF adds OR removes grey list", "en")],
}


def parse_feed(url: str, theme: str, lang: str, limit: int, seen: set, **extra) -> list[dict]:
    """Lit un flux RSS et renvoie les articles normalisés (liens déjà vus ignorés)."""
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    out = []
    for e in feed.entries[:limit]:
        link = e.get("link")
        if not link or link in seen:
            continue
        seen.add(link)
        ts = time.mktime(e.get("published_parsed")) if e.get("published_parsed") else 0
        src = (e.get("source") or {}).get("title", "") if isinstance(e.get("source"), dict) else ""
        out.append(dict(theme=theme, title=clean(e.get("title"), 160), desc=clean(e.get("summary")),
                        link=link, ts=ts, source=src, lang=lang, **extra))
    return out


@st.cache_data(ttl=900, show_spinner=False)
def fetch_all() -> list[dict]:
    items, seen = [], set()
    for theme, qs in THEMES.items():
        for q, lang in qs:
            items += parse_feed(gnews(q, lang), theme, lang, 12, seen)
    return sorted(items, key=lambda x: x["ts"], reverse=True)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_actions() -> list[dict]:
    """Flux ciblés sanctions/embargos, plus profonds (30 articles par requête) pour remonter dans le temps."""
    out, seen = [], set()
    for theme, qs in ACTION_FEEDS.items():
        for q, lang in qs:
            out += parse_feed(gnews(q, lang), theme, lang, 30, seen)
    return out


def summarize(url: str, n: int = 3) -> str:
    """Résumé extractif (sans LLM) : phrases les plus riches en mots fréquents."""
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        txt = re.sub(r"(?is)<(script|style|nav|footer).*?</\1>", " ", r.text)
        txt = clean(txt, 20000)
    except Exception:
        return "Résumé indisponible (page inaccessible ou redirection Google News)."
    sents = [x for x in re.split(r"(?<=[.!?])\s+", txt) if 50 < len(x) < 300]
    words = re.findall(r"\w{5,}", txt.lower())
    freq = {w: words.count(w) for w in set(words)}
    scored = sorted(sents, key=lambda x: -sum(freq.get(w, 0) for w in re.findall(r"\w{5,}", x.lower())) / (len(x) ** 0.5))
    return " ".join(scored[:n]) or "Résumé indisponible."


def archive(items: list[dict]) -> dict:
    """Archive les articles dans data/actualites.csv. Les versions FR / EN d'une même information
    partagent le même « groupe », pour n'être comptées qu'une fois dans les statistiques."""
    from cwp.core import dedup
    from cwp.core.classify import enrich
    from cwp.data.sources import _uid, persist_actualites
    rows = [enrich(i) for i in items]
    groups = {}
    for r in dedup.merge(rows, "fr"):
        g = _uid(r["link"])
        groups[r["link"]] = g
        for v in r.get("versions", []):
            groups[v["link"]] = g
    return persist_actualites([dict(r, groupe=groups.get(r["link"], "")) for r in rows])
