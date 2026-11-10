"""
cwp.services.veille_ciblee — veille à la demande par RÉGION, PAYS et TYPE D'INFORMATION.

Alimente le générateur de documents de veille (PDF / PNG / Excel au format Weekly Watch) :
  • région : Caraïbes, Amérique latine, Amérique du Nord, Europe, Afrique, Moyen-Orient, Asie, Océanie, ou monde entier ;
  • pays : un ou plusieurs, ou « tous les pays » de la région (référentiel data/reference/ref_pays.csv) ;
  • type d'information : sanctions & gels, embargos, amendes des régulateurs, listes GAFI, réglementation /
    circulaires, enquêtes & poursuites, ou toutes les actualités conformité.

Sources : Google Actualités (requêtes FR + EN par pays et par type), plus les actualités déjà collectées par la
plateforme (flux généraux, flux « mesures prononcées ») et l'historique archivé (data/actualites.csv).
Une information n'est retenue que si elle CITE un pays du périmètre (contrôle sur le titre et le résumé).
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import streamlit as st

from cwp.core import geo
from cwp.core.classify import enrich, is_action
from cwp.data import countries as CT
from cwp.services.news import gnews, parse_feed

# --------------------------------------------------------------------------- #
# Régions (construites sur le référentiel ISO : colonnes region / sous_region)
# --------------------------------------------------------------------------- #
MONDE = "🌍 Monde entier"
TOUS = "🌐 Tous les pays de la région"
REGIONS = {
    "🏝️ Caraïbes": lambda r: r.sous_region == "Caraïbes",
    "🌎 Amérique latine": lambda r: r.sous_region.isin(["Amérique centrale", "Amérique du Sud"]),
    "🇺🇸 Amérique du Nord": lambda r: r.sous_region == "Amérique du Nord",
    "🇪🇺 Europe": lambda r: r.region == "Europe",
    "🌍 Afrique": lambda r: r.region == "Afrique",
    "🕌 Moyen-Orient": lambda r: r.sous_region == "Asie de l'Ouest",
    "🌏 Asie": lambda r: (r.region == "Asie") & (r.sous_region != "Asie de l'Ouest"),
    "🌊 Océanie": lambda r: r.region == "Océanie",
}

# --------------------------------------------------------------------------- #
# Types d'information : (requête FR, requête EN, mesures retenues — cf. cwp.core.classify.MEASURES)
# --------------------------------------------------------------------------- #
TOUTES = "📰 Toutes les actualités conformité"
CATEGORIES = {
    "🎯 Sanctions & gels d'avoirs": ("sanctions OR OFAC OR \"gel des avoirs\" OR désigné",
                                     "sanctions OR OFAC OR \"asset freeze\" OR designated", {"sanction", "gel"}),
    "🚫 Embargos & contrôle des exportations": ("embargo OR \"contrôle des exportations\" OR \"double usage\" OR \"embargo sur les armes\"",
                                               "embargo OR \"export controls\" OR \"arms embargo\" OR \"dual-use\"", {"embargo"}),
    "💶 Amendes & sanctions des régulateurs": ("amende OR \"commission des sanctions\" OR pénalité blanchiment",
                                              "fined OR penalty OR settlement \"money laundering\" OR AML", {"amende"}),
    "⚠️ Listes GAFI & pays à risque": ("GAFI OR \"liste grise\" OR \"liste noire\" OR \"pays à haut risque\"",
                                       "FATF OR \"grey list\" OR \"black list\" OR \"high-risk jurisdiction\"", {"liste"}),
    "📜 Réglementation & circulaires": ("circulaire OR règlement OR directive OR \"lignes directrices\" OR loi blanchiment",
                                       "regulation OR guidance OR rule OR directive \"anti-money laundering\"", {"regle"}),
    "🔎 Enquêtes, poursuites & corruption": ("enquête OR inculpé OR condamné OR corruption OR blanchiment",
                                            "investigation OR charged OR convicted OR corruption OR \"money laundering\"", {"enquete"}),
}
CHOIX = [TOUTES] + list(CATEGORIES)
_LABEL = {m: lab for lab, (_, _, ms) in CATEGORIES.items() for m in ms}   # mesure -> type d'information
PERIODES = {"7 jours": 7, "30 jours": 30, "90 jours": 90, "6 mois": 183, "12 mois": 366}
CHUNK = 6          # pays regroupés par requête quand on couvre « tous les pays » d'une région


def court(label: str) -> str:
    """Libellé sans pictogramme (« 🎯 Sanctions & gels d'avoirs » -> « Sanctions & gels d'avoirs »)."""
    return label.split(" ", 1)[1] if " " in label and not label[:1].isalnum() else label


# --------------------------------------------------------------------------- #
# Pays
# --------------------------------------------------------------------------- #
def pays_region(region: str) -> list[tuple[str, str]]:
    """[(iso2, nom)] des pays d'une région (tous les pays si MONDE), triés par nom."""
    ref = CT.ref()
    if region in REGIONS:
        ref = ref[REGIONS[region](ref)]
    ref = ref[ref.region != "Antarctique"]
    return sorted(zip(ref.iso2, ref.nom), key=lambda x: x[1])


def _noms(iso2: str) -> tuple[str, str]:
    ref = CT.ref()
    r = ref[ref.iso2 == iso2]
    fr = r.nom.iloc[0] if len(r) else geo.NAME.get(iso2, iso2)
    en = r.nom_en.iloc[0] if len(r) else fr
    return fr, en


def _q(nom: str) -> str:
    return f"\"{nom}\"" if " " in nom or "-" in nom else nom


def _cite(r: dict, codes: set[str]) -> set[str]:
    """Pays du périmètre cités dans le titre ou le résumé."""
    text = r.get("headline", "") + " " + r.get("desc", "")
    found = {c for _, c in geo.mentions(text)} & codes
    if len(found) < len(codes):                        # pays absents du dictionnaire geo : recherche par nom
        n = geo.norm(text)
        for c in codes - found:
            fr, en = _noms(c)
            if geo.norm(fr) in n or geo.norm(en) in n:
                found.add(c)
    if r.get("cc") in codes:
        found.add(r["cc"])
    return found


# --------------------------------------------------------------------------- #
# Collecte
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=3600, show_spinner=False)
def collecter(codes: tuple[str, ...], cats: tuple[str, ...]) -> list[dict]:
    """Articles Google News pour les pays (vide = monde entier) × types d'information, FR + EN."""
    jobs = []
    for cat in cats:
        q_fr, q_en, _ = CATEGORIES[cat]
        if not codes:
            jobs += [(q_fr, "fr", cat), (q_en, "en", cat)]
            continue
        for i in range(0, len(codes), CHUNK):
            grp = codes[i:i + CHUNK]
            fr = " OR ".join(_q(_noms(c)[0]) for c in grp)
            en = " OR ".join(_q(_noms(c)[1]) for c in grp)
            jobs += [(f"({fr}) ({q_fr})", "fr", cat), (f"({en}) ({q_en})", "en", cat)]
    seen: set = set()

    def run(job):
        q, lang, cat = job
        return parse_feed(gnews(q, lang), cat, lang, 25, set())

    out = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(run, jobs):
            for it in res:
                if it["link"] not in seen:
                    seen.add(it["link"])
                    out.append(it)
    return out


def archives() -> list[dict]:
    """Historique archivé par la plateforme (data/actualites.csv), au format des articles."""
    try:
        from cwp.data import store
        df = store.load("actualites")
    except Exception:
        return []
    if df.empty:
        return []
    out = []
    for _, r in df.iterrows():
        try:
            ts = datetime.strptime(r.get("date", ""), "%Y-%m-%d %H:%M").timestamp()
        except Exception:
            ts = 0
        out.append(dict(theme=r.get("theme", ""), title=r.get("titre", ""), desc=r.get("resume", ""),
                        link=r.get("lien", ""), ts=ts, source=r.get("media", ""), lang=r.get("langue", "")))
    return [o for o in out if o["link"]]


def selectionner(raw: list[dict], codes: set[str] | None, cats: list[str], jours: int,
                 mesures_prononcees: bool = False) -> list[dict]:
    """Enrichit, garde le périmètre (pays cités), le type d'information et la période.
    codes=None => monde entier."""
    toutes = (not cats) or TOUTES in cats
    allowed = set() if toutes else set().union(*[CATEGORIES[c][2] for c in cats if c in CATEGORIES])
    since = time.time() - jours * 86400 if jours else 0
    rows, seen = [], set()
    for it in raw:
        if not it.get("link") or it["link"] in seen:
            continue
        r = enrich(it)
        if r["ts"] and r["ts"] < since:
            continue
        if codes is not None:
            cited = _cite(r, codes)
            if not cited:
                continue
            # pays VISÉ : si la détection automatique a retenu l'émetteur (États-Unis, UE…), on retient le pays cité
            if r["cc"] not in cited:
                cc = sorted(cited)[0]
                r["cc"], r["country"] = cc, _noms(cc)[0]
                if r["entity"] in ("—", "", "États-Unis", "Union européenne", "Royaume-Uni", "Canada", "ONU"):
                    r["entity"] = r["country"]
        if not toutes:
            fetched_for = it.get("theme") in cats
            if r["mkey"] not in allowed and not (fetched_for and r["mkey"] == "news"):
                continue
        if mesures_prononcees and not is_action(r):
            continue
        # colonne « Catégorie » = type d'information
        lab = _LABEL.get(r["mkey"]) or (it.get("theme") if it.get("theme") in CATEGORIES else "")
        r["theme"] = court(lab) if lab else "Actualité"
        seen.add(it["link"])
        rows.append(r)
    return sorted(rows, key=lambda x: x["ts"], reverse=True)


def statut_pays(codes: list[str]) -> pd.DataFrame:
    """Statut GAFI / régimes de sanctions des pays sélectionnés (cwp.data.countries)."""
    out = []
    for c in codes:
        gafi = ("Liste noire (contre-mesures)" if c in CT.GAFI_NOIRE
                else "Liste grise (surveillance renforcée)" if c in CT.GAFI_GRISE else "Non listé")
        out.append({"Pays": _noms(c)[0], f"GAFI ({CT.GAFI_DATE})": gafi,
                    "Régime de sanctions": "Oui" if c in CT.REGIMES_SANCTIONS else "Non connu"})
    return pd.DataFrame(out)
