"""
🗺️ Cartographie — risque pays mondial, sanctions par pays et par programme,
activités à risque LCB-FT d'une ville (OpenStreetMap), entités analysées, actualités par pays.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import reports, sources, store, viz
from cwp.data.countries import iso3, nom


def render_cartographie():
    C.css()
    st.markdown("# 🗺️ Cartographie des risques")
    t = st.tabs(["🌍 Risque pays", "🎯 Sanctions dans le monde", "🏙️ Activités à risque (OpenStreetMap)",
                 "📍 Entités analysées", "📰 Actualités par pays"])
    with t[0]:
        _pays()
    with t[1]:
        _sanctions()
    with t[2]:
        _osm()
    with t[3]:
        _entites()
    with t[4]:
        _news()


def _pays():
    df = C.pays_risque()
    has_wgi = "wgi_corruption" in df and pd.to_numeric(df.wgi_corruption, errors="coerce").notna().any()
    if not has_wgi:
        st.info("Indicateurs de gouvernance de la Banque mondiale absents : score basé sur le GAFI et les sanctions "
                "seulement. Cliquez sur « Enrichir le risque pays » dans le 🗄️ Centre de données.")
    c1, c2 = st.columns([1, 3])
    reg = c1.multiselect("Régions", sorted(df.region.unique()), placeholder="Toutes / tous")
    gafi = c2.multiselect("Statut GAFI", ["Liste noire", "Liste grise", "Aucune"], placeholder="Toutes / tous")
    d = df[df.region.isin(reg)] if reg else df
    d = d[d.gafi.isin(gafi)] if gafi else d
    lv = d.niveau.value_counts()
    st.markdown(viz.kpis([(f"{viz.STATUS_ICON[k]} Risque {k.lower()}", int(lv.get(k, 0)), "pays", viz.STATUS[k])
                          for k in ("Élevé", "Modéré", "Faible")] +
                         [("GAFI liste noire / grise", f"{(d.gafi == 'Liste noire').sum()} / {(d.gafi == 'Liste grise').sum()}",
                           f"plénière du {d.gafi_maj.iloc[0] if 'gafi_maj' in d and len(d) else '—'}", "#fab219")]),
                unsafe_allow_html=True)
    fig = viz.world_risk_map(d)
    C.plot(fig, key="wmap")
    a, b = st.columns([1.1, 1])
    with a:
        top = d.nlargest(20, "score_risque")
        C.plot(viz.hbar(top, "score_risque", "nom", title="20 pays au score le plus élevé"), key="top20")
    with b:
        comp = d.nlargest(20, "score_risque")[["nom", "score_gouvernance", "score_gafi", "score_regime", "score_sanctions"]]
        comp = comp.melt("nom", var_name="composante", value_name="points")
        comp["composante"] = comp.composante.map({"score_gouvernance": "Gouvernance (WGI)", "score_gafi": "GAFI",
                                                  "score_regime": "Régime de sanctions", "score_sanctions": "Entités inscrites"})
        comp["points"] = pd.to_numeric(comp.points, errors="coerce")
        f2 = viz.stacked_bar(comp, "points", "nom", "composante", title="Décomposition du score", height=640)
        f2.update_traces(orientation="h"); f2.update_yaxes(categoryorder="total ascending", title=None)
        f2.update_xaxes(title=None); f2.update_layout(legend_title_text="")
        C.plot(f2, key="decomp")
    show = ["nom", "region", "score_risque", "niveau", "gafi", "regime_sanctions", "nb_entites_sanctionnees"] + \
           [c for c in d.columns if c.startswith(("wgi_", "cpi", "basel"))]
    st.dataframe(d.sort_values("score_risque", ascending=False)[show], width="stretch", hide_index=True,
                 column_config={"score_risque": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f")})
    e1, e2, e3 = st.columns(3)
    e1.download_button("📄 Rapport PDF risque pays", reports.country_pdf(d), "cwp_risque_pays.pdf", "application/pdf",
                       width="stretch")
    e2.download_button("🌐 Rapport HTML interactif", reports.generic_html(
        "Risque pays · LCB-FT & sanctions", "Cartographie des risques pays", f"{len(d)} pays",
        [("Carte mondiale", fig), ("Classement", (d.sort_values("score_risque", ascending=False),
                                                   [(c, c.replace("_", " ")) for c in show], 260)),
         ("Sources", "<p>Banque mondiale (WGI) · GAFI · OFAC · Union européenne · Nations unies · FCDO · DG Trésor</p>")],
        "Risque pays").encode("utf-8"), "cwp_risque_pays.html", "text/html", width="stretch")
    e3.download_button("📊 Excel", reports.to_excel({"Risque pays": d}), "cwp_risque_pays.xlsx", width="stretch")
    st.caption("Méthode : gouvernance WGI (40 pts) + GAFI (noire 35 / grise 18) + régime de sanctions (12) + "
               "entités inscrites (13, échelle log) ± IPC importé (5). Élevé ≥ 55 · Modéré 35–55 · Faible < 35.")


def _sanctions():
    sc = C.sanctions()
    if sc.empty:
        C.empty_state("Aucune liste de sanctions chargée.", "🗄️ Centre de données → Tout enrichir")
        return
    lists = st.multiselect("Listes", sorted(sc.liste.unique()), default=sorted(sc.liste.unique()), placeholder="Toutes / tous")
    types = st.multiselect("Types", sorted(sc.type.unique()), default=sorted(sc.type.unique()), placeholder="Toutes / tous")
    d = sc[sc.liste.isin(lists) & sc.type.isin(types)]
    has_reg = "pays_regime" in d and d.pays_regime.fillna("").ne("").any()
    mode = st.radio("Rattacher chaque inscription au…", ["pays visé par le régime de sanctions", "pays de la personne / entité"],
                    horizontal=True, index=0 if has_reg else 1, key="carto_mode",
                    help="Pays visé : programme OFAC, régime UE / UK / ONU (ex. une société chinoise inscrite au titre du "
                         "programme Iran compte pour l'Iran). Pays de l'entité : nationalité, adresse ou pavillon.")
    col = "pays_regime" if mode.startswith("pays visé") and has_reg else "pays"
    if mode.startswith("pays visé") and not has_reg:
        st.info("Les listes stockées datent d'avant la distinction pays visé / pays de l'entité : relancez "
                "« Tout enrichir » dans le 🗄️ Centre de données pour en profiter.")
    ex = d.assign(p=d[col].fillna("").str.split(r" \| ")).explode("p")
    ex = ex[ex.p.fillna("") != ""]
    cnt = ex.groupby("p").size().rename("n").reset_index()
    cnt["iso3"], cnt["nom"] = cnt.p.map(iso3), cnt.p.map(nom)
    st.markdown(viz.kpis([("Entrées", f"{len(d):,}".replace(",", " "), "actives", "#e66767"),
                          ("Personnes", f"{(d.type == 'Personne').sum():,}".replace(",", " "), "", "#3987e5"),
                          ("Entités", f"{(d.type == 'Entité').sum():,}".replace(",", " "), "", "#199e70"),
                          ("Navires / aéronefs", f"{d.type.isin(['Navire', 'Aéronef']).sum():,}".replace(",", " "), "", "#c98500"),
                          ("Pays concernés", cnt.p.nunique(), "", "#9085e9")]), unsafe_allow_html=True)
    C.plot(viz.bubble_map(cnt[cnt.iso3 != ""]), key="bub")
    a, b = st.columns(2)
    with a:
        C.plot(viz.hbar(cnt.nlargest(15, "n"), "n", "nom", title="15 pays les plus représentés"), key="cnt15")
    with b:
        pg = d.assign(prog=d.programme.str.split(r" \| ")).explode("prog")
        pg = pg[pg.prog.fillna("") != ""].groupby(["liste", "prog"]).size().rename("n").reset_index()
        pg = pg.sort_values("n", ascending=False).groupby("liste").head(12)
        C.plot(viz.treemap(pg, ["liste", "prog"], "n", title="Programmes / régimes par liste"), key="tree")
    from cwp.data.ml import designation_trend
    tr = designation_trend()
    if not tr.empty:
        C.plot(viz.line_trend(tr), key="trend")


def _osm():
    st.markdown("Cartographiez les établissements sensibles en LCB-FT d'une ville à partir d'**OpenStreetMap** "
                "(banques, bureaux de change, transferts d'argent, casinos, prêteurs sur gages, bijouteries…). "
                "Chaque recherche enrichit `data/osm_poi.csv`.")
    with st.form("osm"):
        c1, c2, c3 = st.columns([2, 3, 1])
        lieu = c1.text_input("Ville ou zone", "Port-au-Prince, Haïti")
        cats = c2.multiselect("Catégories", list(sources.OSM_CATEGORIES),
                              default=["Banques", "Bureaux de change", "Transfert d'argent", "Casinos & jeux"])
        km = c3.number_input("Rayon (km)", 2, 60, 15)
        go = st.form_submit_button("🛰️ Interroger OpenStreetMap", type="primary")
    if go:
        try:
            with st.spinner("Requête Overpass…"):
                res = sources.osm_poi(lieu, cats, km)
            st.success(f"{len(res)} point(s) récupéré(s) et ajouté(s) aux données.")
        except Exception as e:
            st.error(f"OpenStreetMap : {e}")
    poi = store.load("osm_poi")
    if poi.empty:
        C.empty_state("Aucun point d'intérêt stocké.", "Lancez une première requête ci-dessus.")
        return
    lieux = sorted(poi.lieu.unique())
    sel = st.selectbox("Zone affichée", lieux, index=lieux.index(lieu) if lieu in lieux else 0)
    d = poi[poi.lieu == sel]
    vc = d.categorie.value_counts().rename_axis("categorie").reset_index(name="n")
    a, b = st.columns([2.4, 1])
    with a:
        C.html_frame(viz.osm_map(d, color_col="categorie", popup_cols=("categorie", "operateur", "adresse"), heat=True), 560)
    with b:
        C.plot(viz.hbar(vc, "n", "categorie", title=f"{len(d)} points — {sel}"), key="poi_cat")
        ops = d[d.operateur != ""].operateur.value_counts().head(10).rename_axis("operateur").reset_index(name="n")
        if not ops.empty:
            C.plot(viz.hbar(ops, "n", "operateur", title="Principaux opérateurs"), key="poi_ops")
    st.dataframe(d[["categorie", "nom", "operateur", "adresse", "lat", "lon", "osm_id"]], width="stretch", hide_index=True)
    st.caption("Données © contributeurs OpenStreetMap (licence ODbL). La couverture varie selon les pays.")


def _entites():
    h = store.load("entites_profils")
    h = h[(h.lat.fillna("") != "")] if not h.empty and "lat" in h else pd.DataFrame()
    if h.empty:
        C.empty_state("Aucune entité géolocalisée.", "Analysez des entités dans 🧭 Profil d'entité avec l'option « Carte OSM ».")
        return
    C.html_frame(viz.osm_map(h, color_col="niveau", popup_cols=("type", "score", "vigilance", "listes")), 560)


@st.cache_data(show_spinner=False)
def _reclassify_cached(key, df):
    from cwp.core import geo
    df = df.copy()
    res = [geo.country_of(t, r, m, au) for t, r, m, au in
           zip(df.titre.fillna(""), df.resume.fillna(""), df.mesure_cle.fillna(""), df.autorite.fillna(""))]
    df["pays_iso2"], df["pays"] = [x[0] for x in res], [x[1] for x in res]
    return df


def _reclassify(a):
    """Recalcule le pays des actualités archivées avec la détection actuelle (pays visé, mots entiers)."""
    import os
    if a.empty or "titre" not in a:
        return a
    key = os.path.getmtime(store.path("actualites")) if os.path.exists(store.path("actualites")) else 0
    return _reclassify_cached(key, a)


def _news():
    a = store.load("actualites")
    if a.empty:
        C.empty_state("Aucune actualité archivée.", "🗄️ Centre de données → Enrichir les actualités")
        return
    a = _reclassify(a)
    if "groupe" in a:   # une information parue en FR et en EN n'est comptée qu'une fois
        a = pd.concat([a[a.groupe.fillna("") == ""], a[a.groupe.fillna("") != ""].drop_duplicates("groupe")])
    a = a[a.pays_iso2 != ""]
    cnt = a.groupby("pays_iso2").size().rename("n").reset_index()
    cnt["iso3"], cnt["nom"] = cnt.pays_iso2.map(iso3), cnt.pays_iso2.map(nom)
    C.plot(viz.bubble_map(cnt, title=f"{len(a)} actualités géolocalisées par pays"), key="newsmap")
    mm = a.groupby(["pays", "mesure"]).size().rename("n").reset_index()
    top = mm.groupby("pays").n.sum().nlargest(12).index
    C.plot(viz.stacked_bar(mm[mm.pays.isin(top)], "pays", "n", "mesure", title="Type de mesure par pays (12 premiers)"),
           key="newsbar")
