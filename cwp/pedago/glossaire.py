"""
Glossaire unifié CWP : termes rédigés + concepts existants + 50 fraudes + termes importés de Wikipédia
(enrichissement à la demande, par catégories thématiques) + vos propres termes (import CSV).
"""
from __future__ import annotations

import random
import re
import time
import unicodedata
from urllib.parse import quote

import pandas as pd

from cwp.data import store
from cwp.data.sources import S, _uid

from .glossaire_data import terms as curated

# Catégories Wikipédia (FR) utilisées pour l'enrichissement — modifiables depuis l'interface
WIKI_CATEGORIES = {
    "Finance de marché": ["Finance de marché", "Instrument financier", "Produit dérivé", "Marché financier", "Bourse"],
    "Analyse financière": ["Analyse financière", "Comptabilité générale", "Comptabilité", "Indicateur financier", "Évaluation d'entreprise"],
    "Crédit": ["Crédit", "Risque de crédit", "Droit des sûretés"],
    "Banque & paiements": ["Banque", "Moyen de paiement", "Système de paiement", "Réglementation bancaire"],
    "LCB-FT": ["Blanchiment d'argent", "Criminalité financière", "Financement du terrorisme"],
    "Sanctions": ["Sanction internationale", "Sanction économique", "Embargo"],
    "Fraude": ["Escroquerie", "Fraude", "Usurpation d'identité", "Fraude financière"],
    "Fiscalité": ["Fiscalité", "Évasion fiscale", "Paradis fiscal", "Droit fiscal"],
    "Crypto-actifs": ["Cryptomonnaie", "Blockchain", "Finance décentralisée"],
    "Corruption": ["Corruption", "Délinquance économique et financière"],
    "Régulation": ["Régulation financière", "Autorité de régulation financière"],
    "Commerce international": ["Commerce international", "Douane"],
    "Assurance": ["Assurance"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# Sigles trop génériques pour identifier un concept unique (« Formation LCB-FT » ≠ « Responsable LCB-FT »)
_GENERIC_ACR = {"UE", "EU", "US", "UK", "LCB-FT", "OFAC", "ACPR", "TRACFIN", "GAFI", "FATF", "EBA", "KYC", "PPE", "RGPD",
                "BIS", "CSRD", "CSDDD", "IFRS", "SEPA", "TVA", "II", "III", "AMF", "ONU", "RIB", "SCT", "FATCA", "CRS"}


def _key_strict(terme: str) -> str:
    """Clé sans parenthèses ni article « Loi » : « Loi Sapin II » = « Sapin II »."""
    t = re.sub(r"\([^)]*\)", " ", str(terme or ""))
    t = re.sub(r"^\s*(la |le |les |l'|loi )", "", t.strip(), flags=re.I)
    return norm(t)


def _key_acronym(terme: str) -> str:
    """Sigle principal entre parenthèses (« Business Email Compromise (BEC) » → BEC), s'il est discriminant."""
    m = re.search(r"\(([A-Z][A-Z0-9\-]{2,9})\b", str(terme or ""))
    if not m or m.group(1) in _GENERIC_ACR:
        return ""
    return m.group(1)


def dedupe_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Fusionne les entrées qui décrivent le même concept (doublons FR / EN, variantes d'intitulé).
    La première occurrence (définition rédigée) est conservée ; les autres intitulés vont dans « aussi_appele »."""
    df = df.reset_index(drop=True).copy()
    df["cle"] = df.terme.map(norm)
    parent = list(range(len(df)))
    first = {}
    for i, t in enumerate(df.terme):
        for k in (f"n:{norm(t)}", f"s:{_key_strict(t)}", f"a:{_key_acronym(t)}"):
            if k.endswith(":"):
                continue
            if k in first:
                parent[i] = parent[first[k]]
                break
        for k in (f"n:{norm(t)}", f"s:{_key_strict(t)}", f"a:{_key_acronym(t)}"):
            if not k.endswith(":"):
                first.setdefault(k, i)
    df["_g"] = parent
    alias = df.groupby("_g").terme.apply(lambda s: " ; ".join(dict.fromkeys(x for x in s.iloc[1:] if x != s.iloc[0])))
    out = df.drop_duplicates("_g", keep="first").copy()
    out["aussi_appele"] = out["_g"].map(alias).fillna("")
    return out.drop(columns="_g")


def _existing():
    rows = [dict(r, niveau="Fondamental") for r in curated()]
    try:
        from cwp.content.concepts import load_concepts
        c = load_concepts()
        for r in c.itertuples():
            rows.append(dict(terme=r.terme, categorie=r.categorie, niveau="Approfondi", source="CWP (concepts)",
                             definition=f"{r.definition} {r.decorticage}".strip(), actualite=getattr(r, "actualite", "")))
    except Exception:
        pass
    try:
        from cwp.content.glossaire_fraudes import FRAUDES
        for f in FRAUDES:
            rows.append(dict(terme=f"{f['nom']}" + (f" ({f['alias']})" if f.get("alias") else ""), categorie=f"Fraude · {f['categorie']}",
                             niveau="Typologie", source="CWP (glossaire des fraudes)",
                             definition=f"{f['description']} Comment l'identifier : {f['identifier']} Comment la combattre : {f['combattre']}"))
    except Exception:
        pass
    return rows


def load(include_wiki=True) -> pd.DataFrame:
    rows = _existing()
    df = pd.DataFrame(rows)
    extra = []
    if include_wiki:
        w = store.load("glossaire_wiki")
        if not w.empty:
            extra.append(w.assign(niveau="Encyclopédique"))
    p = store.load("glossaire_perso")
    if not p.empty:
        extra.append(p.assign(niveau=p.get("niveau", "Personnel")))
    if extra:
        df = pd.concat([df] + extra, ignore_index=True)
    df = dedupe_terms(df)  # les définitions rédigées priment ; doublons FR / EN fusionnés
    for c in ("actualite", "lien"):
        if c not in df:
            df[c] = ""
    return df.fillna("").sort_values("terme", key=lambda s: s.map(norm)).reset_index(drop=True)


def enrich_wikipedia(categories: list[str], domaine: str, max_par_cat: int = 200, progress=None) -> dict:
    """Importe le résumé (2 phrases) des articles de catégories Wikipédia FR. Licence CC BY-SA : source citée."""
    known = set(load().cle)
    rows = []
    for i, cat in enumerate(categories):
        cont, got = {}, 0
        while got < max_par_cat:
            url = ("https://fr.wikipedia.org/w/api.php?action=query&format=json&generator=categorymembers"
                   f"&gcmtitle={quote('Catégorie:' + cat)}&gcmtype=page&gcmlimit=20&prop=extracts|info&inprop=url"
                   "&exintro=1&explaintext=1&exsentences=2&exlimit=20")
            for k, v in cont.items():
                url += f"&{k}={quote(str(v))}"
            try:
                r = S.get(url, timeout=30)
                js = r.json()
            except Exception:
                break
            for pg in (js.get("query", {}).get("pages", {}) or {}).values():
                title, ext = pg.get("title", ""), (pg.get("extract") or "").strip()
                if not ext or len(ext) < 40 or norm(title) in known or title.startswith(("Liste ", "Portail")):
                    continue
                known.add(norm(title)); got += 1
                rows.append(dict(uid=_uid("wiki", title), terme=title, categorie=domaine, definition=ext[:700],
                                 source="Wikipédia (CC BY-SA 4.0)", lien=pg.get("fullurl", ""), categorie_wiki=cat))
            if "continue" not in js:
                break
            cont = js["continue"]
            time.sleep(0.3)
        if progress:
            progress((i + 1) / len(categories), f"{cat} : {got} terme(s)")
    return store.append_rows("glossaire_wiki", rows, source="Wikipédia") if rows else dict(ajoutes=0, total=len(store.load("glossaire_wiki")))


def import_perso(df: pd.DataFrame) -> dict:
    cols = {c.lower(): c for c in df.columns}
    t, d = cols.get("terme") or df.columns[0], cols.get("definition") or df.columns[1]
    c = cols.get("categorie")
    out = pd.DataFrame(dict(terme=df[t].astype(str), definition=df[d].astype(str),
                            categorie=df[c].astype(str) if c else "Personnel", source="Import utilisateur"))
    out["uid"] = out.terme.map(lambda x: _uid("perso", x))
    return store.append_rows("glossaire_perso", out, source="import utilisateur")


def quiz(df: pd.DataFrame, n=10, categorie=None, seed=None) -> list[dict]:
    """QCM : retrouver le terme correspondant à une définition (3 distracteurs de la même catégorie)."""
    rnd = random.Random(seed)
    d = df[df.definition.str.len() > 40]
    if categorie:
        d = d[d.categorie == categorie]
    pool = d.sample(min(n, len(d)), random_state=rnd.randint(0, 10_000)) if len(d) else d
    qs = []
    for _, r in pool.iterrows():
        same = df[(df.categorie == r.categorie) & (df.terme != r.terme)]
        others = (same if len(same) >= 3 else df[df.terme != r.terme]).sample(3, random_state=rnd.randint(0, 10_000)).terme.tolist()
        opts = others + [r.terme]
        rnd.shuffle(opts)
        defin = re.sub(re.escape(r.terme.split(" (")[0]), "…", r.definition, flags=re.I)
        qs.append(dict(definition=defin[:400], options=opts, reponse=r.terme, categorie=r.categorie))
    return qs
