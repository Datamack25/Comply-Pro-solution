"""🏠 Dashboard — Weekly Watch : sanctions, gels, amendes, embargos et listes GAFI prononcés."""
from __future__ import annotations

import html
import time
from collections import Counter
from datetime import datetime

import pandas as pd
import streamlit as st

from cwp.content.concepts import load_concepts
from cwp.core.classify import enrich, is_action
from cwp.exports.weekly_watch import make_pdf, make_png, to_excel_watch
from cwp.services import news
from cwp.ui import components as C
from cwp.ui import state

PERIODS = {"24 h": 1, "7 jours": 7, "30 jours": 30}


def _official_lists_banner():
    try:
        from cwp.data.sources import sanctions_consolidees
        full = sanctions_consolidees(actives_only=False)
        if full.empty:
            return
        base = full.groupby("liste").premiere_vue.transform("min")
        wk = (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        new = full[(full.premiere_vue >= wk) & (full.premiere_vue > base)]
        act = int((full.statut != "retiré").sum())
        st.markdown(f'<div class="card"><span class="tag">LISTES OFFICIELLES</span><span class="meta">'
                    f'{act:,} entrées actives · {full.liste.nunique()} listes · '
                    f'<b style="color:#00ff88">{len(new)}</b> nouvelle(s) inscription(s) détectée(s) sur 7 jours · '
                    f'{int((full.statut == "retiré").sum())} radiation(s) — détail : 🗄️ Centre de données</span></div>'
                    .replace(",", " "), unsafe_allow_html=True)
    except Exception:
        pass


def render(ctx: dict) -> None:
    items, new_links, kws = ctx["items"], ctx["new_links"], ctx["keywords"]
    links = {i["link"] for i in items}
    raw = items + [i for i in news.fetch_actions() if i["link"] not in links]
    rows_all = sorted([enrich(i) for i in raw], key=lambda r: r["ts"], reverse=True)
    hero = st.empty()

    c = st.columns(4)
    c[0].markdown(f'<div class="card"><div class="meta">ARTICLES</div><div class="kpi">{len(items)}</div></div>', unsafe_allow_html=True)
    c[1].markdown(f'<div class="card"><div class="meta">NOUVEAUX</div><div class="kpi">{len(new_links)}</div></div>', unsafe_allow_html=True)
    c[2].markdown(f'<div class="card"><div class="meta">THÈMES</div><div class="kpi">{len(news.THEMES)}</div></div>', unsafe_allow_html=True)
    c[3].markdown(f'<div class="card"><div class="meta">CONCEPTS</div><div class="kpi">{len(load_concepts())}</div></div>', unsafe_allow_html=True)
    _official_lists_banner()

    c1, c2, c3 = st.columns([1.3, 1.7, 1])
    period = c1.radio("Période", list(PERIODS), index=1, horizontal=True)
    view = c2.radio("Affichage", ["🎯 Sanctions & embargos prononcés", "📰 Toutes les actualités"], horizontal=True)
    nmax = c3.slider("Lignes du tableau", 5, 50, 20)
    sanc_only = view.startswith("🎯")

    since = time.time() - PERIODS[period] * 86400
    in_period = [r for r in rows_all if r["ts"] >= since]
    keep = is_action if sanc_only else (lambda r: True)
    pool = [r for r in in_period if keep(r)]
    fallback = not pool
    if fallback:  # aucune mesure récente : on affiche les dernières mesures connues (plus anciennes)
        pool = [r for r in rows_all if keep(r)]
    pool = C.prepare_news(pool, enriched=True)        # langue choisie + fusion des doublons FR / EN
    rows = pool[:nmax]

    d1 = datetime.now()
    if not fallback:
        d0 = datetime.fromtimestamp(since)
    else:
        stamps = [r["ts"] for r in rows if r["ts"]]
        d0 = datetime.fromtimestamp(min(stamps)) if stamps else d1
    period_txt = f"Du {d0:%d/%m/%Y} au {d1:%d/%m/%Y}"
    label = ("Sanctions & embargos prononcés" if not fallback else "Dernières sanctions & embargos connus") if sanc_only \
        else "Dernières actualités sécurité financière"
    hero.markdown(
        f'<div class="hero"><div class="hero-t">Weekly Watch <span>— Sécurité financière</span></div>'
        f'<div class="hero-s">{period_txt.upper()} · SANCTIONS · GELS D\'AVOIRS · AMENDES · LISTES GAFI · EMBARGOS · '
        f'MAJ {d1:%d/%m/%Y %H:%M}</div></div>', unsafe_allow_html=True)

    # Pays visés les plus cités (après fusion des doublons : un fait = une occurrence)
    cnt = Counter((r["cc"], r["country"]) for r in pool if r["cc"])
    if cnt:
        chips = "".join(f'<span class="chip">{C.flag(cc)} {html.escape(n)}<b>{v}</b></span>' for (cc, n), v in cnt.most_common(10))
        st.markdown(f'<div class="meta" style="margin:6px 0">PAYS / ZONES LES PLUS CITÉS</div>{chips}', unsafe_allow_html=True)

    st.markdown(f"### {'🎯' if sanc_only else '📰'} {label}")
    if fallback:
        st.info("Aucune sanction ni embargo prononcé sur la période choisie : affichage des dernières mesures connues, plus anciennes.")
    if sanc_only:
        st.caption("Seules les décisions effectivement prises sont retenues (sanction, gel, amende, embargo, liste GAFI). "
                   "Documentaires, opinions, appels, projets et simples actualités sont exclus.")
    st.markdown(C.table_html(rows), unsafe_allow_html=True)
    st.caption(C.TABLE_NOTE)

    e = st.columns([1, 1, 1, 3])
    stamp = f"{d1:%Y%m%d}"
    try:
        e[0].download_button("🖼️ Image (PNG)", make_png(rows, label, period_txt), f"weekly_watch_{stamp}.png",
                             "image/png", width="stretch")
    except Exception as ex:
        e[0].caption(f"PNG indisponible : {ex}")
    try:
        e[1].download_button("📄 Rapport PDF", make_pdf(rows, label, period_txt), f"weekly_watch_{stamp}.pdf",
                             "application/pdf", width="stretch")
    except ImportError:
        e[1].caption("PDF : ajoutez « reportlab » à requirements.txt")
    e[2].download_button("📥 Excel", to_excel_watch(rows), f"weekly_watch_{stamp}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")

    merged_items = C.prepare_news(items)
    alerts = [i for i in merged_items if C.hits(i, kws)]
    shown = set()
    if alerts:
        st.markdown(f"### 🚨 Alertes ({len(alerts)})")
        for it in alerts[:8]:
            C.news_card(it, it["link"] in new_links, kws, news.summarize)
            shown.add(it["link"])
    with st.expander("🗂️ Vue détaillée en cartes (avec résumé)"):
        for it in [i for i in merged_items if i["link"] not in shown][:15]:
            C.news_card(it, it["link"] in new_links, kws, news.summarize)

    state.save_seen(ctx["seen"] | links)
