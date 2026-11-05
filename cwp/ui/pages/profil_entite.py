"""
🧭 Profil d'entité — filtrage sanctions/PPE, presse négative, registres (LEI, SIRENE), carte OSM,
graphe de relations, score explicable, rapports PDF/HTML/Excel. Filtrage en lot d'un fichier.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import profil360, reports, screening, store, viz
from cwp.data.countries import flag_emoji, ref
from cwp.config import COPYRIGHT as X_COPYRIGHT
from cwp.exports.common import slug


def render_profil_entite():
    C.css()
    st.markdown("# 🧭 Profil d'entité")
    idx = C.name_index()
    if idx.empty:
        st.warning("Les listes de sanctions ne sont pas encore chargées : ouvrez le 🗄️ Centre de données et cliquez sur "
                   "« Tout enrichir ». Le profil reste utilisable pour la presse, les registres et le risque pays.")
    else:
        st.caption(f"Base de filtrage : {idx.uid.nunique():,} entrées · {len(idx):,} variantes de noms "
                   f"({', '.join(sorted(idx.liste.unique()))}).".replace(",", " "))

    t_one, t_batch, t_hist = st.tabs(["🔍 Analyse d'une entité", "📋 Filtrage en lot", "🗂️ Historique des profils"])
    with t_one:
        _single(idx)
    with t_batch:
        _batch(idx)
    with t_hist:
        h = store.load("entites_profils")
        if h.empty:
            C.empty_state("Aucun profil enregistré.", "Chaque analyse est ajoutée ici automatiquement.")
        else:
            h["score"] = pd.to_numeric(h.score, errors="coerce")
            st.dataframe(h.sort_values("date", ascending=False), width="stretch", hide_index=True,
                         column_config={"score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100,
                                                                                 format="%.0f")})
            st.download_button("📥 Historique (CSV)", h.to_csv(index=False).encode("utf-8-sig"), "cwp_profils.csv")


def _single(idx):
    r = ref()
    noms = [""] + r.nom.tolist()
    with st.form("profil"):
        c1, c2, c3, c4 = st.columns([2.6, 1, 1.4, 0.8])
        nom = c1.text_input("Nom de la personne, de la société ou du navire", placeholder="ex. Jimmy Cherizier, Sberbank…")
        type_ = c2.selectbox("Type", ["Entité", "Personne", "Navire"])
        pays_n = c3.selectbox("Pays (facultatif)", noms, format_func=lambda x: f"{flag_emoji(r[r.nom == x].iso2.iloc[0])} {x}" if x else "—")
        annee = c4.text_input("Année naiss.", max_chars=4)
        o = st.columns([1.4, 1, 1, 1, 1, 1, 1, 1])
        seuil = o[0].slider("Seuil", 70, 98, 82, help="Score minimal de correspondance (sur 100)")
        on = dict(ppe=o[1].checkbox("PPE", True, help="Wikidata"), presse=o[2].checkbox("Presse", True, help="GDELT"),
                  lei=o[3].checkbox("LEI", True, help="GLEIF"), fr=o[4].checkbox("Registre FR", True, help="SIRENE / RNE"),
                  geo=o[5].checkbox("Carte", True, help="OpenStreetMap"), wikidata=o[6].checkbox("Fiche", True, help="Wikidata + Wikipédia"),
                  sec=o[7].checkbox("SEC", True, help="SEC EDGAR — sociétés cotées US"))
        go = st.form_submit_button("🧭 Analyser", type="primary", width="stretch")
    if go and nom.strip():
        iso = r[r.nom == pays_n].iso2.iloc[0] if pays_n else ""
        with st.spinner("Filtrage des listes, interrogation des registres et de la presse…"):
            p = screening.profil(nom.strip(), type_, iso, annee.strip(), idx, on, seuil)
            p = profil360.enrich_360(p, on)
            screening.sauver_profil(p)
        st.session_state["cwp_profil"] = p
    p = st.session_state.get("cwp_profil")
    if not p:
        C.empty_state("Saisissez un nom puis « Analyser ».",
                      "Listes OFAC · UE · ONU · UK · DG Trésor — PPE Wikidata — presse GDELT — GLEIF — SIRENE — OpenStreetMap")
        return
    for e in p.get("erreurs", []):
        st.caption(f"⚠️ Source non jointe — {e}")

    st.markdown(viz.profile_header(p), unsafe_allow_html=True)
    fig_c = viz.contributions_bar(p["contributions"])

    if "synthese" not in p:
        p = profil360.enrich_360(p, {})
    t0 = st.tabs(["🧠 Synthèse & trames", "🪪 Fiche d'identité", "🏛️ Sur la plateforme", "⚠️ Correspondances", "★ PPE",
                  "📰 Presse négative", "🏢 Registres", "🕸️ Graphe", "🗺️ Carte", "📑 Rapport"])
    with t0[0]:
        _synthese(p)
    with t0[1]:
        _fiche(p)
    with t0[2]:
        _plateforme(p)
    tabs = t0[3:]
    with tabs[0]:
        C.plot(fig_c, key="contrib")
        h = p["hits"]
        if h.empty:
            st.success("Aucune correspondance au-dessus du seuil sur les listes chargées.")
        else:
            st.dataframe(h[["liste", "nom", "variante", "nature", "type", "programme", "pays", "date_naissance",
                            "date_inscription", "score", "niveau", "ajustements"]], width="stretch",
                         hide_index=True, column_config={"score": st.column_config.ProgressColumn(
                             "Score", min_value=0, max_value=100, format="%.0f")})
            st.caption("Forte ≥ 95 · Probable 88–95 · Possible < 88. Une correspondance n'est pas une identification : "
                       "comparer date de naissance, nationalité et identifiants.")
    with tabs[1]:
        ppe = p["ppe_df"]
        if ppe.empty:
            st.info("Aucune fonction publique trouvée (Wikidata couvre surtout les PPE de niveau national).")
        else:
            st.dataframe(ppe, width="stretch", hide_index=True)
    with tabs[2]:
        pr = p["presse"]
        if pr.empty:
            st.info("Aucun article négatif trouvé sur 24 mois (GDELT), ou recherche non lancée.")
        else:
            cnt = pr.categorie.value_counts().rename_axis("categorie").reset_index(name="n")
            a, b = st.columns([1, 2])
            with a:
                C.plot(viz.hbar(cnt, "n", "categorie", title="Articles par catégorie"), key="pr_cat")
            with b:
                pr2 = pr.copy(); pr2["mois"] = pr2.date.str[:7]
                tl = pr2.groupby(["mois", "categorie"], as_index=False).size()
                C.plot(viz.stacked_bar(tl, "mois", "size", "categorie", title="Chronologie"), key="pr_tl")
            st.dataframe(pr.sort_values("date", ascending=False)[["date", "categorie", "titre", "media", "langue", "lien"]],
                         width="stretch", hide_index=True,
                         column_config={"lien": st.column_config.LinkColumn("Lien", display_text="ouvrir")})
    with tabs[3]:
        if not p["lei_df"].empty:
            st.markdown("<div class='sect'>GLEIF — identifiants LEI</div>", unsafe_allow_html=True)
            st.dataframe(p["lei_df"], width="stretch", hide_index=True)
        if not p["fr_df"].empty:
            st.markdown("<div class='sect'>Registre français — SIRENE / RNE</div>", unsafe_allow_html=True)
            st.dataframe(p["fr_df"], width="stretch", hide_index=True)
        if p["lei_df"].empty and p["fr_df"].empty:
            st.info("Aucun registre consulté (personne physique, option désactivée ou aucun résultat).")
    with tabs[4]:
        n, e = viz.profile_graph(p)
        C.html_frame(viz.network_html(n, e, 560), 570)
        st.caption("Glissez les nœuds ; survolez pour le détail. Le graphe relie l'entité à ses inscriptions, "
                   "programmes, pays, alias, fonctions PPE, sociétés mères (LEI), dirigeants et articles.")
    map_html = None
    with tabs[5]:
        pts = []
        if p.get("geo"):
            pts.append(dict(nom=p["nom"], lat=p["geo"]["lat"], lon=p["geo"]["lon"], categorie="Entité analysée",
                            adresse=p["geo"].get("label", "")))
        if not p["fr_df"].empty:
            for _, f in p["fr_df"].iterrows():
                if f.lat:
                    pts.append(dict(nom=f.nom, lat=f.lat, lon=f.lon, categorie="Homonymes registre FR", adresse=f.adresse))
        if pts:
            map_html = viz.osm_map(pd.DataFrame(pts), color_col="categorie", popup_cols=("adresse",), height=480)
            C.html_frame(map_html, 500)
        else:
            st.info("Aucune adresse géolocalisée (activez « Carte OSM » ou renseignez le pays).")
    with tabs[6]:
        st.markdown(f"Rapports signés **{X_COPYRIGHT}**, avec avertissement de non-responsabilité.")
        a, b, c = st.columns(3)
        base = f"cwp_profil_{slug(p['nom'])}"
        try:
            a.download_button("📄 Rapport PDF", reports.entity_pdf(p), f"{base}.pdf", "application/pdf",
                              width="stretch")
        except Exception as ex:
            a.error(f"PDF : {ex}")
        b.download_button("🌐 Rapport HTML interactif", reports.entity_html(p, [fig_c], map_html).encode("utf-8"),
                          f"{base}.html", "text/html", width="stretch")
        c.download_button("📊 Données (Excel)", reports.to_excel({
            "Synthèse": pd.DataFrame([dict(nom=p["nom"], type=p["type"], pays=p.get("pays_nom"), score=p["score"],
                                           niveau=p["niveau"], vigilance=p["vigilance"], date=p["date"])]),
            "Facteurs": pd.DataFrame(p["contributions"], columns=["facteur", "points"]),
            "Correspondances": p["hits"], "PPE": p["ppe_df"], "Presse": p["presse"], "LEI": p["lei_df"],
            "Registre FR": p["fr_df"]}), f"{base}.xlsx", width="stretch")


def _batch(idx):
    st.markdown("Importez votre fichier clients / fournisseurs / bénéficiaires (CSV ou Excel) : chaque nom est filtré "
                "sur les listes de sanctions et de PPE chargées.")
    up = st.file_uploader("Fichier", type=["csv", "xlsx"], key="batch_up")
    if not up:
        return
    df = pd.read_csv(up, dtype=str, sep=None, engine="python") if up.name.endswith(".csv") else pd.read_excel(up, dtype=str)
    c1, c2, c3 = st.columns(3)
    col = c1.selectbox("Colonne des noms", df.columns)
    colp = c2.selectbox("Colonne pays (facultatif)", ["—"] + list(df.columns))
    seuil = c3.slider("Seuil", 75, 98, 88, key="bseuil")
    if st.button(f"Filtrer {len(df)} ligne(s)", type="primary"):
        with st.spinner("Filtrage…"):
            res = screening.batch_screening(df.fillna(""), col, idx, seuil, None if colp == "—" else colp)
        n = (res.alerte == "OUI").sum()
        st.markdown(viz.kpis([("Lignes filtrées", len(res), "", "#00d4ff"), ("Alertes", n, "à analyser", "#e66767"),
                              ("Taux d'alerte", f"{n / max(len(res), 1):.1%}", "", "#f5c542")]), unsafe_allow_html=True)
        st.dataframe(res.sort_values("alerte", ascending=False), width="stretch", hide_index=True)
        st.download_button("📥 Résultat (Excel)", reports.to_excel({"Filtrage": res}), "cwp_filtrage_lot.xlsx")


def _synthese(p):
    sy = p["synthese"]
    st.markdown("<div class='sect'>Synthèse de l'analyste (générée à partir de toutes les sources)</div>", unsafe_allow_html=True)
    st.markdown("<div class='card' style='font-size:1.02rem;line-height:1.6'>" + "<br>".join(html.escape(x) for x in sy["texte"]) + "</div>",
                unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        st.markdown("<div class='sect'>Points d'attention</div>", unsafe_allow_html=True)
        for x in sy["attention"] or ["Aucun point d'attention particulier."]:
            st.markdown(f"- {x}")
    with b:
        st.markdown("<div class='sect'>Prochaines étapes</div>", unsafe_allow_html=True)
        for i, x in enumerate(sy["etapes"], 1):
            st.markdown(f"{i}. {x}")
    st.markdown("<div class='sect'>Trames recommandées pour ce dossier</div>", unsafe_allow_html=True)
    from cwp.pedago import methodes, trames
    for mid, why in p["trames_recommandees"]:
        m = methodes.by_id(mid)
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{m['titre']}**  \n<span class='meta'>{html.escape(why)}</span>", unsafe_allow_html=True)
        from cwp.ui.pages.espace_pedagogique import tpdf, txls
        c2.download_button("📄 PDF", tpdf(mid), f"cwp_trame_{mid}.pdf", "application/pdf", key=f"rp_{mid}", width="stretch")
        c3.download_button("📊 Excel", txls(mid), f"cwp_trame_{mid}.xlsx", key=f"rx_{mid}", width="stretch")
    st.caption("Le mode d'emploi de chaque trame figure en première page du PDF et dans l'onglet « Mode d'emploi » de l'Excel. "
               "Méthodologies complètes : 🎓 Espace pédagogique.")


LABELS = {"description_courte": "Description", "nature": "Nature", "pays": "Pays", "nationalite": "Nationalité",
          "creation": "Création", "naissance": "Naissance", "deces": "Décès", "secteur": "Secteur", "siege": "Siège",
          "dirigeant": "Dirigeant", "president": "Président", "proprietaire": "Propriétaire", "societe_mere": "Société mère",
          "filiales": "Filiales", "bourse": "Cotation", "isin": "ISIN", "lei": "LEI", "site": "Site", "profession": "Profession",
          "fonctions": "Fonctions occupées", "parti": "Parti", "chiffre_affaires": "Chiffre d'affaires (Wikidata)",
          "effectif": "Effectif", "membres_conseil": "Membres du conseil", "wikipedia": "Article Wikipédia"}


def _fiche(p):
    f = p.get("fiche") or {}
    if not f:
        st.info("Aucune fiche Wikidata trouvée (entité peu connue ou option « Fiche » désactivée). "
                "Les registres, la presse et les listes restent consultés.")
    else:
        if f.get("resume"):
            st.markdown(f"<div class='card'>{html.escape(f['resume'])}<div class='srcline'>Source : Wikipédia</div></div>",
                        unsafe_allow_html=True)
        rows = [(LABELS[k], v) for k, v in f.items() if k in LABELS and v]
        st.markdown("".join(f"<div class='fl'><span>{html.escape(k)}</span><span style='text-align:right;max-width:70%'>"
                            f"{html.escape(str(v))}</span></div>" for k, v in rows), unsafe_allow_html=True)
        st.caption(f"Source : Wikidata ({f.get('qid', '')}) — données collaboratives, à recouper avec les registres officiels.")
    fin = p.get("fin_sec", pd.DataFrame())
    if fin is not None and not fin.empty:
        st.markdown("<div class='sect'>Données financières — SEC EDGAR (10-K, en USD)</div>", unsafe_allow_html=True)
        st.dataframe(fin, width="stretch", hide_index=True)
        long = fin.melt(id_vars=["societe", "ticker", "cik", "indicateur"], var_name="exercice", value_name="usd")
        long = long[long.indicateur.isin(["Chiffre d'affaires", "Résultat net"])]
        if not long.empty:
            long["exercice"] = long.exercice.astype(str)
            C.plot(viz.stacked_bar(long.assign(md=long.usd.astype(float) / 1e6), "exercice", "md", "indicateur",
                                   title="Chiffre d'affaires et résultat net (M USD)").update_layout(barmode="group"), key="sec")
    fr = p.get("fr_df", pd.DataFrame())
    if not fr.empty and str(fr.iloc[0].get("ca", "")):
        st.markdown("<div class='sect'>Données financières — registre français</div>", unsafe_allow_html=True)
        st.dataframe(fr[["nom", "siren", "exercice", "ca", "resultat_net", "effectif", "dirigeants"]], width="stretch", hide_index=True)


def _plateforme(p):
    pl = p["plateforme"]
    pays = pl.get("pays") or {}
    st.markdown(viz.kpis([
        ("Actualités archivées", len(pl.get("actualites", [])), "mentionnant l'entité", "#00d4ff"),
        ("Analyses antérieures", len(pl.get("historique", [])), "profils enregistrés", "#9085e9"),
        ("Presse stockée", len(pl.get("presse_stockee", [])), "articles", "#d95926"),
        ("Inscrits du même pays", pl.get("nb_inscrits_pays", 0), p.get("pays_nom") or "pays non renseigné", "#e66767"),
    ]), unsafe_allow_html=True)
    if len(pl.get("actualites", [])):
        st.markdown("<div class='sect'>Actualités de la veille CWP</div>", unsafe_allow_html=True)
        st.dataframe(pl["actualites"][["date", "mesure", "pays", "titre", "media"]], width="stretch", hide_index=True)
    h = pl.get("historique", pd.DataFrame())
    if len(h) > 1:
        st.markdown("<div class='sect'>Évolution du score</div>", unsafe_allow_html=True)
        import plotly.graph_objects as go
        fig = go.Figure(go.Scatter(x=h.date, y=pd.to_numeric(h.score, errors="coerce"), mode="lines+markers",
                                   line=dict(color=viz.CAT[0], width=2), marker=dict(size=8)))
        fig.update_yaxes(range=[0, 100], title="Score")
        C.plot(viz.theme(fig, 300, legend=False), key="hist")
    if pays:
        st.markdown(f"<div class='sect'>Contexte pays — {html.escape(str(pays.get('nom')))}</div>", unsafe_allow_html=True)
        a, b = st.columns(2)
        a.markdown("".join(f"<div class='fl'><span>{k}</span><span>{html.escape(str(v))}</span></div>" for k, v in [
            ("Score pays", f"{float(pays.get('score_risque') or 0):.0f}/100 · {pays.get('niveau')}"), ("Statut GAFI", pays.get("gafi")),
            ("Régime de sanctions majeur", pays.get("regime_sanctions")), ("Entités inscrites", pl.get("nb_inscrits_pays", 0))]),
            unsafe_allow_html=True)
        rg = pl.get("regimes_pays")
        if rg is not None and len(rg):
            with b:
                C.plot(viz.hbar(rg.rename_axis("programme").reset_index(name="n"), "n", "programme",
                                title="Programmes de sanctions liés au pays"), key="rg")
        foc = pl.get("focus")
        if foc:
            st.markdown(f"<div class='card'><b>Focus Caraïbes & Amérique latine</b><br>Régimes : {html.escape(foc.get('regimes', ''))}"
                        f"<br>GAFI : {html.escape(foc.get('gafi', ''))}<br>Typologies : {html.escape(foc.get('typologies', ''))}"
                        f"<div class='srcline'>Vérifié le {html.escape(foc.get('verifie_le', ''))}</div></div>", unsafe_allow_html=True)
        ap = pl.get("actualites_pays")
        if ap is not None and len(ap):
            with st.expander(f"Dernières actualités du pays ({len(ap)})"):
                st.dataframe(ap[["date", "mesure", "entite", "titre"]], width="stretch", hide_index=True)
    ri = pl.get("renseignements")
    if ri is not None and len(ri):
        st.markdown(f"<div class='sect'>🔒 Renseignements internes ({len(ri)})</div>", unsafe_allow_html=True)
        st.dataframe(ri.drop(columns=[c for c in ("uid",) if c in ri]), width="stretch", hide_index=True)
    na = pl.get("notoriete_articles")
    if na is not None and len(na):
        st.markdown(f"<div class='sect'>📰 Articles de notoriété déjà analysés ({len(na)})</div>", unsafe_allow_html=True)
        st.dataframe(na[["date", "score", "niveau", "titre", "media", "lien"]].sort_values("score", ascending=False), width="stretch",
                     hide_index=True, column_config={"lien": st.column_config.LinkColumn("Lien", display_text="ouvrir")})
    elif p.get("type"):
        st.caption("Aucune recherche de notoriété négative enregistrée pour cette entité : 📰 Notoriété négative.")
    for key, lab in (("lei_stocke", "LEI déjà consultés"), ("fr_stocke", "Registre français (déjà consulté)"),
                     ("ppe_stocke", "PPE stockées"), ("osm", "Points OpenStreetMap liés")):
        d = pl.get(key)
        if d is not None and len(d):
            with st.expander(f"{lab} ({len(d)})"):
                st.dataframe(d, width="stretch", hide_index=True)
