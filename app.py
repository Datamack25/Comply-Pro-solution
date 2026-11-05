"""
CWP – Compliance Watch Platform · point d'entrée Streamlit.

    streamlit run app.py

Ce fichier ne contient que la navigation : chaque page vit dans cwp/ui/pages/,
la logique métier dans cwp/core/ (classification, pays, doublons) et cwp/data/ (listes, risques).
"""
from __future__ import annotations

import importlib

import streamlit as st

from cwp import config

st.set_page_config(page_title=f"{config.APP_SHORT} – {config.APP_NAME}", page_icon="🛡️", layout="wide")

from cwp.core.classify import enrich  # noqa: E402  (après set_page_config)
from cwp.services import news  # noqa: E402
from cwp.ui import components as C  # noqa: E402
from cwp.ui import state, theme  # noqa: E402

# (libellé du menu, module de cwp.ui.pages, fonction d'entrée)
PAGES = [
    ("🏠 Dashboard", "dashboard", "render"),
    ("📡 Veille", "veille", "render"),
    ("🧭 Profil d'entité", "profil_entite", "render_profil_entite"),
    ("📰 Notoriété négative", "notoriete", "render_notoriete"),
    ("🇭🇹 Haïti & Caraïbes", "haiti", "render_haiti"),
    ("🎓 Espace pédagogique", "espace_pedagogique", "render_espace_pedagogique"),
    ("🗺️ Cartographie", "cartographie", "render_cartographie"),
    ("🤖 Machine Learning", "machine_learning", "render_ml"),
    ("📑 Rapports", "rapports", "render_rapports"),
    ("🗄️ Centre de données", "centre_donnees", "render_centre_donnees"),
    ("🔎 OpenSanctions", "reference", "render_opensanctions"),
    ("⚖️ Textes de loi", "reference", "render_textes_loi"),
    ("📅 Calendrier réglementaire", "reference", "render_calendrier"),
    ("📌 Regulatory Flash", "regulatory_flash", "render_regulatory_flash"),
    ("📚 Glossaire", "reference", "render_glossaire"),
    ("🕵️ Glossaire des fraudes", "glossaire_fraudes", "render_glossaire_fraudes"),
    ("🌎 Focus Caraïbes", "focus_caraibes", "render_focus_caraibes"),
    ("🔗 Sources officielles", "reference", "render_sources"),
]
# Pages qui reçoivent le contexte commun (actualités, mots-clés…) en argument
WITH_CTX = {"dashboard", "veille", "focus_caraibes", "centre_donnees", "reference"}

theme.apply()

# ---------- Barre latérale ----------
with st.sidebar:
    st.markdown(f'<div class="brand">{config.APP_SHORT}</div><div class="sub">{config.APP_NAME.upper()}</div>',
                unsafe_allow_html=True)
    page = st.radio("Navigation", [p[0] for p in PAGES], label_visibility="collapsed")
    C.lang_selector()
    kw_in = st.text_area("🚨 Mots-clés d'alerte (un par ligne)", "\n".join(state.load_keywords()),
                         placeholder="Russie\nIran\nNom d'une entité")
    keywords = [k.strip() for k in kw_in.splitlines() if k.strip()]
    state.save_keywords(keywords)
    if st.button("🔄 Rafraîchir la veille", width="stretch"):
        news.fetch_all.clear()
        st.session_state["_archive_news"] = True
        st.rerun()
    st.markdown(f"<div class='cwp-legal' style='margin-top:1rem'>{config.COPYRIGHT}</div>", unsafe_allow_html=True)

# ---------- Contexte commun ----------
items = news.fetch_all()
if st.session_state.pop("_archive_news", False):   # chaque rafraîchissement enrichit data/actualites.csv
    try:
        news.archive(items)
    except Exception:
        pass
seen = state.load_seen()
ctx = dict(items=items, seen=seen, new_links=({i["link"] for i in items} - seen) if seen else set(), keywords=keywords,
           fetch_all=news.fetch_all, fetch_actions=news.fetch_actions, enrich=enrich)

# ---------- Page ----------
label, module, func = next(p for p in PAGES if p[0] == page)
fn = getattr(importlib.import_module(f"cwp.ui.pages.{module}"), func)
if module in WITH_CTX:
    fn(ctx)
else:
    fn()

C.legal_footer()   # © + avertissement, en petits caractères, au bas de chaque page
