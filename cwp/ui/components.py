"""
cwp.ui.components — composants d'interface partagés par toutes les pages :
mentions légales, réglage de langue, cartes d'actualité, tableau Weekly Watch, accès aux données.
"""
from __future__ import annotations

import hashlib
import html
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from cwp import config
from cwp.core import dedup
from cwp.core.classify import SCREEN_COLOR, enrich
from cwp.data import screening, sources, store, viz


def css():
    st.markdown(viz.CSS_EXTRA, unsafe_allow_html=True)


def _mtimes(names):
    return tuple(os.path.getmtime(store.path(n)) if os.path.exists(store.path(n)) else 0 for n in names)


@st.cache_data(show_spinner=False)
def _index(key):
    return screening.build_index()


def name_index() -> pd.DataFrame:
    return _index(_mtimes(list(sources.SANCTION_SOURCES) + ["ppe_wikidata", "renseignements_internes"]))


@st.cache_data(show_spinner=False)
def _sanc(key):
    return sources.sanctions_consolidees()


def sanctions() -> pd.DataFrame:
    return _sanc(_mtimes(list(sources.SANCTION_SOURCES)))


def pays_risque() -> pd.DataFrame:
    df = store.load("pays_risque")
    if df.empty:
        df = sources.build_pays_risque()
    for c in ("score_risque", "nb_entites_sanctionnees", "score_gouvernance"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def html_frame(content: str, height: int):
    import streamlit.components.v1 as components
    components.html(content, height=height, scrolling=False)


def empty_state(msg: str, hint: str = ""):
    st.markdown(f"<div class='card' style='text-align:center;padding:28px'><div style='font-size:1.15rem'>{msg}</div>"
                f"<div class='meta' style='margin-top:6px'>{hint}</div></div>", unsafe_allow_html=True)


def plot(fig, key=None):
    if fig is not None:
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False}, key=key)



# --------------------------------------------------------------------------- #
# Mentions légales (petits caractères)
# --------------------------------------------------------------------------- #
def legal_footer() -> None:
    """Pied de page affiché en bas de chaque page."""
    st.markdown(f"<div class='cwp-legal'><b>{html.escape(config.COPYRIGHT)}</b><br>"
                f"{html.escape(config.DISCLAIMER)}</div>", unsafe_allow_html=True)


def legal_note() -> None:
    """Rappel compact, sous un bloc de résultats."""
    st.markdown(f"<div class='cwp-legal-inline'>{html.escape(config.DISCLAIMER)}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Langue des actualités
# --------------------------------------------------------------------------- #
LANG_LABEL = {"fr": "FR", "en": "EN"}


def lang_mode() -> str:
    return st.session_state.get("cwp_lang_mode", "fr_first")


def lang_selector() -> None:
    st.selectbox("🌐 Langue des actualités", list(config.LANG_MODES), format_func=config.LANG_MODES.get,
                 key="cwp_lang_mode", help="Une information publiée en français et en anglais n'est affichée "
                                           "qu'une fois ; l'autre version reste accessible sous l'article.")


def prepare_news(items: list[dict], enriched: bool = False, with_count: bool = False):
    """Enrichit, filtre selon la langue choisie et fusionne les doublons FR / EN.
    with_count=True : renvoie aussi le nombre d'articles retenus avant fusion."""
    rows = items if enriched else [enrich(i) for i in items]
    rows, prefer = dedup.filter_lang(rows, lang_mode())
    merged = dedup.merge(rows, prefer)
    return (merged, len(rows)) if with_count else merged


def _versions_html(r: dict) -> str:
    vs = [v for v in r.get("versions", []) if v.get("link")]
    if not vs:
        return ""
    links = " · ".join(f'<a href="{html.escape(v["link"])}" target="_blank">{LANG_LABEL.get(v["lang"], v["lang"].upper() or "?")}'
                       f'{" – " + html.escape(v["source"]) if v["source"] else ""}</a>' for v in vs[:4])
    more = f" (+{len(vs) - 4})" if len(vs) > 4 else ""
    return f'<span class="meta">Même information : {links}{more}</span>'


# --------------------------------------------------------------------------- #
# Cartes d'actualité
# --------------------------------------------------------------------------- #
def hits(it: dict, kws: list[str]) -> list[str]:
    t = (it.get("title", "") + " " + it.get("desc", "")).lower()
    return [k for k in kws if k.lower() in t]


def news_card(it: dict, new: bool = False, kws: list[str] | None = None, summarize=None) -> None:
    d = datetime.fromtimestamp(it["ts"]).strftime("%d/%m/%Y %H:%M") if it.get("ts") else "—"
    badge = '<span class="tag new">NOUVEAU</span>' if new else ""
    lang = f'<span class="tag lang">{LANG_LABEL.get(it.get("lang"), "")}</span>' if it.get("lang") else ""
    vers = _versions_html(it)
    st.markdown(f"""<div class="card">{badge}<span class="tag">{html.escape(it.get('theme', ''))}</span>{lang}
<span class="meta">{d} · {html.escape(it.get('source', ''))}</span><br>
<b><a href="{html.escape(it['link'])}" target="_blank">{html.escape(it['title'])}</a></b><br>
<span style="color:#9bb4c9">{html.escape(it.get('desc', ''))}</span><br>
<a class="meta" href="{html.escape(it['link'])}" target="_blank">🔗 Consulter la source</a>{'<br>' + vers if vers else ''}</div>""",
                unsafe_allow_html=True)
    h = hits(it, kws or [])
    if h:
        st.markdown(f'<span class="tag" style="border-color:#ff4d6d;color:#ff4d6d">🚨 ALERTE : {html.escape(", ".join(h))}</span>',
                    unsafe_allow_html=True)
    if summarize and st.button("📝 Résumé", key="s" + hashlib.md5((it["link"] + it.get("theme", "")).encode()).hexdigest()):
        st.info(summarize(it["link"]))


# --------------------------------------------------------------------------- #
# Tableau Weekly Watch
# --------------------------------------------------------------------------- #
FLAG_URL = "https://flagcdn.com/w40/{}.png"


def flag(cc: str) -> str:
    """Drapeau en image (affichage écran)."""
    if len(cc or "") != 2 or not cc.isalpha():
        return ""
    return (f'<img src="{FLAG_URL.format(cc.lower())}" alt="{cc}" '
            f'style="height:14px;width:21px;object-fit:cover;vertical-align:-2px;margin-right:6px;'
            f'border-radius:2px;box-shadow:0 0 0 1px #ffffff22">')


def table_html(rows: list[dict]) -> str:
    heads = ["Entité / cible (*)", "Catégorie", "Description", "Pays (*)", "Mesure", "Montant", "Date", "Autorité / source"]
    th = "".join(f"<th>{h}</th>" for h in heads)
    trs = []
    for r in rows:
        col = SCREEN_COLOR.get(r["mkey"], "#52708a")
        main = html.escape(r["auth"] or r["source"] or "—")
        sub = f'<br><span class="meta">{html.escape(r["source"])}</span>' if r["auth"] and r["source"] else ""
        if r.get("n_media", 1) > 1:
            sub += f'<br><span class="meta">+{r["n_media"] - 1} autre(s) média(s)</span>'
        vers = _versions_html(r)
        pays = f'{flag(r["cc"])} {html.escape(r["country"])}' if r["cc"] else "—"
        date = datetime.fromtimestamp(r["ts"]).strftime("%d/%m/%Y") if r.get("ts") else "—"
        trs.append(
            f'<tr><td class="ent">{html.escape(r["entity"])}</td>'
            f'<td><span class="tag">{html.escape(r["theme"])}</span></td>'
            f'<td><a href="{html.escape(r["link"])}" target="_blank">{html.escape(r["headline"])}</a>'
            f'{"<br>" + vers if vers else ""}</td>'
            f'<td style="white-space:nowrap">{pays}</td>'
            f'<td><span class="mz" style="color:{col};border-color:{col}">{html.escape(r["measure"])}</span></td>'
            f'<td style="white-space:nowrap;font-family:Share Tech Mono;color:{"#f5c542" if r["amount_v"] else "#52708a"}">'
            f'{html.escape(r["amount"])}</td>'
            f'<td class="meta" style="white-space:nowrap">{date}</td>'
            f'<td>{main}{sub}</td></tr>')
    if not trs:
        trs = ['<tr><td colspan="8" class="meta">Aucun élément.</td></tr>']
    return f'<div class="wwrap"><table class="wtable"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


TABLE_NOTE = ("(*) Entité, pays et mesure sont détectés automatiquement à partir du titre. Pour une sanction, un gel, "
              "un embargo ou une liste GAFI, la colonne Pays indique le pays VISÉ (l'émetteur figure dans la colonne "
              "Autorité) ; « — » signifie que le titre ne le précise pas. Une même information parue en français et en "
              "anglais n'apparaît qu'une fois.")
