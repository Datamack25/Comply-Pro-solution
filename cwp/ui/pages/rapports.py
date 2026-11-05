"""📑 Rapports — générateur centralisé (PDF, HTML interactif, Excel)."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import reports, screening, sources, store, viz
from cwp.exports.common import slug


def render_rapports():
    C.css()
    st.markdown("# 📑 Rapports")
    kind = st.radio("Type de rapport", ["🚨 Veille sanctions (nouveautés)", "🌍 Risque pays", "🧭 Profil d'entité",
                                        "🗄️ Inventaire des données"], horizontal=True)
    if kind.startswith("🚨"):
        _veille()
    elif kind.startswith("🌍"):
        _pays()
    elif kind.startswith("🧭"):
        _entite()
    else:
        _inventaire()


def _dl(cols, pdf=None, html=None, xlsx=None, base="cwp"):
    a, b, c = st.columns(3)
    if pdf is not None:
        a.download_button("📄 PDF", pdf, f"{base}.pdf", "application/pdf", width="stretch")
    if html is not None:
        b.download_button("🌐 HTML interactif", html.encode("utf-8"), f"{base}.html", "text/html", width="stretch")
    if xlsx is not None:
        c.download_button("📊 Excel", xlsx, f"{base}.xlsx", width="stretch")


def _veille():
    d0 = st.date_input("Depuis le", date.today() - timedelta(days=7))
    since = d0.strftime("%Y-%m-%d")
    full = sources.sanctions_consolidees(actives_only=False)
    if full.empty:
        C.empty_state("Aucune liste chargée.", "🗄️ Centre de données → Tout enrichir"); return
    base = full.groupby("liste").premiere_vue.transform("min")
    new = full[(full.premiere_vue >= since) & (full.premiere_vue > base)]
    rem = full[(full.statut == "retiré") & (full.retire_le >= since)]
    news = store.load("actualites")
    if not news.empty:
        news = news[(news.date >= since) & news.mesure_cle.isin(["gel", "liste", "amende", "sanction", "embargo"])]
    st.markdown(viz.kpis([("Nouvelles inscriptions", len(new), f"depuis le {d0:%d/%m/%Y}", "#e66767"),
                          ("Radiations", len(rem), "", "#3987e5"), ("Actualités sanctions", len(news), "", "#f5c542")]),
                unsafe_allow_html=True)
    st.dataframe(new[["premiere_vue", "liste", "nom", "type", "programme", "pays"]], width="stretch", hide_index=True)
    fig = viz.hbar(new.liste.value_counts().rename_axis("liste").reset_index(name="n"), "n", "liste",
                   title="Nouvelles inscriptions par liste") if len(new) else None
    cols = [(c, c) for c in ["liste", "nom", "type", "programme", "pays", "date_inscription", "premiere_vue"]]
    h = reports.generic_html("Rapport de veille sanctions", "Nouvelles inscriptions & radiations", f"Depuis le {d0:%d/%m/%Y}",
                             [("Synthèse", reports.tiles_html([("Inscriptions", len(new)), ("Radiations", len(rem)),
                                                               ("Actualités", len(news))]))]
                             + ([("Répartition", fig)] if fig else [])
                             + [("Nouvelles inscriptions", (new, cols, 500)), ("Radiations", (rem, cols, 200)),
                                ("Actualités", (news, [(c, c) for c in ["date", "entite", "mesure", "pays", "titre", "media"]], 200)
                                 if not news.empty else "<p>Aucune.</p>")],
                             "Rapport de veille sanctions")
    _dl(None, reports.veille_pdf(new, rem, news if not news.empty else pd.DataFrame(), d0.strftime("%d/%m/%Y")), h,
        reports.to_excel({"Inscriptions": new, "Radiations": rem, "Actualités": news}), f"cwp_veille_{since}")


def _pays():
    df = C.pays_risque()
    try:
        from cwp.data.ml import cluster_countries
        seg = cluster_countries(4)[["iso2", "segment"]]
        df = df.merge(seg, on="iso2", how="left")
    except Exception:
        df["segment"] = ""
    focus = st.multiselect("Pays suivis (mis en avant)", df.nom.tolist(),
                           default=[n for n in ["Haïti", "Venezuela", "Nicaragua", "Russie", "Iran"] if n in set(df.nom)])
    iso = df[df.nom.isin(focus)].iso2.tolist()
    fig = viz.world_risk_map(df)
    C.plot(fig, key="rp_map")
    cols = [(c, c.replace("_", " ")) for c in ["nom", "score_risque", "niveau", "gafi", "regime_sanctions",
                                               "nb_entites_sanctionnees", "segment"]]
    h = reports.generic_html("Risque pays · LCB-FT & sanctions", "Cartographie des risques pays", f"{len(df)} pays",
                             [("Carte", fig), ("Pays suivis", (df[df.iso2.isin(iso)], cols)),
                              ("Classement complet", (df.sort_values("score_risque", ascending=False), cols, 260))], "Risque pays")
    _dl(None, reports.country_pdf(df, iso), h, reports.to_excel({"Risque pays": df}), "cwp_risque_pays")


def _entite():
    hist = store.load("entites_profils")
    opts = hist.sort_values("date", ascending=False).drop_duplicates("uid") if not hist.empty else hist
    c1, c2 = st.columns([3, 1])
    if not opts.empty:
        pick = c1.selectbox("Entité déjà analysée", opts.nom + " · " + opts.type + " · " + opts.pays)
        row = opts[(opts.nom + " · " + opts.type + " · " + opts.pays) == pick].iloc[0]
        nom, typ, pays = row.nom, row.type, row.pays
    else:
        nom, typ, pays = c1.text_input("Nom"), "Entité", ""
    if c2.button("Générer", type="primary", width="stretch") and nom:
        with st.spinner("Reconstitution du profil (données locales)…"):
            from cwp.data import profil360
            st.session_state["rep_p"] = profil360.enrich_360(screening.profil(nom, typ, pays, index=C.name_index()))
    p = st.session_state.get("rep_p")
    if p:
        st.markdown(viz.profile_header(p), unsafe_allow_html=True)
        f = viz.contributions_bar(p["contributions"])
        _dl(None, reports.entity_pdf(p), reports.entity_html(p, [f]),
            reports.to_excel({"Correspondances": p["hits"], "Presse": p["presse"]}), f"cwp_profil_{slug(p['nom'])}")
        st.caption("Pour actualiser PPE, presse, LEI et registre, relancez l'analyse en ligne depuis 🧭 Profil d'entité.")


def _inventaire():
    stt = store.status()
    st.dataframe(stt, width="stretch", hide_index=True)
    cols = [(c, c) for c in stt.columns]
    h = reports.generic_html("Inventaire", "Inventaire des données CWP", f"{int(stt.lignes.sum())} lignes",
                             [("Jeux de données", (stt, cols)), ("Journal", (store.journal().tail(200), [(c, c) for c in store.journal().columns]))],
                             "Inventaire des données")
    _dl(None, None, h, store.export_excel(), f"cwp_inventaire_{datetime.now():%Y%m%d}")
