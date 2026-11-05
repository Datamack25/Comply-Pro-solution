"""
cwp.core.dedup — fusion des doublons, y compris d'une langue à l'autre.

Problème corrigé : la veille interroge Google Actualités en français ET en anglais ; un même fait
(« L'UE sanctionne Rosneft » / « EU sanctions Rosneft ») apparaissait donc deux fois, avec deux
entités, deux libellés de mesure, parfois deux pays.

Méthode (sans IA, déterministe) :
  1. empreinte de chaque article, indépendante de la langue :
       • noms propres et sigles du titre (Rosneft, Viv Ansanm, IRGC…), qui ne se traduisent pas ;
       • pays cités (codes ISO, identiques en FR et en EN) ;
       • montants et nombres (« 5 millions $ » = « $5 million » ; « 20e paquet » = « 20th package ») ;
       • notions clés traduites dans un lexique commun (gel ↔ freeze, amende ↔ fine, pétrole ↔ oil…) ;
  2. deux articles sont un même fait si : publiés à moins de 4 jours d'intervalle, pays compatibles,
     et empreintes assez proches (ou même entité + même type de mesure) ;
  3. un seul article est affiché par fait : la langue choisie par l'utilisateur d'abord (français par
     défaut), puis le média le plus crédible ; les autres versions restent accessibles (« aussi en EN »).
"""
from __future__ import annotations

import re
from collections import Counter

from . import geo
from .classify import _STOP as _CSTOP
from .classify import detect_amount, source_rank

WINDOW_S = 4 * 86400
THRESHOLD = 0.34

# Notions clés FR / EN → identifiant commun
LEXICON = {
    "sanction": ["sanction", "sanctions", "sanctionne", "sanctionnent", "sanctionnes", "sanctioned", "sanctioning",
                 "designe", "designes", "designates", "designated", "designation", "designations"],
    "freeze": ["gel", "gele", "geles", "freeze", "freezes", "frozen", "froze"],
    "assets": ["avoirs", "actifs", "assets"],
    "fine": ["amende", "amendes", "fined", "fine", "fines", "penalty", "penalite", "settlement"],
    "embargo": ["embargo", "embargos", "embargoes"],
    "export": ["export", "exports", "exportation", "exportations"],
    "package": ["paquet", "package"],
    "list": ["liste", "list", "listed", "inscrit", "inscrits", "inscription"],
    "grey": ["grise", "grey", "gray"],
    "black": ["noire", "black"],
    "add": ["ajoute", "ajoutes", "adds", "added"],
    "remove": ["retire", "retires", "removes", "removed", "radie", "delisted", "delist", "sort"],
    "oil": ["petrole", "petroliers", "petrolier", "oil", "crude", "brut"],
    "tanker": ["tanker", "tankers", "navire", "navires", "vessel", "vessels", "ship", "ships", "flotte", "fleet"],
    "gold": ["aurifere", "gold"],
    "arms": ["armes", "arms", "weapons", "armement"],
    "drug": ["drogue", "drogues", "stupefiants", "drug", "drugs", "narcotics", "fentanyl", "cocaine", "narcotrafic"],
    "gang": ["gang", "gangs", "cartel", "cartels"],
    "terror": ["terroriste", "terroristes", "terrorisme", "terrorist", "terrorists", "terrorism", "fto", "sdgt"],
    "launder": ["blanchiment", "blanchi", "laundering", "launder", "laundered"],
    "corruption": ["corruption", "corrompu", "bribery", "bribe", "pots-de-vin"],
    "fraud": ["fraude", "escroquerie", "fraud", "scam"],
    "bank": ["banque", "banques", "bank", "banks", "bancaire", "banking"],
    "crypto": ["crypto", "cryptomonnaie", "cryptomonnaies", "cryptocurrency", "bitcoin", "stablecoin", "exchange", "plateforme"],
    "network": ["reseau", "reseaux", "network", "networks"],
    "company": ["societe", "societes", "entreprise", "entreprises", "company", "companies", "firm", "firms", "entities", "entites"],
    "official": ["responsable", "responsables", "officials", "official", "dirigeant", "dirigeants", "leaders", "leader"],
    "oligarch": ["oligarque", "oligarques", "oligarch", "oligarchs"],
    "minister": ["ministre", "ministres", "minister", "ministers"],
    "bank_central": ["banque centrale", "central bank"],
    "indict": ["inculpe", "inculpes", "indicted", "charged", "poursuivi", "poursuivis", "accuse"],
    "arrest": ["arrete", "arretes", "arrested", "interpelle", "interpelles", "arrestation", "arrest"],
    "convict": ["condamne", "condamnes", "convicted", "sentenced"],
    "extend": ["prolonge", "prolongent", "renouvelle", "extends", "extended", "renews", "renewed"],
    "investigation": ["enquete", "investigation", "probe"],
    "regulation": ["reglement", "directive", "regulation", "rules", "regles", "lignes", "guidelines"],
    "refinery": ["raffinerie", "raffineries", "refinery", "refineries"],
    "shadow": ["fantome", "shadow"],
    "sector": ["secteur", "sector"],
}
# Notions présentes dans presque toutes les actualités de sanctions : elles ne suffisent pas à rapprocher deux faits
_WEAK = {"k:sanction", "k:list", "k:company", "k:official", "k:bank", "k:regulation", "k:network", "k:assets"}
_LEX = {w: k for k, ws in LEXICON.items() for w in ws}
# Les sigles d'autorités ne différencient pas deux faits (ils sont présents partout) : poids réduit
_GENERIC = {"ofac", "ue", "eu", "us", "uk", "onu", "un", "gafi", "fatf", "treasury", "tresor", "acpr", "amf", "amla",
            "doj", "sec", "fincen", "ofsi", "fca"}
_STOP = set("""le la les l un une des du de d au aux et en a sur pour par avec dans selon apres avant contre vers
ce cette ces il elle ils elles on nous est sont sera plus moins nouveau nouvelle nouveaux nouvelles son sa ses leur leurs
the a an of and to in on for with by at from as is are be will its his her their new over under amid after into about
says said announces announce annonce selon""".split())


def _tokens(text: str) -> list[str]:
    return [w for w in geo.norm(text).replace(".", " ").split() if w]


def fingerprint(headline: str) -> dict[str, float]:
    """Empreinte pondérée d'un titre : {jeton: poids}."""
    fp: dict[str, float] = {}
    raw = str(headline or "")
    # pays (codes ISO)
    for _, c in geo.mentions(raw):
        if c not in geo.ISSUERS:
            fp[f"cc:{c}"] = 1.5
    # montants
    amt, v = detect_amount(" " + raw + " ")
    if v:
        fp[f"amt:{v:.3g}"] = 2.5
    # nombres (numéro de paquet, nombre de personnes…)
    for n in re.findall(r"\b(\d{1,4})(?:e|er|ème|eme|st|nd|rd|th)?\b", raw):
        if not (1900 <= int(n) <= 2100):
            fp[f"n:{int(n)}"] = 1.0
    # noms propres et sigles : mots à majuscule non initiaux ou sigles
    words = re.findall(r"[A-Za-zÀ-ÿ][\w'’\-]*", raw)
    for i, w in enumerate(words):
        base = re.sub(r"['’]s$", "", w)
        nb = geo.norm(base).strip()
        if not nb or nb in _STOP or nb in _LEX or len(nb) < 3:
            continue
        if base.isupper() and len(base) >= 2:
            fp[f"p:{nb}"] = 0.6 if nb in _GENERIC else 2.0
        elif base[:1].isupper():
            if i == 0 and (base.lower() in _CSTOP or nb in _CSTOP):
                continue                     # majuscule de début de phrase (« Les », « New »…)
            if geo.country_by_name(base) or nb in _GENERIC:
                continue
            fp[f"p:{nb}"] = 2.0
    # notions traduites
    n = geo.norm(raw)
    for phrase in ("banque centrale", "central bank"):
        if phrase in n:
            fp["k:bank_central"] = 1.2
    for w in _tokens(raw):
        k = _LEX.get(w)
        if k:
            fp[f"k:{k}"] = 0.5 if f"k:{k}" in _WEAK else 1.0
    return fp


def _specific(k: str, w: float) -> bool:
    """Jeton discriminant : nom propre, montant, nombre ou notion précise (pas un pays seul, pas « sanction »)."""
    return k.startswith(("amt:", "n:")) or (k.startswith("p:") and w >= 2) or (k.startswith("k:") and k not in _WEAK)


def similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Jaccard pondéré."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    inter = sum(min(a.get(k, 0), b.get(k, 0)) for k in keys)
    union = sum(max(a.get(k, 0), b.get(k, 0)) for k in keys)
    return inter / union if union else 0.0


def _ekey(entity: str) -> str:
    e = re.sub(r"[^a-z0-9 ]", "", geo.norm(entity))
    e = re.sub(r"\b(the|le|la|les|group|groupe|sa|inc|ltd|plc|corp|corporation|co)\b", " ", e)
    return re.sub(r"\s+", " ", e).strip()


def _family(mkey: str) -> str:
    return "restrictive" if mkey in ("gel", "sanction", "embargo") else mkey or "news"


def same_fact(r1: dict, r2: dict, fp1: dict, fp2: dict) -> bool:
    t1, t2 = r1.get("ts") or 0, r2.get("ts") or 0
    if t1 and t2 and abs(t1 - t2) > WINDOW_S:
        return False
    if r1.get("link") and r1.get("link") == r2.get("link"):
        return True                     # même article remonté par deux requêtes
    c1, c2 = r1.get("cc", ""), r2.get("cc", "")
    if c1 and c2 and c1 != c2:
        return False
    e1, e2 = _ekey(r1.get("entity", "")), _ekey(r2.get("entity", ""))
    is_country = geo.country_by_name(r1.get("entity", "")) is not None
    if e1 and e1 == e2 and not is_country and _family(r1.get("mkey", "")) == _family(r2.get("mkey", "")):
        return True     # même entité nommée (société, personne) et même type de mesure
    a1, a2 = r1.get("amount_v") or 0, r2.get("amount_v") or 0
    if a1 and a1 == a2 and c1 == c2:
        return True
    sim = similarity(fp1, fp2)
    shared = [k for k in set(fp1) & set(fp2) if _specific(k, min(fp1[k], fp2[k]))]
    if not shared:
        return False    # seuls le pays et le mot « sanction » en commun : deux faits distincts
    if sim >= THRESHOLD:
        return True
    # langues différentes : un nom propre commun suffit avec une similarité plus faible
    if r1.get("lang") != r2.get("lang") and any(k.startswith("p:") for k in shared) and sim >= 0.22:
        return True
    return False


def _rank(r: dict, prefer: str) -> tuple:
    lang_pen = 0 if (r.get("lang") or prefer) == prefer else 1.5
    return (source_rank(r) + lang_pen, -(r.get("ts") or 0))


def merge(rows: list[dict], prefer: str = "fr", text_key: str = "headline") -> list[dict]:
    """Un seul élément par fait. Ajoute à chaque représentant :
       n_media (nb de médias), versions (autres articles : langue, média, lien, titre), langs (langues couvertes)."""
    if not rows:
        return []
    fps = [fingerprint(r.get(text_key) or r.get("title") or r.get("titre") or "") for r in rows]
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(len(rows)), key=lambda i: -(rows[i].get("ts") or 0))
    for a_i, i in enumerate(order):
        for j in order[a_i + 1:]:
            ti, tj = rows[i].get("ts") or 0, rows[j].get("ts") or 0
            if ti and tj and ti - tj > WINDOW_S:
                break                      # triés par date : au-delà de la fenêtre, plus aucun candidat
            if find(i) != find(j) and same_fact(rows[i], rows[j], fps[i], fps[j]):
                parent[find(j)] = find(i)
    groups: dict[int, list[int]] = {}
    for i in range(len(rows)):
        groups.setdefault(find(i), []).append(i)

    out = []
    for idx in groups.values():
        g = [rows[i] for i in idx]
        best = dict(min(g, key=lambda r: _rank(r, prefer)))
        if not best.get("amount_v"):
            withamt = [x for x in g if x.get("amount_v")]
            if withamt:
                best["amount"], best["amount_v"] = withamt[0]["amount"], withamt[0]["amount_v"]
        if not best.get("cc") and any(x.get("cc") for x in g):
            cc, country = Counter((x["cc"], x["country"]) for x in g if x.get("cc")).most_common(1)[0][0]
            best["cc"], best["country"] = cc, country
        best["n_media"] = len({x.get("source") or x.get("media") for x in g if x.get("source") or x.get("media")}) or 1
        best["versions"] = [dict(lang=x.get("lang", ""), source=x.get("source") or x.get("media") or "",
                                 link=x.get("link") or x.get("lien") or "", title=x.get(text_key) or x.get("title") or "")
                            for x in g if x is not best and (x.get("link") or x.get("lien")) != (best.get("link") or best.get("lien"))]
        best["langs"] = sorted({x.get("lang") for x in g if x.get("lang")})
        best["ts"] = max((x.get("ts") or 0) for x in g)
        out.append(best)
    return sorted(out, key=lambda r: r.get("ts") or 0, reverse=True)


def filter_lang(rows: list[dict], mode: str) -> tuple[list[dict], str]:
    """Applique le réglage de langue. Renvoie (articles, langue préférée)."""
    if mode == "en_only":
        return [r for r in rows if r.get("lang") == "en"], "en"
    if mode == "fr_only":
        return [r for r in rows if r.get("lang") == "fr"], "fr"
    return rows, ("en" if mode == "en_first" else "fr")
