"""
cwp.data.screening — filtrage des noms (correspondance approchante) et profil d'entité.

Le profil agrège : listes de sanctions locales, PPE (Wikidata), presse négative (GDELT),
LEI (GLEIF), registre français (SIRENE/RNE), géocodage OSM et risque pays,
puis calcule un score de risque explicable (contribution de chaque facteur).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

import pandas as pd

from . import sources, store
from .countries import nom as pays_nom, to_iso2

try:
    from rapidfuzz import fuzz, process
except ImportError:  # repli très simple
    fuzz = process = None

STOP = {"the", "le", "la", "les", "de", "du", "des", "of", "and", "et", "sa", "sas", "sarl", "ltd", "llc",
        "inc", "co", "corp", "company", "plc", "gmbh", "ag", "bv", "jsc", "ojsc", "pjsc", "ooo", "limited",
        "group", "groupe", "holding", "al", "el", "bin", "ibn", "mr", "mrs", "dr"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(w for w in s.split() if w not in STOP)


def build_index() -> pd.DataFrame:
    """Une ligne par variante de nom (nom principal + alias) des listes de sanctions et des PPE."""
    sc = sources.sanctions_consolidees()
    rows = []
    for r in sc.itertuples():
        for i, n in enumerate([r.nom] + [a for a in str(r.alias).split(" | ") if a]):
            k = norm(n)
            if len(k) >= 3:
                rows.append((r.uid, r.liste, r.nom, n, "nom" if i == 0 else "alias", k, r.type, r.programme,
                             r.pays, r.date_naissance, r.date_inscription))
    ppe = store.load("ppe_wikidata")
    for r in ppe.itertuples() if not ppe.empty else []:
        k = norm(r.nom)
        if len(k) >= 3:
            rows.append((r.uid, "PPE (Wikidata)", r.nom, r.nom, "nom", k, "Personne", r.fonction, r.pays,
                         r.naissance, r.debut))
    ri = store.load("renseignements_internes")
    for r in ri.itertuples() if not ri.empty else []:
        for i, n in enumerate([r.nom] + [a for a in str(getattr(r, "alias", "")).split(" | ") if a.strip()]):
            k = norm(n)
            if len(k) >= 3:
                rows.append((r.uid, "Renseignement interne", r.nom, n.strip(), "nom" if i == 0 else "alias", k, r.type,
                             f"{r.categorie} · fiabilité {str(r.fiabilite)[:1]}{str(r.credibilite)[:1]}", r.pays, "", r.date_info))
    return pd.DataFrame(rows, columns=["uid", "liste", "nom", "variante", "nature", "cle", "type", "programme",
                                       "pays", "date_naissance", "date_inscription"])


def match(query: str, index: pd.DataFrame, seuil: int = 82, limite: int = 25,
          pays: str = "", annee: str = "", type_: str = "") -> pd.DataFrame:
    """Correspondances approchantes : moyenne pondérée de token_sort, token_set et Jaro-Winkler,
    avec bonus/malus sur le pays, l'année de naissance et le type d'entité."""
    q = norm(query)
    if not q or index.empty:
        return pd.DataFrame()
    keys = index.cle.tolist()
    if process:
        cand = process.extract(q, keys, scorer=fuzz.token_set_ratio, limit=limite * 8, score_cutoff=seuil - 15)
        idx = [c[2] for c in cand]
    else:
        idx = [i for i, k in enumerate(keys) if q in k or k in q]
    out = []
    try:
        from rapidfuzz.distance import JaroWinkler
    except Exception:
        JaroWinkler = None
    for i in idx:
        k = keys[i]
        s_sort = fuzz.token_sort_ratio(q, k) if fuzz else 100
        s_set = fuzz.token_set_ratio(q, k) if fuzz else 100
        s_jw = JaroWinkler.similarity(q, k) * 100 if JaroWinkler else s_sort
        # token_set sur-estime les noms courts inclus dans un long nom : on pondère par la couverture
        cov = min(len(q.split()), len(k.split())) / max(len(q.split()), len(k.split()))
        score = 0.45 * s_sort + 0.35 * s_set * (0.6 + 0.4 * cov) + 0.20 * s_jw
        r = index.iloc[i]
        bonus = []
        if pays and r.pays:
            if pays in str(r.pays).split(" | "):
                score += 4; bonus.append("pays identique")
            else:
                score -= 3; bonus.append("pays différent")
        if annee and r.date_naissance:
            if annee in str(r.date_naissance):
                score += 5; bonus.append("année de naissance identique")
            else:
                score -= 6; bonus.append("année de naissance différente")
        if type_ and r.type and type_ != r.type:
            score -= 8; bonus.append("type différent")
        score = max(0, min(100, score))
        if score >= seuil:
            out.append({**r.to_dict(), "score": round(score, 1), "ajustements": ", ".join(bonus)})
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out).sort_values("score", ascending=False).drop_duplicates("uid")
    df["niveau"] = pd.cut(df.score, [0, 88, 95, 101], labels=["Possible", "Probable", "Forte"], right=False).astype(str)
    return df.head(limite).reset_index(drop=True)


def batch_screening(df: pd.DataFrame, col_nom: str, index: pd.DataFrame, seuil=85,
                    col_pays: str | None = None) -> pd.DataFrame:
    """Filtrage d'une liste (fichier clients / fournisseurs) : meilleure correspondance par ligne."""
    res = []
    for _, r in df.iterrows():
        p = to_iso2(r[col_pays]) if col_pays else ""
        m = match(str(r[col_nom]), index, seuil=seuil, limite=3, pays=p)
        best = m.iloc[0] if not m.empty else None
        res.append({col_nom: r[col_nom], "alerte": "OUI" if best is not None else "non",
                    "meilleur_score": best.score if best is not None else "",
                    "nom_liste": best.nom if best is not None else "", "liste": best.liste if best is not None else "",
                    "programme": best.programme if best is not None else "",
                    "niveau": best.niveau if best is not None else "", "nb_correspondances": len(m)})
    return pd.DataFrame(res)


# --------------------------------------------------------------------------- #
# Score de risque d'une entité
# --------------------------------------------------------------------------- #
PAYS_OPAQUES = {"VG", "KY", "PA", "BZ", "SC", "BS", "MH", "LR", "AE", "CY", "MT", "LU", "JE", "GG", "IM",
                "BM", "AI", "TC", "WS", "VU", "LI", "MC", "GI"}


def score_entite(p: dict) -> dict:
    """Retourne score 0–100, niveau, vigilance et contributions (explicabilité)."""
    contrib = []
    best = p.get("meilleur_score_sanctions", 0) or 0
    if best >= 95:
        contrib.append(("Correspondance forte sur une liste de sanctions", 60))
    elif best >= 88:
        contrib.append(("Correspondance probable sur une liste de sanctions", 38))
    elif best >= 80:
        contrib.append(("Correspondance possible (homonymie à lever)", 15))
    if p.get("ppe_en_fonction"):
        contrib.append(("Personne politiquement exposée en fonction", 22))
    elif p.get("ppe"):
        contrib.append(("Ancienne PPE (moins de 12 mois à vérifier)", 10))
    nneg = p.get("nb_presse_negative", 0) or 0
    nfort = p.get("nb_presse_grave", 0) or 0
    if nneg:
        contrib.append((f"Presse négative ({nneg} article(s), dont {nfort} grave(s))", min(20, 2 * nneg + 3 * nfort)))
    sp = float(p.get("score_pays", 0) or 0)
    if sp:
        contrib.append((f"Risque pays {p.get('pays_nom', '')} ({sp:.0f}/100)", round(sp * 0.25, 1)))
    if p.get("interne_score", 0) >= 88:
        contrib.append(("Renseignement interne défavorable (fichier CWP)", 15))
    no = p.get("notoriete")
    if no:
        lvl = int(str(no["niveau"])[0]) if str(no["niveau"])[:1].isdigit() else 0
        pts = {5: 20, 4: 12, 3: 6}.get(lvl, 0)
        if pts:
            contrib.append((f"Notoriété négative niveau {lvl}/5 (recherche du {no['date'][:10]})", pts))
    from .countries import REGIMES_SANCTIONS
    if p.get("pays") in REGIMES_SANCTIONS:
        contrib.append((f"Pays visé par un régime de sanctions majeur ({p.get('pays_nom', '')})", 15))
    if p.get("pays") in PAYS_OPAQUES:
        contrib.append(("Juridiction à forte opacité / centre offshore", 6))
    if p.get("type") == "Entité" and p.get("lei_recherche") and not p.get("lei"):
        contrib.append(("Aucun LEI trouvé pour une personne morale", 4))
    if p.get("lei_statut") and p.get("lei_statut") not in ("ISSUED", "PENDING_TRANSFER", "PENDING_ARCHIVAL"):
        contrib.append((f"LEI non renouvelé ({p.get('lei_statut')})", 4))
    if p.get("etat_fr") == "C":
        contrib.append(("Société radiée / cessée au registre français", 5))
    total = min(100.0, sum(c[1] for c in contrib))
    niveau = "Élevé" if total >= 60 else "Modéré" if total >= 30 else "Faible"
    vig = {"Élevé": "Vigilance renforcée", "Modéré": "Vigilance standard", "Faible": "Vigilance simplifiée possible"}[niveau]
    if best >= 95:
        vig = "STOP — gel / déclaration à étudier immédiatement"
    elif not p.get("listes_chargees", True) and niveau == "Faible":
        vig = "Vigilance standard (filtrage incomplet : listes de sanctions non chargées)"
    return dict(score=round(total, 1), niveau=niveau, vigilance=vig, contributions=contrib)


def profil(nom: str, type_: str = "Entité", pays: str = "", annee: str = "", index: pd.DataFrame | None = None,
           en_ligne: dict | None = None, seuil: int = 82) -> dict:
    """Construit le profil complet d'une entité.
    en_ligne : {"ppe": bool, "presse": bool, "lei": bool, "fr": bool, "geo": bool} pour les appels réseau."""
    en_ligne = en_ligne or {}
    index = build_index() if index is None else index
    p = dict(nom=nom, type=type_, pays=pays, pays_nom=pays_nom(pays) if pays else "", annee=annee,
             date=datetime.now().strftime("%Y-%m-%d %H:%M"), erreurs=[])
    hits = match(nom, index, seuil=seuil, pays=pays, annee=annee, type_=type_)
    p["hits"] = hits
    sanc = hits[~hits.liste.isin(["PPE (Wikidata)", "Renseignement interne"])] if not hits.empty else hits
    interne = hits[hits.liste == "Renseignement interne"] if not hits.empty else hits
    p["interne_df"] = interne
    p["interne_score"] = float(interne.score.max()) if not interne.empty else 0
    p["meilleur_score_sanctions"] = float(sanc.score.max()) if not sanc.empty else 0
    p["listes_touchees"] = sorted(set(sanc.liste)) if not sanc.empty else []
    ppe_local = hits[hits.liste == "PPE (Wikidata)"] if not hits.empty else pd.DataFrame()

    ppe = ppe_local
    if en_ligne.get("ppe") and type_ == "Personne":
        try:
            w = sources.ppe_nom(nom)
            if not w.empty:
                w = w[w.nom.map(lambda x: (fuzz.token_sort_ratio(norm(x), norm(nom)) if fuzz else 100) >= 88)]
                ppe = pd.concat([ppe_local, w], ignore_index=True)
        except Exception as e:
            p["erreurs"].append(f"Wikidata : {e}")
    p["ppe_df"] = ppe
    p["ppe"] = not ppe.empty
    p["ppe_en_fonction"] = bool(not ppe.empty and "en_fonction" in ppe and (ppe.en_fonction == "oui").any())

    presse = pd.DataFrame()
    if en_ligne.get("presse"):
        try:
            presse = sources.presse_negative(nom)
        except Exception as e:
            p["erreurs"].append(f"GDELT : {e}")
    if presse.empty:
        old = store.load("presse_negative")
        if not old.empty:
            presse = old[old.entite.str.lower() == nom.lower()]
    p["presse"] = presse
    nr = store.load("notoriete_recherches")
    if not nr.empty:
        nh = nr[nr.nom.map(norm) == norm(nom)].sort_values("date")
        if not nh.empty:
            last = nh.iloc[-1]
            p["notoriete"] = dict(score=float(last.score), niveau=last.niveau, date=last.date, synthese=last.synthese)
    p["nb_presse_negative"] = len(presse)
    p["nb_presse_grave"] = int(presse.categorie.isin(["Sanctions", "Blanchiment", "Corruption", "Justice"]).sum()) if not presse.empty else 0

    p["lei_df"] = pd.DataFrame()
    if en_ligne.get("lei") and type_ == "Entité":
        p["lei_recherche"] = True
        try:
            g = sources.gleif_search(nom, n=5)
            if not g.empty:
                g["sim"] = g.nom.map(lambda x: fuzz.token_sort_ratio(norm(x), norm(nom)) if fuzz else 100)
                g = g.sort_values("sim", ascending=False)
                p["lei_df"] = g
                top = g.iloc[0]
                if top.sim >= 85:
                    p.update(lei=top.lei, lei_statut=top.statut_lei, lei_parent=top.parent_direct,
                             lei_parent_ultime=top.parent_ultime, adresse=f"{top.adresse}, {top.ville}",
                             pays=p["pays"] or top.pays)
        except Exception as e:
            p["erreurs"].append(f"GLEIF : {e}")

    p["fr_df"] = pd.DataFrame()
    if en_ligne.get("fr") and type_ == "Entité" and (not pays or pays == "FR"):
        try:
            f = sources.entreprises_fr(nom, n=5)
            if not f.empty:
                p["fr_df"] = f
                top = f.iloc[0]
                if fuzz is None or fuzz.token_sort_ratio(norm(top.nom), norm(nom)) >= 80:
                    p.update(siren=top.siren, dirigeants=top.dirigeants, etat_fr=top.etat, naf=top.naf,
                             adresse=p.get("adresse") or f"{top.adresse}", pays=p["pays"] or "FR")
                    if top.lat:
                        p["geo"] = dict(lat=float(top.lat), lon=float(top.lon), label=top.adresse)
        except Exception as e:
            p["erreurs"].append(f"Registre français : {e}")

    if en_ligne.get("geo") and not p.get("geo"):
        q = p.get("adresse") or (pays_nom(p["pays"]) if p["pays"] else "")
        if q:
            try:
                p["geo"] = sources.geocode(q)
            except Exception as e:
                p["erreurs"].append(f"OpenStreetMap : {e}")

    p["pays_nom"] = pays_nom(p["pays"]) if p["pays"] else ""
    p["listes_chargees"] = not index[~index.liste.isin(["PPE (Wikidata)", "Renseignement interne"])].empty if not index.empty else False
    pr = store.load("pays_risque")
    if pr.empty:
        pr = sources.build_pays_risque()
    if p["pays"] and not pr.empty and p["pays"] in set(pr.iso2):
        row = pr[pr.iso2 == p["pays"]].iloc[0]
        p["score_pays"], p["pays_gafi"], p["pays_niveau"] = row.score_risque, row.gafi, row.niveau
    p.update(score_entite(p))
    return p


def sauver_profil(p: dict) -> dict:
    row = dict(uid=store_key(p), nom=p["nom"], type=p["type"], pays=p.get("pays", ""), date=p["date"],
               score=p["score"], niveau=p["niveau"], vigilance=p["vigilance"],
               meilleur_score_sanctions=p["meilleur_score_sanctions"], listes=" | ".join(p["listes_touchees"]),
               nb_correspondances=len(p["hits"]), ppe="oui" if p["ppe"] else "non",
               ppe_en_fonction="oui" if p["ppe_en_fonction"] else "non",
               nb_presse_negative=p["nb_presse_negative"], nb_presse_grave=p["nb_presse_grave"],
               score_pays=p.get("score_pays", ""), lei=p.get("lei", ""), siren=p.get("siren", ""),
               lat=(p.get("geo") or {}).get("lat", ""), lon=(p.get("geo") or {}).get("lon", ""),
               facteurs=" ; ".join(f"{a} (+{b})" for a, b in p["contributions"]))
    return store.append_rows("entites_profils", [row], source="CWP")


def store_key(p: dict) -> str:
    return f"{norm(p['nom']).replace(' ', '-')}-{p.get('type', '')}-{p.get('pays', '')}"[:80]
