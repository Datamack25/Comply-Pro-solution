"""
🌎 Focus Caraïbes & Amérique latine — rubrique de veille et d'analyse régionale de CWP.

Réutilise les briques communes de la plateforme : classification (cwp.core.classify),
fusion des doublons FR / EN (cwp.core.dedup), tableau et cartes (cwp.ui.components),
exports Weekly Watch (cwp.exports.weekly_watch).

Données pays éditables : data/reference/focus_caraibes_pays.csv
(code,pays,regimes,gafi,ipc,typologies,sources,verifie_le — régimes séparés par « | »,
typologies par « ; »).
"""

import html
import os
import re
import time
from datetime import datetime
from urllib.parse import quote_plus

import feedparser
import pandas as pd
import streamlit as st

from cwp.core import geo
from cwp.core.classify import enrich, is_action
from cwp.exports.weekly_watch import make_pdf, make_png, to_excel_watch
from cwp.services.news import summarize
from cwp.ui import components as C

from cwp.config import COPYRIGHT as AUTHOR, ref_path  # noqa: E402

DATA_FILE = ref_path("focus_caraibes_pays.csv")
NEW_HOURS = 48
PERIODS = {"24 h": 1, "7 jours": 7, "15 jours": 15, "30 jours": 30, "90 jours": 90}

# Nom affiché -> mots utilisés dans la requête Google News (FR / EN)
SEARCH_NAMES = {
    "HT": ("Haïti OR Haiti", "Haiti"), "VE": ("Venezuela", "Venezuela"), "NI": ("Nicaragua", "Nicaragua"),
    "BO": ("Bolivie", "Bolivia"), "VG": ("\"îles Vierges britanniques\"", "\"British Virgin Islands\""),
    "MX": ("Mexique", "Mexico"), "GT": ("Guatemala", "Guatemala"), "HN": ("Honduras", "Honduras"),
    "SV": ("Salvador", "\"El Salvador\""), "CU": ("Cuba", "Cuba"),
    "DO": ("\"République dominicaine\"", "\"Dominican Republic\""), "CO": ("Colombie", "Colombia"),
}

THEMES = {
    "Sanctions & embargos": ("sanctions OR embargo OR OFAC OR \"gel des avoirs\"",
                             "sanctions OR embargo OR OFAC OR \"asset freeze\""),
    "Corruption": ("corruption OR détournement OR \"pots-de-vin\"", "corruption OR bribery OR embezzlement"),
    "Blanchiment & GAFI": ("blanchiment OR GAFI OR \"liste grise\"", "\"money laundering\" OR FATF OR \"grey list\""),
    "Gangs, cartels & armes": ("gang OR cartel OR \"trafic d'armes\" OR terroriste",
                               "gang OR cartel OR \"arms trafficking\" OR terrorist"),
}

TYPOLOGIES = [
    ("Rançons d'enlèvement", "Haïti, Mexique",
     "Virements ou transferts urgents vers un bénéficiaire inconnu, souvent fractionnés entre plusieurs proches de la victime.",
     "Pic soudain de transferts d'une famille vers un même corridor ; motif vague ; montants ronds sur 24 à 72 h."),
    ("Extorsion et taxation illicite", "Haïti, Amérique centrale",
     "Paiements réguliers de commerçants ou de transporteurs à des groupes armés qui contrôlent un territoire ou une route.",
     "Retraits ou paiements récurrents sans contrepartie commerciale ; activité en zone sous contrôle de gangs."),
    ("Trafic d'armes", "Haïti, République dominicaine, États-Unis",
     "Achat d'armes à l'étranger et acheminement par voie maritime ou terrestre, en violation de l'embargo ONU.",
     "Achats répétés chez des armuriers ; frais de fret vers Haïti incohérents avec l'activité déclarée."),
    ("Or et métaux précieux", "Nicaragua, Venezuela",
     "Exportation d'or pour déplacer de la valeur hors des circuits surveillés ou financer des personnes désignées.",
     "Négociant récent ou opaque ; transit par des pays tiers sans logique économique ; lien avec une PPE."),
    ("Soutien matériel à une organisation désignée", "Haïti, Mexique, Venezuela",
     "Tout paiement, bien ou service au profit d'un cartel ou d'un gang désigné FTO/SDGT expose à des poursuites pénales américaines.",
     "Contrepartie liée à une zone contrôlée ; homonymie avec un nom désigné ; paiements de « protection »."),
    ("Corruption et PPE", "Toute la région",
     "Détournement de fonds publics et blanchiment via l'immobilier, les sociétés écrans ou les proches.",
     "Patrimoine sans rapport avec les revenus ; proches et associés de PPE ; structures offshore."),
]


# ---------- Données ----------
@st.cache_data(show_spinner=False)
def load_countries():
    return pd.read_csv(DATA_FILE, dtype=str).fillna("à compléter")


def _gnews(q, lang):
    return (f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={lang}"
            f"&gl={'FR' if lang == 'fr' else 'US'}&ceid={'FR:fr' if lang == 'fr' else 'US:en'}")


def _clean(t, n=280):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_region(codes, theme_keys):
    """Articles Google News par pays et par thème, en français et en anglais.
    Même format que fetch_all() d'app.py, plus « focus_cc » (pays de la requête)."""
    out, seen = [], set()
    for cc in codes:
        fr_name, en_name = SEARCH_NAMES[cc]
        for th in theme_keys:
            q_fr, q_en = THEMES[th]
            for lang, url in (("fr", _gnews(f"({fr_name}) ({q_fr})", "fr")), ("en", _gnews(f"({en_name}) ({q_en})", "en"))):
                try:
                    feed = feedparser.parse(url)
                except Exception:
                    continue
                for e in feed.entries[:15]:
                    link = e.get("link")
                    if not link or (link, cc) in seen:   # un article peut concerner plusieurs pays
                        continue
                    seen.add((link, cc))
                    ts = time.mktime(e.get("published_parsed")) if e.get("published_parsed") else 0
                    src = (e.get("source") or {}).get("title", "") if isinstance(e.get("source"), dict) else ""
                    out.append(dict(theme=th, title=_clean(e.get("title"), 160), desc=_clean(e.get("summary")),
                                    link=link, ts=ts, source=src, focus_cc=cc, lang=lang))
    return sorted(out, key=lambda x: x["ts"], reverse=True)


def _is_new(ts):
    return bool(ts) and time.time() - ts < NEW_HOURS * 3600


# ---------- Post LinkedIn ----------
def build_post(country, title, fact, why, actions, sources, question):
    tag = re.sub(r"[^A-Za-zÀ-ÿ]", "", country)
    lines = [f"📌 Focus Caraïbes & Amérique latine – {country}", "", title.strip(), ""]
    if fact.strip():
        lines += [fact.strip(), ""]
    if why.strip():
        lines += [f"Pourquoi c'est important : {why.strip()}", ""]
    acts = [a.strip(" -•") for a in actions.splitlines() if a.strip()]
    if acts:
        lines += ["Pour une équipe conformité :"] + [f"• {a}" for a in acts] + [""]
    if question.strip():
        lines += [question.strip(), ""]
    if sources.strip():
        lines += [f"Sources : {sources.strip()}", ""]
    lines += [AUTHOR, "", f"#LCBFT #Sanctions #Conformité #{tag} #AmeriqueLatine"]
    return "\n".join(lines)


# ---------- Sous-onglets ----------
def _regional_rows(raw, names):
    """Enrichit les articles et corrige le pays :
    • l'article doit citer le pays de la requête (sinon il est hors sujet : homonymes « Salvador », etc.) ;
    • si le pays détecté n'est pas un pays de la région (ex. l'émetteur « États-Unis »), on retient
      le pays de la requête, qui est bien celui visé."""
    rows = []
    for it in raw:
        r = enrich(it)
        cited = {c for _, c in geo.mentions(r["headline"] + " " + it.get("desc", ""))}
        if it["focus_cc"] not in cited:
            continue
        if r["cc"] not in names:
            r["cc"], r["country"] = it["focus_cc"], names[it["focus_cc"]]
            if r["entity"] in ("—", "États-Unis", "Union européenne", "Royaume-Uni", "Canada", "ONU"):
                r["entity"] = names[it["focus_cc"]]
        rows.append(r)
    return rows


def _tab_weekly(df, h=None):
    codes_all = df["code"].tolist()
    names = dict(zip(df["code"], df["pays"]))
    c1, c2, c3 = st.columns([2, 2, 1])
    period = c1.radio("Période", list(PERIODS), index=1, horizontal=True, key="fc_period")
    sel = c2.multiselect("Pays", codes_all, default=codes_all[:4], format_func=lambda c: names[c], key="fc_pays")
    nmax = c3.slider("Lignes", 5, 50, 20, key="fc_nmax")
    sanc_only = st.toggle("🎯 Uniquement les mesures prononcées (sanction, gel, amende, embargo, liste GAFI)",
                          value=False, key="fc_sanc")
    if not sel:
        st.info("Choisissez au moins un pays.")
        return

    with st.spinner("Collecte de la veille régionale…"):
        raw = fetch_region(tuple(sel), tuple(THEMES))
    rows = _regional_rows(raw, names)

    since = time.time() - PERIODS[period] * 86400
    pool = [r for r in rows if r["ts"] >= since and (not sanc_only or is_action(r))]
    pool = C.prepare_news(pool, enriched=True)[:nmax]      # une information = une ligne (FR / EN fusionnés)

    d1 = datetime.now()
    period_txt = f"Du {datetime.fromtimestamp(since):%d/%m/%Y} au {d1:%d/%m/%Y}"
    label = "Focus Caraïbes & Amérique latine — " + ", ".join(names[c] for c in sel)
    st.markdown(
        f'<div class="hero"><div class="hero-t">Focus Caraïbes <span>— & Amérique latine</span></div>'
        f'<div class="hero-s">{period_txt.upper()} · SANCTIONS · EMBARGOS · CORRUPTION · GAFI · '
        f'MAJ {d1:%d/%m/%Y %H:%M}</div></div>', unsafe_allow_html=True)
    st.markdown(C.table_html(pool), unsafe_allow_html=True)
    st.caption(C.TABLE_NOTE + " Un nom cité dans la presse n'est pas une désignation officielle : vérifiez sur la liste source.")

    e = st.columns([1, 1, 1, 3])
    stamp = f"{d1:%Y%m%d}"
    try:
        e[0].download_button("🖼️ Image (PNG)", make_png(pool, label, period_txt),
                             f"focus_caraibes_{stamp}.png", "image/png", width="stretch", key="fc_png")
    except Exception as ex:
        e[0].caption(f"PNG indisponible : {ex}")
    try:
        e[1].download_button("📄 Rapport PDF", make_pdf(pool, label, period_txt),
                             f"focus_caraibes_{stamp}.pdf", "application/pdf", width="stretch", key="fc_pdf")
    except ImportError:
        e[1].caption("PDF : ajoutez « reportlab » à requirements.txt")
    e[2].download_button("📥 Excel", to_excel_watch(pool), f"focus_caraibes_{stamp}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         width="stretch", key="fc_xlsx")


def _tab_veille(df, h=None):
    names = dict(zip(df["code"], df["pays"]))
    c1, c2 = st.columns([1, 1])
    cc = c1.selectbox("Pays", df["code"].tolist(), format_func=lambda c: names[c], key="fc_v_pays")
    th = c2.selectbox("Thème", list(THEMES), key="fc_v_theme")
    with st.spinner("Collecte…"):
        raw = fetch_region((cc,), (th,))
    items = C.prepare_news(_regional_rows(raw, names), enriched=True)
    st.caption(f"{len(items)} information(s) · {len(raw) - len(items)} doublon(s) ou article(s) hors sujet écarté(s) · "
               f"badge NOUVEAU = moins de {NEW_HOURS} h")
    if not items:
        st.info("Aucun article pour cette combinaison.")
    for it in items[:25]:
        C.news_card(dict(it, theme=th), _is_new(it["ts"]), summarize=summarize)
        if st.button("✍️ Préparer un post", key="fcp" + str(abs(hash(it["link"])))):
            st.session_state["fc_post_pays"] = cc
            st.session_state["fc_post_title"] = re.sub(r"\s+-\s+[^-]{2,60}$", "", it["title"]).strip()
            st.session_state["fc_post_sources"] = it["source"]
            st.success("Brouillon pré-rempli dans l'onglet « Post LinkedIn ».")


def _country_card(r):
    regimes = "".join(f"<li>{html.escape(x)}</li>" for x in str(r["regimes"]).split(" | "))
    typos = "".join(f'<span class="chip">{html.escape(x)}</span>' for x in str(r["typologies"]).split(" ; "))
    gafi_col = "#ffb020" if "grise" in r["gafi"].lower() else "#52708a"
    flag = (f'<img src="https://flagcdn.com/w40/{r["code"].lower()}.png" alt="{r["code"]}" '
            f'style="height:18px;width:27px;object-fit:cover;vertical-align:-3px;margin-right:8px;border-radius:2px">')
    st.markdown(f"""<div class="card">
<h3 style="margin-top:0">{flag}{html.escape(r["pays"])}</h3>
<span class="mz" style="color:{gafi_col};border-color:{gafi_col}">GAFI</span>
<span style="color:#cfe3f5">{html.escape(r["gafi"])}</span><br><br>
<span class="mz" style="color:#f5c542;border-color:#f5c542">IPC</span>
<span style="color:#cfe3f5">{html.escape(r["ipc"])}</span>
<div class="meta" style="margin-top:14px">RÉGIMES DE SANCTIONS</div>
<ul style="color:#cfe3f5;margin-top:4px">{regimes}</ul>
<div class="meta">TYPOLOGIES À SURVEILLER</div><div style="margin-top:6px">{typos}</div>
<div class="meta" style="margin-top:10px">Sources : {html.escape(r["sources"])} · vérifié le {html.escape(r["verifie_le"])}</div>
</div>""", unsafe_allow_html=True)


def gafi_mismatch(code: str, texte: str) -> str:
    """Contrôle de cohérence entre la fiche (texte libre) et la liste GAFI de référence (cwp/data/countries.py)."""
    from cwp.data.countries import GAFI_DATE, GAFI_GRISE, GAFI_NOIRE
    t = str(texte or "").lower()
    ref = "noire" if code in GAFI_NOIRE else "grise" if code in GAFI_GRISE else "aucune"
    says_grey = "liste grise" in t and not re.search(r"(pas|plus|sort\w*|retir\w*) (sur|de) la liste grise", t)
    says_black = "liste noire" in t and "pas sur la liste noire" not in t
    fiche = "noire" if says_black else "grise" if says_grey else ("aucune" if t and "compléter" not in t else "")
    if fiche and fiche != ref:
        return (f"Incohérence à corriger : la fiche indique « {texte} » alors que la liste GAFI de référence "
                f"({GAFI_DATE}) donne : {'liste ' + ref if ref != 'aucune' else 'non listé'}.")
    return ""


def _tab_fiches(df):
    view = st.radio("Affichage", ["Fiche pays", "Tableau comparatif"], horizontal=True, key="fc_f_view")
    if view == "Fiche pays":
        names = dict(zip(df["code"], df["pays"]))
        cc = st.selectbox("Pays", df["code"].tolist(), format_func=lambda c: names[c], key="fc_f_pays")
        row = df[df["code"] == cc].iloc[0]
        warn = gafi_mismatch(cc, row["gafi"])
        if warn:
            st.warning(warn)
        _country_card(row)
    else:
        st.dataframe(df.drop(columns=["code"]), width="stretch", hide_index=True)
    st.caption("Pour compléter une fiche, modifiez data/reference/focus_caraibes_pays.csv. "
               "Les cases « à compléter » n'ont pas encore été vérifiées.")


def _tab_typologies():
    for name, where, how, flags in TYPOLOGIES:
        with st.expander(f"{name}  ·  {where}"):
            st.markdown(f"**Mécanisme** — {how}")
            st.markdown(f"**Signaux d'alerte** — {flags}")


def _tab_post(df):
    names = dict(zip(df["code"], df["pays"]))
    st.caption("Format CWP : le fait, pourquoi c'est important, ce que doit faire une équipe conformité, la source.")
    cc = st.selectbox("Pays", df["code"].tolist(), format_func=lambda c: names[c], key="fc_post_pays")
    title = st.text_input("Titre", key="fc_post_title")
    fact = st.text_area("Le fait (1 à 2 phrases, avec la date)", height=90, key="fc_post_fact")
    why = st.text_area("Pourquoi c'est important", height=70, key="fc_post_why")
    actions = st.text_area("Actions pour une équipe conformité (une par ligne)", height=90, key="fc_post_actions")
    question = st.text_input("Question à la communauté (optionnel)", key="fc_post_q")
    sources = st.text_input("Sources (noms uniquement)", key="fc_post_sources")
    post = build_post(names[cc], title, fact, why, actions, sources, question)
    st.text_area("Aperçu du post", post, height=320, key="fc_post_preview_" + str(abs(hash(post))))
    st.download_button("📥 Télécharger le post (.txt)", post.encode("utf-8"),
                       f"post_linkedin_{names[cc]}_{datetime.now():%Y%m%d}.txt", key="fc_post_dl")
    st.warning("Avant de publier : vérifiez chaque nom sur la liste officielle. "
               "Une accusation parue dans la presse reste une allégation.")


# ---------- Point d'entrée ----------
def render_focus_caraibes(ctx: dict | None = None):
    """Point d'entrée de la page (ctx : contexte commun fourni par app.py, non utilisé ici)."""
    st.markdown("# 🌎 Focus Caraïbes & Amérique latine")
    st.caption("Sanctions, embargos, corruption et risque LCB-FT dans la région, Haïti en tête.")
    df = load_countries()
    t1, t6, t2, t3, t4, t5 = st.tabs(["🎯 Weekly Watch régional", "🏝️ Veille Caraïbes & Amérique latine (image / PDF)", "📡 Veille par pays",
                                      "🗺️ Fiches pays", "🕵️ Typologies", "✍️ Post LinkedIn"])
    with t1:
        _tab_weekly(df)
    with t2:
        _tab_veille(df)
    with t6:
        from cwp.ui.pages.generateur_veille import render_generateur
        render_generateur(ctx, region_defaut="🏝️ Caraïbes", pays_defaut=None, key="fcg")   # tous les pays de la Caraïbe
    with t3:
        _tab_fiches(df)
    with t4:
        _tab_typologies()
    with t5:
        _tab_post(df)
