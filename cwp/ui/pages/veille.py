"""📡 Veille — actualités sanctions & embargos (cartes), veille réglementaire et générateur de documents de veille."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from cwp.exports.weekly_watch import to_excel_news
from cwp.services import news
from cwp.ui import components as C


def render(ctx: dict) -> None:
    items, new_links, kws = ctx["items"], ctx["new_links"], ctx["keywords"]
    st.markdown("# 📡 Veille")
    tab_sanctions, tab_reglementaire, tab_gen = st.tabs(["🚨 Sanctions & embargos", "📜 Veille réglementaire",
                                                         "🖨️ Générateur de veille (PDF / image)"])
    with tab_sanctions:
        col1, col2 = st.columns([2, 1])
        q = col1.text_input("Recherche", placeholder="ex : Russie, AMLA, OFAC…")
        sel = col2.multiselect("Thèmes", list(news.THEMES), default=list(news.THEMES))
        c1, c2 = st.columns(2)
        only_new = c1.checkbox("Uniquement les nouveautés", value=False)
        only_alert = c2.checkbox("Uniquement les alertes", value=False)
        merged, n_in = C.prepare_news(items, with_count=True)   # une information = une carte, quelle que soit la langue
        shown = [i for i in merged
                 if i["theme"] in sel
                 and (not q or q.lower() in (i["title"] + i["desc"]).lower())
                 and (not only_new or i["link"] in new_links)
                 and (not only_alert or C.hits(i, kws))]
        doubles = n_in - len(merged)
        st.caption(f"{len(shown)} information(s) affichée(s)"
                   + (f" · {doubles} doublon(s) fusionné(s) (même information en FR / EN ou dans plusieurs médias)" if doubles > 0 else ""))
        if shown:
            st.download_button("📥 Export Excel", to_excel_news(shown), f"veille_conformite_{datetime.now():%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        for it in shown:
            C.news_card(it, it["link"] in new_links, kws, news.summarize)
    with tab_reglementaire:
        from cwp.ui.pages.veille_reglementaire import render_veille_reglementaire
        render_veille_reglementaire()
    with tab_gen:
        from cwp.ui.pages.generateur_veille import render_generateur
        render_generateur(ctx, key="gv")
