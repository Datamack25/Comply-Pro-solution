"""
🖨️ Générateur de veille — documents de veille à la demande (PNG / PDF / Excel, format Weekly Watch).

L'utilisateur choisit :
  • la région (Caraïbes, Amérique latine, Europe, Afrique…) ou le monde entier ;
  • un ou plusieurs pays, ou « tous les pays » de la région ;
  • le type d'information : sanctions & gels, embargos, amendes, listes GAFI, réglementation / circulaires,
    enquêtes & corruption, ou toutes les actualités conformité ;
  • la période, et éventuellement « uniquement les mesures prononcées ».

Le tableau reprend les colonnes du Weekly Watch : Entité / cible (*), Catégorie, Description (+ « Même information »),
Pays (*), Mesure, Montant, Date, Autorité / source. Logique de collecte : cwp/services/veille_ciblee.py.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta

import streamlit as st

from cwp.exports.weekly_watch import make_pdf, make_png, to_excel_watch
from cwp.services import news
from cwp.services import veille_ciblee as V
from cwp.ui import components as C


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:50] or "veille"


def render_generateur(ctx: dict | None = None, region_defaut: str | None = None, pays_defaut: list[str] | None = None,
                      key: str = "gv") -> None:
    """ctx : contexte commun d'app.py (actualités déjà collectées) ; region_defaut / pays_defaut : pré-sélection
    (ex. Focus Caraïbes -> « 🏝️ Caraïbes » / ["HT"]) ; key : préfixe des widgets (page appelante)."""
    st.caption("Composez votre document de veille : région, pays (ou tous les pays), type d'information et période, "
               "puis téléchargez-le en image (PNG), PDF ou Excel — au format du tableau Weekly Watch.")

    # 1. Périmètre géographique
    regions = [V.MONDE] + list(V.REGIONS)
    c1, c2 = st.columns([1, 2])
    region = c1.selectbox("Région", regions, index=regions.index(region_defaut) if region_defaut in regions else 0,
                          key=f"{key}_region")
    liste = V.pays_region(region)
    noms = dict(liste)
    if region == V.MONDE:
        opts = ["🌍 Tous les pays"] + [c for c, _ in liste]
        tous_label = "🌍 Tous les pays"
    else:
        opts = [V.TOUS] + [c for c, _ in liste]
        tous_label = V.TOUS
    defaut = [c for c in (pays_defaut or []) if c in noms] or [tous_label]
    sel = c2.multiselect("Pays concerné(s)", opts, default=defaut, key=f"{key}_pays_{region}",
                         format_func=lambda c: c if c.startswith(("🌍", "🌐")) else f"{V.CT.flag_emoji(c)} {noms[c]}",
                         help="Choisissez un ou plusieurs pays, ou « tous les pays » de la région.")
    tous = (not sel) or tous_label in sel
    codes = [c for c, _ in liste] if tous else [c for c in sel if c in noms]
    if tous and region != V.MONDE and len(sel) > 1:
        st.caption("« Tous les pays » est sélectionné : les autres pays choisis sont déjà inclus.")

    # 2. Type d'information
    cats = st.multiselect("Type d'information", V.CHOIX,
                          default=["🎯 Sanctions & gels d'avoirs", "🚫 Embargos & contrôle des exportations"],
                          key=f"{key}_cats",
                          help="« Toutes les actualités conformité » couvre tous les types SAUF les actualités générales "
                               "(faits divers, politique, sécurité…), à ajouter séparément si besoin.")
    if not cats:
        cats = [V.TOUTES]

    # Titre du document
    t1, t2 = st.columns([1, 1])
    nom_doc = t1.selectbox("Titre du document", V.TITRES + [V.TITRE_LIBRE], key=f"{key}_titre")
    if nom_doc == V.TITRE_LIBRE:
        nom_doc = t2.text_input("Titre personnalisé", "Bulletin de veille", key=f"{key}_titre_libre").strip() or "Bulletin de veille"

    # 3. Période / options
    d1, d2, d3 = st.columns([1.6, 1.2, 1])
    periode = d1.radio("Période", list(V.PERIODES), index=1, horizontal=True, key=f"{key}_per")
    prononcees = d2.toggle("🎯 Uniquement les mesures prononcées", value=False, key=f"{key}_pron",
                           help="Sanction, gel, amende, embargo, liste GAFI effectivement décidés "
                                "(exclut opinions, projets, analyses).")
    nmax = d3.slider("Lignes max.", 5, 100, 30, key=f"{key}_nmax")
    synthese = st.text_area("Synthèse de l'analyste (facultatif, ajoutée en tête du PDF)", height=70, key=f"{key}_syn")

    if not st.button("🔎 Lancer la veille et générer le tableau", type="primary", key=f"{key}_go"):
        if st.session_state.get(f"{key}_res"):
            _afficher(st.session_state[f"{key}_res"], key)
        else:
            st.info("Réglez les filtres puis cliquez sur « Lancer la veille ». La collecte prend quelques secondes.")
        return

    cats_fetch = tuple(V.CATEGORIES) if (V.TOUTES in cats or cats == [V.GENERALE]) else tuple(c for c in cats if c in V.CATEGORIES)
    monde_entier = region == V.MONDE and tous
    with st.spinner("Collecte de la veille (presse FR / EN, flux de la plateforme, historique)…"):
        raw = V.collecter(() if monde_entier else tuple(codes), cats_fetch)
        if ctx:
            raw += ctx.get("items", [])
            try:
                raw += news.fetch_actions()
            except Exception:
                pass
        raw += V.archives()
        rows = V.selectionner(raw, None if monde_entier else set(codes), cats, V.PERIODES[periode], prononcees)
        rows = C.prepare_news(rows, enriched=True)[:nmax]     # une information = une ligne (FR / EN fusionnés)

    now = datetime.now()
    period_txt = f"Du {now - timedelta(days=V.PERIODES[periode]):%d/%m/%Y} au {now:%d/%m/%Y}"
    if monde_entier:
        perimetre = "Monde entier"
    elif tous:
        perimetre = f"{V.court(region)} — tous les pays"
    else:
        perimetre = ", ".join(noms[c] for c in codes)
    types = " · ".join(V.court(c) for c in cats)
    zone = perimetre if len(perimetre) <= 40 else V.court(region)
    title = f"{nom_doc} — {zone}"
    label = types if zone == perimetre else f"{types} — {perimetre}"
    intro = [f"Synthèse : {synthese.strip()}"] if synthese.strip() else []
    if not tous and codes:
        st_df = V.statut_pays(codes)
        intro.append("Statut des pays : " + " · ".join(
            f"{r['Pays']} — GAFI : {r.iloc[1]} ; régime de sanctions : {r['Régime de sanctions']}" for _, r in st_df.iterrows()))
    st.session_state[f"{key}_res"] = dict(rows=rows, title=title, label=label, period_txt=period_txt, intro=intro,
                                          stamp=f"{now:%Y%m%d}", slug=_slug(perimetre), n_raw=len(raw))
    _afficher(st.session_state[f"{key}_res"], key)


def _afficher(res: dict, key: str) -> None:
    rows = res["rows"]
    st.markdown(
        f'<div class="hero"><div class="hero-t">{res["title"]}</div>'
        f'<div class="hero-s">{res["period_txt"].upper()} · {res["label"].upper()} · {len(rows)} INFORMATION(S)</div></div>',
        unsafe_allow_html=True)
    for line in res["intro"]:
        st.caption(line)
    if not rows:
        st.info("Aucune information ne correspond à ces critères sur la période. Élargissez la période, le type "
                "d'information ou le périmètre (les petits pays sont peu couverts par la presse).")
    st.markdown(C.table_html(rows), unsafe_allow_html=True)
    st.caption(C.TABLE_NOTE + " Un nom cité dans la presse n'est pas une désignation officielle : vérifiez sur la liste source.")

    base = f"veille_{res['slug']}_{res['stamp']}"
    e = st.columns([1, 1, 1, 3])
    try:
        png = make_png(rows, res["label"], res["period_txt"], title=res["title"])
        e[0].download_button("🖼️ Image (PNG)", png, f"{base}.png", "image/png", width="stretch", key=f"{key}_png")
    except Exception as ex:
        png = None
        e[0].caption(f"PNG indisponible : {ex}")
    try:
        e[1].download_button("📄 Rapport PDF", make_pdf(rows, res["label"], res["period_txt"], title=res["title"],
                                                         intro=res["intro"]),
                             f"{base}.pdf", "application/pdf", width="stretch", key=f"{key}_pdf")
    except ImportError:
        e[1].caption("PDF : ajoutez « reportlab » à requirements.txt")
    e[2].download_button("📥 Excel", to_excel_watch(rows), f"{base}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
                         key=f"{key}_xlsx")
    if png:
        with st.expander("👁️ Aperçu de l'image"):
            st.image(png, width="stretch")
