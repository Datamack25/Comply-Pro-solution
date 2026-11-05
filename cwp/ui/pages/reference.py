"""Pages de référence : OpenSanctions, textes de loi, calendrier, glossaire, sources officielles."""
from __future__ import annotations

import html

import streamlit as st

from cwp.content.concepts import load_concepts
from cwp.content.legal import LEGAL
from cwp.content.references import CALENDAR, OFFICIAL_LINKS
from cwp.services import opensanctions as osn


def render_opensanctions(ctx: dict | None = None) -> None:
    st.markdown("# 🔎 OpenSanctions")
    st.caption("Recherche dans les listes de sanctions, PPE et entités à risque agrégées par OpenSanctions (clé API requise). "
               "Une correspondance de nom n'est pas une identification : comparez date de naissance, nationalité et identifiants.")
    c1, c2 = st.columns([3, 1])
    q = c1.text_input("Nom d'une personne, société ou navire")
    schema = c2.selectbox("Type", ["Thing", "Person", "Company", "Organization", "Vessel"])
    if q:
        try:
            for r in osn.search(q, schema):
                p = r.get("properties", {})
                st.markdown(f"""<div class="card"><span class="tag">{html.escape(str(r.get('schema', '')))}</span>
<b><a href="https://www.opensanctions.org/entities/{html.escape(r['id'])}/" target="_blank">{html.escape(r.get('caption', ''))}</a></b><br>
<span class="meta">Pays : {html.escape(', '.join(p.get('country', [])) or '—')} · Thèmes : {html.escape(', '.join(p.get('topics', [])) or '—')}</span><br>
<span class="meta">Listes : {html.escape(', '.join(r.get('datasets', [])[:6]))}</span></div>""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"OpenSanctions : {e}")
    st.markdown("[Données en vrac gratuites (usage non commercial)](https://www.opensanctions.org/datasets/)")


def render_textes_loi(ctx: dict | None = None) -> None:
    st.markdown("# ⚖️ Textes de loi")
    st.caption("Vérifiez les références sur Légifrance. Ajoutez vos textes dans cwp/content/legal.py.")
    for name, ref, desc, url in LEGAL:
        st.markdown(f'<div class="card"><b><a href="{url}" target="_blank">{html.escape(name)}</a></b> '
                    f'<span class="tag">{html.escape(ref)}</span><br><span style="color:#9bb4c9">{html.escape(desc)}</span></div>',
                    unsafe_allow_html=True)


def render_calendrier(ctx: dict | None = None) -> None:
    st.markdown("# 📅 Calendrier réglementaire")
    st.caption("Dates indicatives : vérifiez toujours sur EUR-Lex / sites officiels.")
    for d, t, desc in CALENDAR:
        st.markdown(f'<div class="card"><span class="tag">{d}</span><b>{html.escape(t)}</b><br>'
                    f'<span style="color:#9bb4c9">{html.escape(desc)}</span></div>', unsafe_allow_html=True)


def render_glossaire(ctx: dict | None = None) -> None:
    df = load_concepts()
    st.markdown(f"# 📚 Glossaire — {len(df)} concepts")
    col1, col2 = st.columns([2, 1])
    q = col1.text_input("Rechercher un concept")
    cat = col2.selectbox("Catégorie", ["Toutes"] + sorted(df.categorie.unique()))
    if cat != "Toutes":
        df = df[df.categorie == cat]
    if q:
        df = df[df.apply(lambda r: q.lower() in " ".join(map(str, r)).lower(), axis=1)]
    for _, r in df.iterrows():
        with st.expander(f"{r.terme}  ·  {r.categorie}"):
            st.markdown(f"**Définition** — {r.definition}")
            st.markdown(f"**Décorticage** — {r.decorticage}")
            st.markdown(f"**Actualité / échéance** — {r.actualite}")


def render_sources(ctx: dict | None = None) -> None:
    st.markdown("# 🔗 Sources officielles")
    st.caption("Toute décision (gel, refus d'entrée en relation, déclaration de soupçon) doit reposer sur ces sources.")
    for n, u in OFFICIAL_LINKS.items():
        st.markdown(f'<div class="card"><a href="{u}" target="_blank">{html.escape(n)}</a></div>', unsafe_allow_html=True)
