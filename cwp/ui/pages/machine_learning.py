"""🤖 Machine Learning — modèles entraînés sur les CSV de CWP, ré-entraînables d'un clic."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import ml, store, viz


def render_ml():
    C.css()
    st.markdown("# 🤖 Machine Learning")
    st.caption("Les modèles apprennent des données accumulées à chaque enrichissement. Plus vous enrichissez "
               "et validez d'étiquettes, plus ils deviennent précis. Modèles enregistrés dans data/models/.")
    t = st.tabs(["📰 Classifieur d'actualités", "🌍 Segmentation pays", "🧪 Anomalies entités",
                 "🧬 Typologies de sanctions", "📈 Tendance des inscriptions"])
    with t[0]:
        _news()
    with t[1]:
        _countries()
    with t[2]:
        _anom()
    with t[3]:
        _typo()
    with t[4]:
        tr = ml.designation_trend(st.slider("Mois projetés", 3, 18, 6))
        if tr.empty:
            C.empty_state("Historique insuffisant.", "Enrichissez au moins une liste de sanctions.")
        else:
            C.plot(viz.line_trend(tr), key="ml_trend")
            st.caption("Régression linéaire sur les 36 derniers mois (date d'inscription officielle, à défaut date de "
                       "détection par CWP). Indication de tendance, pas une prévision réglementaire.")


def _news():
    ts = ml.training_set()
    m = ml.load_model("news_classifier")
    info = m["info"] if m else {}
    st.markdown(viz.kpis([
        ("Actualités d'entraînement", len(ts), "historique data/actualites.csv", "#00d4ff"),
        ("Étiquettes validées", int((ts.origine == "validé").sum()) if len(ts) else 0, "pèsent 3× plus", "#00ff88"),
        ("Exactitude (val. croisée)", f"{info.get('accuracy', 0):.0%}" if info.get("accuracy") else "—",
         f"F1 macro {info.get('f1_macro', 0):.2f}" if info.get("f1_macro") else "non entraîné", "#f5c542"),
        ("Dernier entraînement", info.get("date", "—"), f"{info.get('classes', 0)} classes", "#9085e9")]),
        unsafe_allow_html=True)
    if st.button("🧠 Entraîner / ré-entraîner le classifieur", type="primary"):
        try:
            with st.spinner("Entraînement (TF-IDF mots + caractères, régression logistique, validation croisée)…"):
                res = ml.train_news_classifier()
            st.session_state["ml_news"] = res
            st.success("Modèle entraîné et enregistré.")
            st.rerun()
        except ValueError as e:
            st.warning(str(e))
    res = st.session_state.get("ml_news")
    if res and "confusion" in res:
        a, b = st.columns([1.2, 1])
        with a:
            C.plot(viz.heatmap(res["confusion"]), key="cm")
        with b:
            st.dataframe(res["report"], width="stretch")
    tt = ml.top_terms()
    if not tt.empty:
        with st.expander("🔍 Mots les plus déterminants par classe (explicabilité)"):
            cls = st.selectbox("Classe", tt.classe.unique())
            C.plot(viz.hbar(tt[tt.classe == cls], "poids", "terme", title=f"Termes pour « {cls} »", text=False), key="tt")
    if m and len(ts):
        st.markdown("<div class='sect'>Revue : désaccords entre le modèle et les règles</div>", unsafe_allow_html=True)
        pr = ml.predict_news(ts.texte.tolist())
        rv = pd.concat([ts.reset_index(drop=True), pr], axis=1)
        dis = rv[(rv.prediction != rv.label) & (rv.origine != "validé")].sort_values("confiance", ascending=False).head(40)
        if dis.empty:
            st.success("Aucun désaccord à revoir.")
        else:
            st.caption("Corrigez la colonne « label » si besoin puis enregistrez : le modèle apprend de vos validations.")
            dis = dis[["uid", "texte", "label", "prediction", "confiance"]].copy()
            ed = st.data_editor(dis, width="stretch", hide_index=True, key="ed_lab",
                                column_config={"label": st.column_config.SelectboxColumn("label", options=list(ml.MEASURE_LABELS)),
                                               "texte": st.column_config.TextColumn(width="large"),
                                               "uid": None},
                                disabled=["texte", "prediction", "confiance"])
            c1, c2 = st.columns(2)
            if c1.button("✅ Enregistrer ces étiquettes"):
                r = ml.save_labels(ed); st.success(f"{r['ajoutes'] + r['maj']} étiquette(s) enregistrée(s).")
            if c2.button("🤝 Accepter toutes les prédictions du modèle"):
                r = ml.save_labels(ed.assign(label=ed.prediction)); st.success(f"{r['ajoutes'] + r['maj']} étiquette(s) enregistrée(s).")
        q = st.text_input("Tester une phrase", "L'OFAC désigne trois sociétés vénézuéliennes pour contournement des sanctions")
        if q:
            p = ml.predict_news([q]).iloc[0]
            st.markdown(f"Prédiction : **{p.prediction_lib}** · confiance {p.confiance:.0%}")


def _countries():
    k = st.slider("Nombre de segments", 3, 6, 4)
    try:
        df = ml.cluster_countries(k)
    except ValueError as e:
        C.empty_state(str(e)); return
    C.plot(viz.scatter_segments(df), key="acp")
    import plotly.express as px
    order = sorted(df.segment.unique())
    fig = px.choropleth(df, locations="iso3", color="segment", hover_name="nom", category_orders={"segment": order},
                        color_discrete_sequence=viz.CAT)
    fig.update_geos(showframe=False, bgcolor=viz.SURFACE, landcolor="#0f2236", showocean=True, oceancolor=viz.BG,
                    projection_type="natural earth", lataxis_range=[-58, 84], showcoastlines=False)
    C.plot(viz.theme(fig, 480, title="Segments de pays (K-means)"), key="segmap")
    prof = df.groupby("segment")[[c for c in ml.COUNTRY_FEATS if c in df]].apply(
        lambda g: g.apply(pd.to_numeric, errors="coerce").mean()).round(2)
    prof["pays"] = df.groupby("segment").nom.apply(lambda s: ", ".join(s.head(8)) + ("…" if len(s) > 8 else ""))
    st.dataframe(prof, width="stretch")
    st.caption("K-means sur les 6 indicateurs WGI standardisés + composantes GAFI / sanctions ; les segments sont "
               "ordonnés par score de risque moyen. L'ACP projette les profils sur 2 axes : deux pays proches ont un profil similaire.")


def _anom():
    c = st.slider("Part attendue d'atypiques", 0.02, 0.3, 0.1)
    try:
        df = ml.entity_anomalies(c)
    except ValueError as e:
        C.empty_state(str(e)); return
    import plotly.express as px
    df["score"] = pd.to_numeric(df.score, errors="coerce")
    fig = px.scatter(df, x="score", y="score_anomalie", color="anomalie", hover_name="nom",
                     color_discrete_map={"atypique": viz.CAT[7], "normal": viz.CAT[0]})
    fig.update_traces(marker=dict(size=11, line=dict(color=viz.SURFACE, width=2)))
    fig.update_xaxes(title="Score de risque"); fig.update_yaxes(title="Score d'anomalie (Isolation Forest)")
    C.plot(viz.theme(fig, 440), key="iso")
    st.dataframe(df[["nom", "type", "pays", "score", "niveau", "anomalie", "score_anomalie", "facteurs"]],
                 width="stretch", hide_index=True)


def _typo():
    k = st.slider("Nombre de typologies", 4, 14, 8)
    if st.button("🧬 Calculer les typologies"):
        try:
            with st.spinner("Vectorisation et regroupement…"):
                st.session_state["typo"] = ml.sanction_typologies(k)
        except ValueError as e:
            st.warning(str(e))
    if "typo" in st.session_state:
        sc, summ = st.session_state["typo"]
        summ["libelle"] = summ.typologie.map(lambda x: f"T{x}")
        C.plot(viz.hbar(summ, "effectif", "libelle", title="Effectif par typologie"), key="typo_bar")
        st.dataframe(summ.drop(columns="libelle"), width="stretch", hide_index=True)
        t = st.selectbox("Explorer une typologie", summ.typologie)
        st.dataframe(sc[sc.typologie == t][["liste", "nom", "type", "programme", "pays", "date_inscription"]].head(200),
                     width="stretch", hide_index=True)
