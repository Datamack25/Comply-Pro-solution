"""
cwp.data.profil360 — profil d'entité « 360° » : combine les sources en ligne et toutes les données
déjà présentes sur la plateforme, puis rédige une synthèse d'analyste et recommande les trames à utiliser.

Sources en ligne ajoutées : Wikidata (fiche d'identité structurée), Wikipédia (résumé),
SEC EDGAR (données financières des sociétés cotées américaines).
Données plateforme : actualités archivées, presse négative stockée, profils antérieurs, registres
déjà consultés, PPE, risque pays, Focus Caraïbes, points OSM, typologies et méthodologies CWP.
"""
from __future__ import annotations

import os
import re
from urllib.parse import quote

import pandas as pd

from . import store
from .countries import nom as pays_nom
from .countries import to_iso2
from .sources import S, _get, _sparql
from cwp.config import ref_path



def _norm(s):
    from .screening import norm
    return norm(s)


# --------------------------------------------------------------------------- #
# En ligne : Wikidata + Wikipédia
# --------------------------------------------------------------------------- #
WD_PROPS = {
    "P31": "nature", "P17": "pays", "P27": "nationalite", "P571": "creation", "P569": "naissance", "P570": "deces",
    "P452": "secteur", "P159": "siege", "P169": "dirigeant", "P488": "president", "P127": "proprietaire",
    "P749": "societe_mere", "P355": "filiales", "P414": "bourse", "P946": "isin", "P1278": "lei",
    "P856": "site", "P106": "profession", "P39": "fonctions", "P102": "parti", "P2139": "chiffre_affaires",
    "P1128": "effectif", "P3320": "membres_conseil",
}


def wikidata_fiche(nom: str, type_: str) -> dict:
    js = _get(f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote(nom)}&language=fr&uselang=fr"
              f"&type=item&limit=7&format=json", timeout=20).json()
    cands = js.get("search", [])
    if not cands:
        return {}
    from rapidfuzz import fuzz
    best = max(cands, key=lambda c: fuzz.token_sort_ratio(_norm(c.get("label", "")), _norm(nom)))
    if fuzz.token_sort_ratio(_norm(best.get("label", "")), _norm(nom)) < 80:
        return {}
    qid = best["id"]
    vals = " ".join(f"wdt:{p}" for p in WD_PROPS)
    q = f"""SELECT ?prop (GROUP_CONCAT(DISTINCT ?vl; separator=" | ") AS ?vals) WHERE {{
  VALUES ?prop {{ {vals} }}
  wd:{qid} ?prop ?v .
  OPTIONAL {{ ?v rdfs:label ?lf . FILTER(LANG(?lf) = "fr") }}
  OPTIONAL {{ ?v rdfs:label ?le . FILTER(LANG(?le) = "en") }}
  BIND(COALESCE(?lf, ?le, STR(?v)) AS ?vl)
}} GROUP BY ?prop"""
    row = {}
    try:
        for b in _sparql(q):
            pid = b.get("prop", "").rsplit("/", 1)[-1]
            if pid in WD_PROPS:
                row[WD_PROPS[pid]] = b.get("vals", "")
    except Exception:
        pass
    fiche = {k: _dedup(v) for k, v in row.items() if v}
    for k in ("creation", "naissance", "deces"):
        if k in fiche:
            fiche[k] = fiche[k][:10]
    fiche.update(qid=qid, libelle=best.get("label", ""), description_courte=best.get("description", ""))
    try:
        title = _sparql(f"SELECT ?t WHERE {{ ?a schema:about wd:{qid}; schema:isPartOf <https://fr.wikipedia.org/>; schema:name ?t }}")[0]["t"]
        r = S.get(f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}", timeout=15)
        if r.ok:
            fiche["resume"] = r.json().get("extract", "")
            fiche["wikipedia"] = title
    except Exception:
        pass
    row = dict(uid=qid, nom=fiche.get("libelle", nom), **{k: v for k, v in fiche.items() if k not in ("qid",)})
    store.append_rows("wikidata_entites", [row], source="Wikidata / Wikipédia")
    return fiche


def _dedup(v):
    seen, out = set(), []
    for x in str(v).split(" | "):
        x = x.strip()
        if x and x.lower() not in seen and not x.startswith("http://www.wikidata.org/.well-known"):
            seen.add(x.lower()); out.append(x)
    return " | ".join(out[:12])


# --------------------------------------------------------------------------- #
# En ligne : SEC EDGAR (sociétés cotées américaines)
# --------------------------------------------------------------------------- #
def _sec_headers():
    ua = os.getenv("SEC_USER_AGENT")
    try:
        import streamlit as st
        ua = ua or st.secrets.get("SEC_USER_AGENT")
    except Exception:
        pass
    return {"User-Agent": ua or "CWP-Compliance-Watch-Platform research-tool", "Accept": "application/json"}


SEC_TAGS = {"Chiffre d'affaires": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
            "Résultat net": ["NetIncomeLoss"], "Total actif": ["Assets"], "Total passif": ["Liabilities"],
            "Capitaux propres": ["StockholdersEquity"], "Trésorerie": ["CashAndCashEquivalentsAtCarryingValue"],
            "Dette long terme": ["LongTermDebt", "LongTermDebtNoncurrent"]}


def sec_financials(nom: str) -> pd.DataFrame:
    cache = os.path.join(store.DATA_DIR, "sec_tickers.json")
    import json
    if os.path.exists(cache):
        tick = json.load(open(cache))
    else:
        tick = S.get("https://www.sec.gov/files/company_tickers.json", headers=_sec_headers(), timeout=30).json()
        json.dump(tick, open(cache, "w"))
    from rapidfuzz import fuzz, process
    names = {v["title"]: v for v in tick.values()}
    m = process.extractOne(_norm(nom), {k: _norm(k) for k in names}, scorer=fuzz.token_sort_ratio, score_cutoff=88)
    if not m:
        return pd.DataFrame()
    co = names[m[2]]
    cik = str(co["cik_str"]).zfill(10)
    facts = S.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=_sec_headers(), timeout=40).json()
    gaap = facts.get("facts", {}).get("us-gaap", {})
    rows = []
    for lab, tags in SEC_TAGS.items():
        for t in tags:
            units = gaap.get(t, {}).get("units", {}).get("USD", [])
            annual = [u for u in units if u.get("form") == "10-K" and u.get("fp") == "FY"]
            if annual:
                byy = {}
                for u in annual:
                    byy[u["fy"]] = u["val"]
                for fy in sorted(byy)[-4:]:
                    rows.append(dict(indicateur=lab, exercice=fy, valeur_usd=byy[fy]))
                break
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.pivot_table(index="indicateur", columns="exercice", values="valeur_usd", aggfunc="last").reset_index()
        df.insert(0, "societe", co["title"]); df.insert(1, "ticker", co["ticker"]); df.insert(2, "cik", cik)
        store.append_rows("sec_edgar", df.assign(uid=lambda d: d.cik + "-" + d.indicateur).astype(str), source="SEC EDGAR")
    return df


# --------------------------------------------------------------------------- #
# Données déjà présentes sur la plateforme
# --------------------------------------------------------------------------- #
def _contains(df, cols, name):
    if df.empty:
        return df
    k = _norm(name)
    mask = pd.Series(False, index=df.index)
    for c in cols:
        if c in df:
            mask |= df[c].astype(str).map(_norm).str.contains(re.escape(k), na=False)
    return df[mask]


def platform_data(p: dict) -> dict:
    nom = p["nom"]
    out = {}
    out["actualites"] = _contains(store.load("actualites"), ["entite", "titre", "resume"], nom)
    hist = store.load("entites_profils")
    out["historique"] = _contains(hist, ["nom"], nom).sort_values("date") if not hist.empty else hist
    out["presse_stockee"] = _contains(store.load("presse_negative"), ["entite", "titre"], nom)
    out["lei_stocke"] = _contains(store.load("lei_gleif"), ["nom", "parent_direct", "parent_ultime"], nom)
    out["fr_stocke"] = _contains(store.load("entreprises_fr"), ["nom", "dirigeants"], nom)
    out["osm"] = _contains(store.load("osm_poi"), ["nom", "operateur"], nom)
    out["ppe_stocke"] = _contains(store.load("ppe_wikidata"), ["nom"], nom)
    out["renseignements"] = _contains(store.load("renseignements_internes"), ["nom", "alias"], nom)
    na = store.load("notoriete_articles")
    if not na.empty:
        na = na[na.entite.map(_norm) == _norm(nom)].copy()
        na["_s"] = pd.to_numeric(na.score, errors="coerce")
        na = na.sort_values("_s", ascending=False).drop_duplicates(subset=["titre"]).drop(columns="_s")
    out["notoriete_articles"] = na
    c = p.get("pays", "")
    out["pays"] = {}
    if c:
        pr = store.load("pays_risque")
        if pr.empty:
            from .sources import build_pays_risque
            pr = build_pays_risque()
        if not pr.empty and c in set(pr.iso2):
            out["pays"] = pr[pr.iso2 == c].iloc[0].to_dict()
        fc = ref_path("focus_caraibes_pays.csv")
        if os.path.exists(fc):
            f = pd.read_csv(fc, dtype=str, keep_default_na=False)
            if c in set(f.code):
                out["focus"] = f[f.code == c].iloc[0].to_dict()
        from .sources import sanctions_consolidees
        sc = sanctions_consolidees()
        if not sc.empty:
            sub = sc[sc.pays.str.contains(rf"\b{c}\b", na=False)]
            out["regimes_pays"] = sub.programme.str.split(r" \| ").explode().value_counts().head(8)
            out["nb_inscrits_pays"] = len(sub)
        news = store.load("actualites")
        out["actualites_pays"] = news[news.pays_iso2 == c].sort_values("date", ascending=False).head(15) if not news.empty else news
    return out


# --------------------------------------------------------------------------- #
# Synthèse d'analyste et trames recommandées
# --------------------------------------------------------------------------- #
def recommandations(p: dict, plat: dict) -> list[tuple[str, str]]:
    """(id méthodologie, raison)"""
    rec = []
    add = lambda mid, why: rec.append((mid, why)) if mid not in [r[0] for r in rec] else None
    if p["meilleur_score_sanctions"] >= 80:
        add("homonymie", "correspondance sur une liste de sanctions à confirmer ou écarter")
    if p.get("pays") in {"RU", "BY", "IR", "KP", "SY", "VE", "CU", "MM"} or plat.get("nb_inscrits_pays", 0) > 200:
        add("contournement", f"pays exposé à des régimes de sanctions ({p.get('pays_nom')})")
    if p["ppe"]:
        add("ppe", "qualité de PPE détectée")
    if p["type"] == "Entité":
        add("kyc_pm", "personne morale : identifier les bénéficiaires effectifs et la chaîne de détention")
        add("analyse_fin", "apprécier la solidité financière et la cohérence des comptes")
    else:
        add("kyc_pp", "personne physique : vérifier identité et connaissance client")
    pr = p.get("presse", pd.DataFrame())
    if not pr.empty:
        cats = set(pr.categorie)
        if "Corruption" in cats: add("corruption", "presse : corruption")
        if "Fraude" in cats: add("fraude_paiement", "presse : fraude")
        if "Blanchiment" in cats: add("blanchiment", "presse : blanchiment")
        if "Sanctions" in cats: add("contournement", "presse : sanctions")
    if p.get("pays") in {"VG", "KY", "PA", "BZ", "SC", "BS", "MH", "AE", "CY", "LU"}:
        add("fraude_fiscale", "juridiction offshore ou à fiscalité privilégiée")
    if p["score"] >= 30:
        add("n2", "score de risque modéré ou élevé : examen renforcé")
    if p.get("pays") == "HT" or plat.get("focus"):
        add("blanchiment", "corridor Caraïbes : espèces, transferts et économie informelle")
    if p.get("pays_gafi") in ("Liste noire", "Liste grise"):
        add("blanchiment", f"pays sur la {p['pays_gafi'].lower()} du GAFI")
    return rec


def synthese(p: dict, plat: dict, fiche: dict) -> dict:
    nom, s = p["nom"], []
    ident = fiche.get("description_courte") or fiche.get("nature") or p["type"].lower()
    s.append(f"{nom} est identifié(e) comme {ident}" + (f", rattaché(e) à {p.get('pays_nom')}" if p.get("pays_nom") else "")
             + (f", créé(e) en {fiche['creation'][:4]}" if fiche.get("creation") else "")
             + (f", né(e) le {fiche['naissance']}" if fiche.get("naissance") else "") + ".")
    if fiche.get("secteur"):
        s.append(f"Secteur d'activité : {fiche['secteur']}.")
    if fiche.get("societe_mere") or p.get("lei_parent"):
        s.append(f"Groupe : société mère {fiche.get('societe_mere') or p.get('lei_parent')}.")
    if p["listes_touchees"]:
        s.append(f"Le filtrage relève une correspondance de {p['meilleur_score_sanctions']:.0f} % sur {len(p['listes_touchees'])} liste(s) "
                 f"({', '.join(p['listes_touchees'])}). L'identité doit être confirmée par des identifiants forts avant toute décision.")
    else:
        s.append("Aucune correspondance n'a été trouvée sur les listes de sanctions chargées dans la plateforme.")
    if p["ppe"]:
        f = p["ppe_df"].iloc[0]
        s.append(f"La personne est exposée politiquement ({f.get('fonction', f.get('programme', 'fonction publique'))})"
                 + (" et toujours en fonction." if p["ppe_en_fonction"] else "."))
    if p["nb_presse_negative"]:
        cats = p["presse"].categorie.value_counts().head(3)
        s.append(f"{p['nb_presse_negative']} article(s) de presse négative recensé(s), principalement : "
                 + ", ".join(f"{k.lower()} ({v})" for k, v in cats.items()) + ".")
    ri = plat.get("renseignements", pd.DataFrame())
    if len(ri):
        s.append(f"{len(ri)} renseignement(s) interne(s) enregistré(s) sur l'entité ({', '.join(sorted(set(ri.categorie)))}).")
    if p.get("notoriete"):
        s.append(f"Dernière recherche de notoriété négative ({p['notoriete']['date'][:10]}) : {p['notoriete']['niveau']} "
                 f"(score {p['notoriete']['score']:.0f}/100).")
    na = len(plat.get("actualites", []))
    if na:
        s.append(f"La veille CWP a archivé {na} actualité(s) mentionnant l'entité.")
    h = plat.get("historique", pd.DataFrame())
    if len(h) > 1:
        sc = pd.to_numeric(h.score, errors="coerce").dropna()
        if len(sc) > 1:
            s.append(f"L'entité a déjà été analysée {len(h)} fois ; score passé de {sc.iloc[0]:.0f} à {sc.iloc[-1]:.0f}.")
    pays = plat.get("pays") or {}
    if pays:
        s.append(f"Risque pays {pays.get('nom')} : {float(pays.get('score_risque') or 0):.0f}/100 ({pays.get('niveau')}), statut GAFI : "
                 f"{pays.get('gafi')}, {plat.get('nb_inscrits_pays', 0)} entrée(s) de sanctions rattachée(s) au pays.")
    foc = plat.get("focus")
    if foc:
        s.append(f"Focus Caraïbes & Amérique latine — typologies du pays : {foc.get('typologies')}.")
    if p.get("fin_sec") is not None and not p["fin_sec"].empty:
        s.append("Données financières SEC EDGAR disponibles (société cotée aux États-Unis).")
    s.append(f"Conclusion : risque {p['niveau'].lower()} ({p['score']:.0f}/100) — {p['vigilance']}.")
    attention = [a for a, _ in p["contributions"]]
    if p["type"] == "Entité" and not p.get("lei") and not any("LEI" in a for a in attention):
        attention.append("Pas de LEI identifié : vérifier l'existence légale au registre du pays.")
    if not p.get("pays"):
        msg = "Pays non renseigné : le risque géographique n'a pas pu être évalué."
        hits = p.get("hits", pd.DataFrame())
        if not hits.empty:
            cs = sorted({c for x in hits.pays for c in str(x).split(" | ") if c})
            if cs:
                msg += f" Les inscriptions correspondantes sont rattachées à : {', '.join(pays_nom(c) for c in cs[:5])}."
        attention.append(msg)
    if not p.get("listes_chargees", True):
        attention.insert(0, "Listes de sanctions non chargées dans la plateforme : filtrage incomplet (Centre de données → Tout enrichir).")
    etapes = []
    if p["meilleur_score_sanctions"] >= 80:
        etapes.append("Comparer date de naissance, nationalité et identifiants avec l'inscription (trame « Lever une homonymie »).")
    if p["type"] == "Entité":
        etapes.append("Obtenir l'extrait de registre et l'organigramme jusqu'aux bénéficiaires effectifs.")
    if p["nb_presse_negative"]:
        etapes.append("Lire les articles les plus graves et vérifier les faits sur des sources de premier rang.")
    if p["score"] >= 60:
        etapes.append("Soumettre le dossier à la conformité (validation hiérarchique) ; envisager la déclaration de soupçon ou le refus.")
    etapes.append("Renseigner la trame recommandée et conserver le rapport CWP au dossier.")
    return dict(texte=s, attention=attention, etapes=etapes)


def enrich_360(p: dict, en_ligne: dict | None = None) -> dict:
    en_ligne = en_ligne or {}
    p["fiche"] = {}
    if en_ligne.get("wikidata"):
        try:
            p["fiche"] = wikidata_fiche(p["nom"], p["type"])
            if not p.get("pays"):
                c = to_iso2((p["fiche"].get("pays") or p["fiche"].get("nationalite") or "").split(" | ")[0])
                if c:
                    p["pays"], p["pays_nom"] = c, pays_nom(c)
        except Exception as e:
            p["erreurs"].append(f"Wikidata (fiche) : {e}")
    if not p["fiche"]:
        w = store.load("wikidata_entites")
        if not w.empty:
            hit = w[w.nom.map(_norm) == _norm(p["nom"])]
            if not hit.empty:
                p["fiche"] = {k: v for k, v in hit.iloc[-1].to_dict().items() if v and k not in store.META_COLS}
    p["fin_sec"] = pd.DataFrame()
    if en_ligne.get("sec") and p["type"] == "Entité":
        try:
            p["fin_sec"] = sec_financials(p["nom"])
        except Exception as e:
            p["erreurs"].append(f"SEC EDGAR : {e}")
    plat = platform_data(p)
    p["plateforme"] = plat
    p["trames_recommandees"] = recommandations(p, plat)
    p["synthese"] = synthese(p, plat, p["fiche"])
    return p
