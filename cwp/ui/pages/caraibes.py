"""CWP — Caraïbes : dispositif LCB-FT de 29 juridictions de la Caraïbe, sur le modèle de la fiche Haïti.

Appelé depuis cwp/ui/pages/haiti.py (onglet « 🌎 Caraïbe — 29 pays »).
Fichiers : data/reference/caraibes_pays.csv (base de connaissances, modifiable) ; veille stockée via cwp.data.store sous « veille_caraibes_pays ».
Fond de carte : projection Plotly « natural earth » (aucune clé API, contrairement aux tuiles CARTO).
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from cwp.config import DATA_DIR, ref_path

F_PAYS = Path(ref_path("caraibes_pays.csv"))
F_VEILLE = Path(DATA_DIR) / "veille_caraibes_pays.csv"  # repli seulement si cwp.data.store est indisponible
UA = {"User-Agent": "CWP-ComplianceWatch/1.0 (veille réglementaire)"}

COORD = {"HT": (18.97, -72.29), "DO": (18.74, -70.16), "CU": (21.52, -77.78), "VE": (8.0, -66.0), "TT": (10.69, -61.22),
         "JM": (18.11, -77.30), "BS": (25.03, -77.40), "BB": (13.19, -59.54), "BZ": (17.19, -88.50), "GY": (4.86, -58.93),
         "SR": (3.92, -56.03), "AG": (17.06, -61.80), "DM": (15.41, -61.37), "GD": (12.11, -61.68), "KN": (17.36, -62.78),
         "LC": (13.91, -60.98), "VC": (12.98, -61.29), "KY": (19.31, -81.25), "VG": (18.42, -64.64), "AI": (18.22, -63.07),
         "MS": (16.74, -62.19), "TC": (21.69, -71.80), "BM": (32.32, -64.76), "AW": (12.52, -69.97), "CW": (12.17, -68.99),
         "SX": (18.04, -63.05), "BQ": (12.20, -68.26), "FR-DOM": (16.25, -61.55), "PR-VI": (18.22, -66.59)}

# Requêtes Google Actualités : nom local + mots-clés LCB-FT dans la langue du pays + édition locale
LANG = {"es": ("lavado de activos OR sanciones OR corrupción OR GAFIC OR GAFILAT OR narcotráfico", "es-419"),
        "en": ('"money laundering" OR sanctions OR corruption OR CFATF OR FATF OR "financial intelligence"', "en"),
        "nl": ("witwassen OR sancties OR corruptie OR FIU OR CFATF", "nl"),
        "fr": ("blanchiment OR sanctions OR corruption OR GAFIC OR GAFI OR TRACFIN", "fr")}
REQ = {"HT": ("Haïti", "fr", "HT"), "DO": ("República Dominicana", "es", "DO"), "CU": ("Cuba", "es", "CU"),
       "VE": ("Venezuela", "es", "VE"), "TT": ('"Trinidad and Tobago"', "en", "TT"), "JM": ("Jamaica", "en", "JM"),
       "BS": ("Bahamas", "en", "BS"), "BB": ("Barbados", "en", "BB"), "BZ": ("Belize", "en", "BZ"), "GY": ("Guyana", "en", "GY"),
       "SR": ("Suriname", "nl", "SR"), "AG": ('"Antigua and Barbuda"', "en", "AG"), "DM": ("Dominica", "en", "DM"),
       "GD": ("Grenada", "en", "GD"), "KN": ('"St Kitts" OR Nevis', "en", "KN"), "LC": ('"St Lucia" OR "Saint Lucia"', "en", "LC"),
       "VC": ('"St Vincent" Grenadines', "en", "VC"), "KY": ('"Cayman Islands"', "en", "KY"), "VG": ('"British Virgin Islands" OR BVI', "en", "VG"),
       "AI": ("Anguilla", "en", "AI"), "MS": ("Montserrat", "en", "MS"), "TC": ('"Turks and Caicos"', "en", "TC"),
       "BM": ("Bermuda", "en", "BM"), "AW": ("Aruba", "nl", "AW"), "CW": ("Curaçao", "nl", "CW"), "SX": ('"Sint Maarten"', "nl", "SX"),
       "BQ": ("Bonaire OR Saba OR \"Sint Eustatius\"", "nl", "BQ"), "FR-DOM": ("Guadeloupe OR Martinique OR Guyane OR \"Saint-Martin\"", "fr", "FR"),
       "PR-VI": ('"Puerto Rico" OR "US Virgin Islands"', "en", "PR")}
THEMES = {"Sanctions & gangs": r"sanction|ofac|gang|pandilla|banda|embargo",
          "GAFIC / CFATF": r"gafic|cfatf|gafi|fatf|gafilat|grey list|liste grise|lista gris|evaluaci|evaluation",
          "Blanchiment": r"blanchi|lavado|laundering|witwas|tracfin|\bfiu\b|\buaf\b",
          "Corruption": r"corrup|soborno|bribe|pot-de-vin|fraud",
          "Narcotrafic": r"drog|narco|cocaïne|cocaine|cocaína|trafic|trafficking",
          "Fiscalité & offshore": r"offshore|fiscal|tax|impuesto|citizenship by investment|cbi|passport"}


@st.cache_data(show_spinner=False)
def pays() -> pd.DataFrame:
    return pd.read_csv(F_PAYS, dtype=str).fillna("")


try:  # stockage CWP (cwp.data.store) ; repli sur un CSV local si le module est utilisé hors de CWP
    from cwp.data import store as _store
    from cwp.data.sources import _uid
except Exception:  # pragma: no cover
    _store = None
    import hashlib

    def _uid(*x):
        return hashlib.md5("|".join(map(str, x)).encode()).hexdigest()[:16]

NOM_STORE = "veille_caraibes_pays"  # séparé de « veille_caraibes » (onglet Veille Haïti existant)


def lire_veille() -> pd.DataFrame:
    if _store is not None:
        try:
            return _store.load(NOM_STORE)
        except Exception:
            pass
    return pd.read_csv(F_VEILLE) if F_VEILLE.exists() else pd.DataFrame()


def _theme(t: str) -> str:
    return next((k for k, v in THEMES.items() if re.search(v, t, re.I)), "Autre")


def mettre_a_jour_veille(codes: list[str] | None = None) -> tuple[int, list[str]]:
    p = pays().set_index("code")
    lignes, erreurs = [], []
    for code in codes or list(REQ):
        nom, lg, gl = REQ[code]
        mots, hl = LANG[lg]
        q = f"({mots}) {nom}"
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
        try:
            r = requests.get(url, headers=UA, timeout=20)
            r.raise_for_status()
            for it in ET.fromstring(r.content).iter("item"):
                titre = html.unescape(it.findtext("title") or "")
                src = it.find("source")
                try:
                    d = parsedate_to_datetime(it.findtext("pubDate")).strftime("%Y-%m-%d")
                except Exception:
                    d = ""
                media = src.text if src is not None else ""
                if media and titre.endswith(" - " + media):
                    titre = titre[: -(len(media) + 3)]
                lien = it.findtext("link") or ""
                lignes.append({"uid": _uid(lien or titre), "date": d, "pays": p.loc[code, "pays"], "code": code, "titre": titre,
                               "media": media, "lien": lien, "langue": lg, "theme": _theme(titre), "requete": q,
                               "collecte_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")})
        except Exception as e:
            erreurs.append(f"{p.loc[code, 'pays']} : {str(e)[:80]}")
    if not lignes:
        return 0, erreurs
    if _store is not None:
        try:
            r = _store.append_rows(NOM_STORE, lignes, source="Google Actualités (Caraïbe)")
            return int(r.get("ajoutes", len(lignes))), erreurs
        except Exception as e:
            erreurs.append(f"stockage CWP : {str(e)[:80]}")
    df = pd.DataFrame(lignes)
    if F_VEILLE.exists():
        df = pd.concat([df, pd.read_csv(F_VEILLE)], ignore_index=True)
    df = df.drop_duplicates("uid").sort_values("date", ascending=False).head(6000)
    F_VEILLE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(F_VEILLE, index=False)
    return len(lignes), erreurs


def _badge(txt: str) -> str:
    rouge = any(k in txt for k in ("liste grise", "haut risque", "Annexe I", "Oui"))
    orange = "Annexe II" in txt or "Programme" in txt or "Désignations" in txt
    c = "#d03b3b" if rouge and "Annexe II" not in txt else "#eb6834" if orange else "#0ca30c"
    return f"<span style='background:{c};color:#fff;border-radius:999px;padding:2px 10px;font-size:.8rem;font-weight:700'>{html.escape(txt)}</span>"


def liens(urls: str, vide: str = "🔗 lien à compléter") -> str:
    """Transforme « url1 | url2 » en liens Markdown cliquables, nommés par leur domaine."""
    out = [f"[{u.strip().split('/')[2].replace('www.', '')}]({u.strip()})" for u in str(urls).split("|") if u.strip().startswith("http")]
    return " · ".join(out) if out else f"_{vide}_"


def _score(r) -> int:
    """Indice de vigilance 0-100 (lecture rapide pour l'analyste ; à adapter à votre matrice de risque pays)."""
    s = 0
    s += 35 if "liste grise" in r.statut_gafi else 0
    s += 25 if "haut risque" in r.statut_ue_lcb else 0
    s += 15 if "Annexe I" in r.statut_ue_fiscal and "Annexe II" not in r.statut_ue_fiscal else 8 if "Annexe II" in r.statut_ue_fiscal else 0
    s += 15 if r.sanctions_onu.startswith("Oui") else 0
    s += 10 if r.sanctions_pays_usa.startswith("Programme") else 5 if r.sanctions_pays_usa != "Non" else 0
    return min(100, s)


def render_caraibes() -> None:
    p = pays().copy()
    p["vigilance"] = p.apply(_score, axis=1)
    t_reg, t_disp, t_seuil, t_ctx, t_veille = st.tabs(["🗺️ Vue régionale", "🏛️ Dispositif & institutions", "📏 Seuils & obligations",
                                                      "🌪️ Contexte & rapport", "📡 Veille Caraïbes"])
    with t_reg:
        st.caption("29 juridictions : membres du GAFIC, République dominicaine et Cuba (GAFILAT), territoires français, néerlandais et "
                   "américains. Statuts des listes vérifiés au 04/11/2026.")
        a, b, c, d = st.columns(4)
        a.metric("Juridictions", len(p))
        b.metric("Liste grise GAFI", int(p.statut_gafi.str.contains("grise").sum()))
        c.metric("Haut risque UE (LCB-FT)", int(p.statut_ue_lcb.str.contains("haut risque").sum()))
        d.metric("Liste noire fiscale UE", int(p.statut_ue_fiscal.str.startswith("Annexe I (").sum()))
        g = p.assign(lat=p.code.map(lambda k: COORD[k][0]), lon=p.code.map(lambda k: COORD[k][1]))
        fig = px.scatter_geo(g, lat="lat", lon="lon", color="vigilance", size=g.vigilance + 12, hover_name="pays",
                             hover_data={"statut_gafi": True, "statut_ue_lcb": True, "statut_ue_fiscal": True, "lat": False, "lon": False,
                                         "vigilance": True}, color_continuous_scale=["#0ca30c", "#fab219", "#d03b3b"], range_color=[0, 100],
                             projection="natural earth")
        fig.update_geos(lataxis_range=[0, 34], lonaxis_range=[-92, -52], showcountries=True, showland=True, landcolor="#f0efec",
                        showocean=True, oceancolor="#dfeaf5")
        fig.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar_title="Vigilance")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(p.sort_values("vigilance", ascending=False)[["pays", "statut_politique", "organisme_regional", "sigle_crf", "statut_gafi",
                                                                 "statut_ue_lcb", "statut_ue_fiscal", "sanctions_onu", "sanctions_pays_usa",
                                                                 "vigilance", "site_crf"]],
                     hide_index=True, width="stretch",
                     column_config={"vigilance": st.column_config.ProgressColumn("Vigilance /100", min_value=0, max_value=100, format="%d"),
                                    "pays": "Juridiction", "statut_politique": "Statut", "organisme_regional": "Organisme régional",
                                    "sigle_crf": "CRF", "statut_gafi": "GAFI", "statut_ue_lcb": "UE – LCB-FT",
                                    "statut_ue_fiscal": "UE – fiscal", "sanctions_onu": "Sanctions ONU", "sanctions_pays_usa": "Sanctions USA",
                                    "site_crf": st.column_config.LinkColumn("Site CRF", display_text="ouvrir")})
        st.caption("Indice de vigilance : liste grise GAFI 35 · haut risque UE 25 · liste noire fiscale UE 15 (grise 8) · sanctions ONU 15 · "
                   "programme de sanctions américain 10 (désignations ciblées 5). Les juridictions de la liste noire GAFI (RPDC, Iran, Myanmar) "
                   "ne sont pas dans la Caraïbe.")
        st.download_button("⬇️ Base Caraïbes (CSV)", p.to_csv(index=False).encode("utf-8-sig"), "caraibes_pays.csv", "text/csv")

    choix = None
    for cle, onglet in (("disp", t_disp), ("seuil", t_seuil), ("ctx", t_ctx)):
        with onglet:
            choix = st.selectbox("Juridiction", p.pays.tolist(), index=0, key=f"car_juridiction_{cle}")
            r = p[p.pays == choix].iloc[0]
            st.markdown(f"### {r.pays} &nbsp; {_badge(r.statut_gafi)}", unsafe_allow_html=True)
            if onglet is t_disp:
                st.markdown(f"""
| Rubrique | Information | Vérifier |
|---|---|---|
| Statut | {r.statut_politique} | |
| Langues · monnaie | {r.langues} · {r.monnaie} | |
| Organisme régional | {r.organisme_regional} | {liens(r.source_membres)} |
| Cellule de renseignement financier | **{r.crf} ({r.sigle_crf})** | {liens(r.site_crf)} |
| Autorités de supervision | {r.supervision} | _à confirmer (site du superviseur)_ |
| Texte principal | {r.loi_principale} | {liens(r.source_loi)} |
| Dernière évaluation mutuelle | {r.derniere_evaluation} | {liens(r.source_evaluation)} |
""")
                st.caption(f"Fiabilité : {r.fiabilite_dispositif}")
            elif onglet is t_seuil:
                st.markdown(f"**Seuils spécifiques à {r.pays}** : {r.seuils}")
                st.markdown(f"🔗 **Vérifier** : {liens(r.source_seuils, 'aucun texte trouvé en ligne — à compléter')}  \n"
                            f"<small>Fiabilité : {r.fiabilite_seuils or 'À vérifier'}</small>", unsafe_allow_html=True)
                st.markdown("**Obligations communes (recommandations du GAFI, applicables dans toutes ces juridictions)** :\n"
                            "- identification et vérification du client et du bénéficiaire effectif (R.10, R.24-25) ;\n"
                            "- vigilance renforcée pour les PPE (R.12) et les pays à haut risque (R.19) ;\n"
                            "- déclaration d'opération suspecte à la CRF sans délai (R.20) et interdiction d'en informer le client (R.21) ;\n"
                            "- conservation des documents au moins 5 ans (R.11) ;\n"
                            "- informations sur le donneur d'ordre et le bénéficiaire des virements (R.16) ;\n"
                            "- gel sans délai des avoirs des personnes désignées par l'ONU (R.6).")
                if "haut risque" in r.statut_ue_lcb:
                    st.warning("Pour une entité assujettie de l'UE : mesures de vigilance renforcées obligatoires pour toute relation "
                               "d'affaires ou opération impliquant cette juridiction (pays tiers à haut risque).")
            else:
                st.markdown(f"**Typologies et facteurs de risque** : {r.typologies}")
                st.markdown(f"""
| Liste | Statut | Vérifier |
|---|---|---|
| GAFI – juridictions sous surveillance (30/10/2026) | {_badge(r.statut_gafi)} | {liens(r.source_gafi)} |
| UE – pays tiers à haut risque LCB-FT | {_badge(r.statut_ue_lcb)} | {liens(r.source_ue_lcb)} |
| UE – liste fiscale (oct. 2026) | {_badge(r.statut_ue_fiscal)} | {liens(r.source_ue_fiscal)} |
| Conseil de sécurité de l'ONU | {_badge('Sanctions ONU : ' + r.sanctions_onu)} | [un.org](https://main.un.org/securitycouncil/fr/content/un-sc-consolidated-list) |
| États-Unis (OFAC) | {html.escape(r.sanctions_pays_usa)} | [ofac.treasury.gov](https://ofac.treasury.gov/sanctions-programs-and-country-information) |
""", unsafe_allow_html=True)
                st.metric("Indice de vigilance", f"{r.vigilance} / 100")
                st.caption(f"Fiabilité des statuts : {r.fiabilite_statuts}.")
                fiche = pd.DataFrame(r).reset_index()
                fiche.columns = ["Rubrique", "Valeur"]
                st.download_button(f"⬇️ Fiche {r.pays} (HTML)", (f"<meta charset='utf-8'><h1>{html.escape(r.pays)}</h1>"
                                   + fiche.to_html(index=False)).encode("utf-8"), f"fiche_lcbft_{r.code}.html", "text/html")

    with t_veille:
        st.write("Articles récents sur la conformité, le blanchiment, la corruption et les sanctions dans **toute la Caraïbe**, dans la langue "
                 "de chaque pays (espagnol, anglais, néerlandais, français). Chaque clic enrichit la veille « veille_caraibes_pays ».")
        v = lire_veille()
        c1, c2 = st.columns(2)
        sel_p = c1.multiselect("Pays", p.pays.tolist(), placeholder="Tous les pays")
        sel_t = c2.multiselect("Thèmes", list(THEMES) + ["Autre"], placeholder="Tous les thèmes")
        if st.button("📡 Mettre à jour la veille Caraïbes (29 juridictions)", type="primary"):
            codes = p[p.pays.isin(sel_p)].code.tolist() if sel_p else None
            with st.spinner("Collecte en cours (≈ 30 s)…"):
                n, err = mettre_a_jour_veille(codes)
            st.success(f"{n} articles collectés.")
            if err:
                st.caption("Sources en échec : " + " · ".join(err))
            st.cache_data.clear()
            v = lire_veille()
        if v.empty:
            st.info("Aucun article : cliquez sur « Mettre à jour la veille Caraïbes ».")
            return
        if "pays" not in v:
            v = v.assign(pays="—")
        if sel_p:
            v = v[v.pays.isin(sel_p)]
        if sel_t and "theme" in v:
            v = v[v.theme.isin(sel_t)]
        st.plotly_chart(px.histogram(v, y="pays", color="theme" if "theme" in v else None, height=420,
                                     title="Articles par pays et par thème").update_yaxes(categoryorder="total ascending", title=None),
                        width="stretch")
        cols_aff = [c for c in ("date", "pays", "theme", "titre", "media", "lien", "langue") if c in v]
        st.dataframe(v.sort_values("date", ascending=False)[cols_aff].head(500), hide_index=True, width="stretch",
                     column_config={"lien": st.column_config.LinkColumn("Lien", display_text="ouvrir")})
