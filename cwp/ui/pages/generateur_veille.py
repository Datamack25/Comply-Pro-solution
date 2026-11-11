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

    # 0. Raccourcis : règlent région, types d'information et titre en un clic
    def _appliquer(nom):
        reg, cats_, titre = V.RACCOURCIS[nom]
        st.session_state[f"{key}_region"] = reg
        st.session_state[f"{key}_cats"] = cats_
        st.session_state[f"{key}_titre"] = titre
        st.session_state.pop(f"{key}_pays_{reg}", None)       # « tous les pays » de la région

    st.markdown('<div class="meta">RACCOURCIS</div>', unsafe_allow_html=True)
    rc = st.columns(len(V.RACCOURCIS))
    for col, nom in zip(rc, V.RACCOURCIS):
        col.button(nom, key=f"{key}_rc_{_slug(nom)}", on_click=_appliquer, args=(nom,), width="stretch")

    # 1. Périmètre géographique
    regions = [V.MONDE] + list(V.REGIONS)
    # valeurs initiales posées une seule fois dans la session (les raccourcis peuvent ensuite les modifier)
    st.session_state.setdefault(f"{key}_region", region_defaut if region_defaut in regions else regions[0])
    st.session_state.setdefault(f"{key}_cats", ["🎯 Sanctions & gels d'avoirs", "🚫 Embargos & contrôle des exportations"])
    c1, c2 = st.columns([1, 2])
    region = c1.selectbox("Région", regions, key=f"{key}_region")
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
    periode = st.radio("Période", list(V.PERIODES), index=1, horizontal=True, key=f"{key}_per")
    d1, d2, d3 = st.columns([1.4, 1.2, 1])
    tri = d1.selectbox("Trier par", V.TRIS, key=f"{key}_tri")
    prononcees = d2.toggle("🎯 Uniquement les mesures prononcées", value=False, key=f"{key}_pron",
                           help="Sanction, gel, amende, embargo, liste GAFI effectivement décidés "
                                "(exclut opinions, projets, analyses).")
    nmax = d3.slider("Lignes max.", 5, 100, 30, key=f"{key}_nmax")
    synthese = st.text_area("Synthèse de l'analyste (facultatif, ajoutée en tête du PDF)", height=70, key=f"{key}_syn")

    if not st.button("🔎 Générer la veille (image + PDF)", type="primary", key=f"{key}_go"):
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
        rows = C.prepare_news(rows, enriched=True)            # une information = une ligne (FR / EN fusionnés)
        rows = V.trier(sorted(rows, key=lambda r: r.get("ts") or 0, reverse=True)[:nmax], tri)   # les plus récentes, puis tri

    now = datetime.now()
    jours = V.PERIODES[periode]
    period_txt = (f"Dernières 24 h — du {now - timedelta(days=1):%d/%m/%Y %H:%M} au {now:%d/%m/%Y %H:%M}" if jours == 1
                  else f"Du {now - timedelta(days=jours):%d/%m/%Y} au {now:%d/%m/%Y}")
    if monde_entier:
        perimetre = "Monde entier"
    elif tous:
        perimetre = f"{V.court(region)} (tous les pays)"
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


@st.cache_data(show_spinner=False, max_entries=8)
def _apercu_pdf(pdf: bytes, max_pages: int = 6) -> list[bytes]:
    """Pages du PDF en images, pour l'aperçu à l'écran (pypdfium2)."""
    import io

    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf)
    out = []
    for i in range(min(len(doc), max_pages)):
        buf = io.BytesIO()
        page = doc[i]
        page.render(scale=1.6).to_pil().save(buf, "PNG")
        page.close()
        out.append(buf.getvalue())
    doc.close()
    return out


def _afficher(res: dict, key: str) -> None:
    """Affichage principal : la veille en IMAGE et en PDF (format Weekly Watch), prêts à télécharger."""
    rows = res["rows"]
    st.markdown(f"#### {res['title']}")
    st.caption(f"{res['period_txt']} · {res['label']} · {len(rows)} information(s)")
    for line in res["intro"]:
        st.caption(line)
    if not rows:
        st.info("Aucune information ne correspond à ces critères sur la période. Élargissez la période, le type "
                "d'information ou le périmètre (les petits pays sont peu couverts par la presse).")

    base = f"veille_{res['slug']}_{res['stamp']}"
    png = pdf = None
    try:
        png = make_png(rows, res["label"], res["period_txt"], title=res["title"])
    except Exception as ex:
        st.caption(f"Image indisponible : {ex}")
    try:
        pdf = make_pdf(rows, res["label"], res["period_txt"], title=res["title"], intro=res["intro"])
    except ImportError:
        st.caption("PDF : ajoutez « reportlab » à requirements.txt")

    e = st.columns([1, 1, 1, 2])
    if png:
        e[0].download_button("🖼️ Télécharger l'image (PNG)", png, f"{base}.png", "image/png", width="stretch",
                             type="primary", key=f"{key}_png")
    if pdf:
        e[1].download_button("📄 Télécharger le PDF", pdf, f"{base}.pdf", "application/pdf", width="stretch",
                             type="primary", key=f"{key}_pdf")
    e[2].download_button("📥 Excel", to_excel_watch(rows), f"{base}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
                         key=f"{key}_xlsx")

    v_img, v_pdf, v_tab = st.tabs(["🖼️ Image", "📄 PDF", "📋 Tableau interactif (liens)"])
    with v_img:
        if png:
            st.image(png, width="stretch")
    with v_pdf:
        if pdf:
            try:
                pages = _apercu_pdf(pdf)
                for i, p in enumerate(pages, 1):
                    st.image(p, caption=f"Page {i}", width="stretch")
            except Exception:
                st.caption("Aperçu PDF indisponible : téléchargez le fichier.")
    with v_tab:
        st.markdown(C.table_html(rows), unsafe_allow_html=True)
    st.caption(C.TABLE_NOTE + " Un nom cité dans la presse n'est pas une désignation officielle : vérifiez sur la liste source.")
