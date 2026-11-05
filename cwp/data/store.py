"""
cwp.data.store — stockage CSV de CWP, enrichi à chaque clic.

Principe
--------
Chaque jeu de données est un CSV dans data/ avec une clé unique (`uid`).
`upsert()` fusionne un nouveau lot avec l'existant :
  • nouvelle clé       → ajoutée, `premiere_vue` = maintenant, `statut` = actif
  • clé déjà connue    → champs mis à jour, `derniere_vue` = maintenant
  • clé absente du lot → (si `snapshot=True`, c.-à-d. le lot est la liste complète)
                         `statut` = retiré, `retire_le` = maintenant
Rien n'est jamais supprimé : l'historique s'accumule à chaque enrichissement.
Chaque opération est tracée dans data/journal_maj.csv.
"""
from __future__ import annotations

import io
import os
import zipfile
from datetime import datetime

import pandas as pd

from cwp.config import COPYRIGHT, DATA_DIR, DISCLAIMER, MODEL_DIR, ROOT  # noqa: F401  (ROOT réexporté)

META_COLS = ["premiere_vue", "derniere_vue", "statut", "retire_le"]

# Catalogue des jeux de données : nom de fichier -> description + source (nom seul)
CATALOGUE = {
    "sanctions_ofac":     ("Sanctions — OFAC SDN (États-Unis)", "OFAC – Trésor américain"),
    "sanctions_ue":       ("Sanctions — liste consolidée UE", "Commission européenne (FSF)"),
    "sanctions_onu":      ("Sanctions — liste consolidée ONU", "Conseil de sécurité des Nations unies"),
    "sanctions_uk":       ("Sanctions — UK Sanctions List", "FCDO – Royaume-Uni"),
    "gels_avoirs_fr":     ("Registre national des gels (France)", "DG Trésor"),
    "pays_risque":        ("Risque pays (WGI, GAFI, sanctions)", "Banque mondiale · GAFI · CWP"),
    "actualites":         ("Actualités conformité enrichies", "Presse (Google News) · CWP"),
    "presse_negative":    ("Presse négative par entité", "GDELT Project"),
    "ppe_wikidata":       ("Personnes politiquement exposées", "Wikidata"),
    "lei_gleif":          ("Identifiants LEI et liens de groupe", "GLEIF"),
    "entreprises_fr":     ("Entreprises françaises (SIRENE / RNE)", "API Recherche d'entreprises – DINUM"),
    "osm_poi":            ("Points d'intérêt à risque (OSM)", "OpenStreetMap (Overpass)"),
    "geocodage":          ("Cache de géocodage", "OpenStreetMap (Nominatim)"),
    "entites_profils":    ("Profils d'entités analysés", "CWP"),
    "ml_labels":          ("Étiquettes validées pour l'apprentissage", "CWP"),
    "wikidata_entites":   ("Fiches d'identité (Wikidata / Wikipédia)", "Wikidata · Wikipédia"),
    "sec_edgar":          ("Données financières sociétés cotées US", "SEC EDGAR"),
    "glossaire_wiki":     ("Glossaire importé de Wikipédia", "Wikipédia (CC BY-SA)"),
    "glossaire_perso":    ("Glossaire personnel importé", "Utilisateur"),
    "notoriete_recherches": ("Recherches de notoriété négative", "CWP (Google Actualités · GDELT · web)"),
    "notoriete_articles": ("Articles de notoriété analysés et notés", "CWP"),
    "veille_caraibes":    ("Veille conformité Haïti & Caraïbes", "Google Actualités · médias haïtiens"),
    "renseignements_internes": ("Renseignements internes (non publics)", "Saisie analyste"),
}


def path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.csv")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load(name: str) -> pd.DataFrame:
    p = path(name)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
    except Exception:
        return pd.DataFrame()


def save(name: str, df: pd.DataFrame) -> None:
    tmp = path(name) + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path(name))


def upsert(name: str, new: pd.DataFrame, key: str = "uid", snapshot: bool = False,
           source: str = "") -> dict:
    """Fusionne `new` dans data/<name>.csv. Renvoie un bilan {ajoutes, maj, retires, total}."""
    ts = now()
    old = load(name)
    if new is None or new.empty:
        stats = dict(ajoutes=0, maj=0, retires=0, total=len(old))
        log(name, "aucune donnée reçue", stats, source)
        return stats
    new = new.copy().astype(str).replace({"nan": "", "None": ""})
    new = new.drop_duplicates(subset=[key], keep="last")
    for c in META_COLS:
        if c in new.columns:
            new = new.drop(columns=c)

    if old.empty:
        out = new.assign(premiere_vue=ts, derniere_vue=ts, statut="actif", retire_le="")
        stats = dict(ajoutes=len(out), maj=0, retires=0, total=len(out))
    else:
        for c in META_COLS:
            if c not in old.columns:
                old[c] = ""
        old_keys, new_keys = set(old[key]), set(new[key])
        added = new[~new[key].isin(old_keys)].assign(premiere_vue=ts, derniere_vue=ts,
                                                       statut="actif", retire_le="")
        upd = new[new[key].isin(old_keys)].set_index(key)
        base = old.set_index(key)
        for c in upd.columns:
            if c not in base.columns:
                base[c] = ""
        base.loc[upd.index, upd.columns] = upd
        base.loc[upd.index, "derniere_vue"] = ts
        reactivated = base.loc[upd.index, "statut"].eq("retiré").sum()
        base.loc[upd.index, "statut"] = "actif"
        base.loc[upd.index, "retire_le"] = ""
        retired = 0
        if snapshot:
            gone = base.index.difference(list(new_keys))
            mask = base.loc[gone, "statut"].ne("retiré")
            retired = int(mask.sum())
            base.loc[gone[mask.values], "statut"] = "retiré"
            base.loc[gone[mask.values], "retire_le"] = ts
        out = pd.concat([base.reset_index(), added], ignore_index=True)
        stats = dict(ajoutes=len(added), maj=len(upd), retires=retired, total=len(out),
                     reactives=int(reactivated))
    save(name, out)
    log(name, "enrichissement", stats, source)
    return stats


def append_rows(name: str, rows: list[dict] | pd.DataFrame, key: str = "uid", source: str = "") -> dict:
    df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    return upsert(name, df, key=key, snapshot=False, source=source)


def log(name: str, action: str, stats: dict, source: str = "", erreur: str = "") -> None:
    p = path("journal_maj")
    row = pd.DataFrame([dict(horodatage=now(), jeu=name, action=action, source=source,
                             ajoutes=stats.get("ajoutes", 0), maj=stats.get("maj", 0),
                             retires=stats.get("retires", 0), total=stats.get("total", 0),
                             erreur=erreur)])
    row.to_csv(p, mode="a", header=not os.path.exists(p), index=False, encoding="utf-8")


def journal() -> pd.DataFrame:
    return load("journal_maj")


def status() -> pd.DataFrame:
    """Tableau de bord des jeux de données (lignes, actifs, dernière mise à jour)."""
    j = journal()
    rows = []
    for name, (desc, src) in CATALOGUE.items():
        df = load(name)
        last = ""
        if not j.empty:
            jj = j[(j.jeu == name) & (j.erreur.fillna("") == "")]
            last = jj.horodatage.max() if not jj.empty else ""
        actifs = int((df["statut"] == "actif").sum()) if "statut" in df.columns else len(df)
        nouveaux = 0
        if not df.empty and "premiere_vue" in df.columns and last:
            nouveaux = int((df["premiere_vue"] == last).sum()) if last in set(df["premiere_vue"]) else 0
        rows.append(dict(jeu=name, description=desc, source=src, lignes=len(df), actives=actifs,
                         derniere_maj=last or "jamais", nouveaux_dernier_lot=nouveaux,
                         taille_ko=round(os.path.getsize(path(name)) / 1024, 1) if os.path.exists(path(name)) else 0))
    return pd.DataFrame(rows)


def export_zip() -> bytes:
    """Toutes les données CSV dans une archive (sauvegarde)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(DATA_DIR)):
            if f.endswith(".csv"):
                z.write(os.path.join(DATA_DIR, f), f"data/{f}")
        z.writestr("data/LISEZMOI.txt", f"Sauvegarde des données — {COPYRIGHT} · {now()}\n{DISCLAIMER}\n")
    return buf.getvalue()


def import_zip(data: bytes) -> list[str]:
    """Restaure une sauvegarde : fusionne chaque CSV avec l'existant (rien n'est perdu)."""
    done = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            base = os.path.basename(n)
            if not base.endswith(".csv") or base.startswith("."):
                continue
            name = base[:-4]
            df = pd.read_csv(z.open(n), dtype=str, keep_default_na=False)
            if name == "journal_maj":
                cur = journal()
                pd.concat([cur, df]).drop_duplicates().to_csv(path(name), index=False)
            elif "uid" in df.columns:
                cur = load(name)
                merged = pd.concat([cur, df]).drop_duplicates(subset=["uid"], keep="first") if not cur.empty else df
                save(name, merged)
            else:
                save(name, df)
            done.append(name)
    return done


def export_excel(names: list[str] | None = None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"CWP": [COPYRIGHT, DISCLAIMER,
                              f"Export du {datetime.now():%d/%m/%Y %H:%M}"]}).to_excel(xw, sheet_name="Signature", index=False)
        status().to_excel(xw, sheet_name="Inventaire", index=False)
        for n in names or CATALOGUE:
            df = load(n)
            if not df.empty:
                df.head(1_000_000).to_excel(xw, sheet_name=n[:31], index=False)
    return buf.getvalue()
