"""
cwp.ui.pages.glossaire_fraudes — Onglet « Glossaire des fraudes » de CWP.

50 typologies (blanchiment, FT, sanctions, paiements, identité, escroqueries, fiscal,
corruption, abus de marché, traite) : description, signaux transactionnels, parades.
Recherche + filtre par catégorie, export PDF (sélection complète) et PNG (fiche ou planche).

Intégration :  from cwp.ui.pages.glossaire_fraudes import render_glossaire_fraudes
               with tab_glossaire: render_glossaire_fraudes()
"""
from __future__ import annotations

import json
import unicodedata
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

from cwp.exports import common as X
from cwp.content.glossaire_fraudes import CATEGORIES, FRAUDES

PNG_MAX = 10  # nombre max de fiches dans une planche image

CAT_COLOR = {  # une teinte par famille, sobre
    "Blanchiment": "#1F3A5F", "Financement du terrorisme": "#C0392B",
    "Contournement de sanctions": "#7B3FC4", "Fraude aux paiements": "#D68910",
    "Fraude identitaire & crédit": "#16808A", "Escroqueries": "#B03A6F",
    "Fraude fiscale": "#2E8B57", "Corruption & fraude interne": "#8E5A2B",
    "Abus de marché": "#3D5A99", "Traite & exploitation": "#6B6B6B",
}


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


def _numbered() -> list[dict]:
    """Fiches triées par catégorie puis nom, avec un numéro stable 1-50."""
    order = {c: i for i, c in enumerate(CATEGORIES)}
    items = sorted(FRAUDES, key=lambda f: (order.get(f["categorie"], 99), _norm(f["nom"])))
    return [{**f, "num": i + 1} for i, f in enumerate(items)]


# --------------------------------------------------------------------------- #
# Rendu PDF
# --------------------------------------------------------------------------- #
def _card(f: dict, width: float):
    s = X.styles()
    col = CAT_COLOR.get(f["categorie"], X.HEX["navy"])
    alias = f' <font size="8.5" color="{X.HEX["grey"]}">— {X.esc(f["alias"])}</font>' if f.get("alias") else ""
    title = Paragraph(f'<font color="{X.HEX["gold"]}">{f["num"]:02d}</font>  {X.esc(f["nom"])}{alias}',
                      s["card_title"])
    tag = Paragraph(f'<font color="{col}">{X.esc(f["categorie"]).upper()}</font>', s["tag"])
    desc = Paragraph(X.esc(f["description"]), s["body"])
    half = (width - 16) / 2
    ident = [Paragraph("COMMENT L'IDENTIFIER", s["label"]),
             Spacer(1, 2), Paragraph(X.esc(f["identifier"]), s["small"])]
    comb = [Paragraph("COMMENT LA COMBATTRE", s["label"]),
            Spacer(1, 2), Paragraph(X.esc(f["combattre"]), s["small"])]
    two = Table([[ident, comb]], colWidths=[half, half])
    two.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), X.ROW_ALT),
        ("LINEBEFORE", (0, 0), (0, 0), 2, X.colors.HexColor(X.HEX["red"])),
        ("LINEBEFORE", (1, 0), (1, 0), 2, X.colors.HexColor(X.HEX["green"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    inner = Table([[title], [tag], [desc], [two]], colWidths=[width - 2])
    inner.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, X.LINE),
        ("LINEABOVE", (0, 0), (-1, 0), 2, X.colors.HexColor(col)),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 8), ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, 1), 2), ("BOTTOMPADDING", (0, 2), (-1, 2), 6),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 10),
    ]))
    return KeepTogether([inner, Spacer(1, 9)])


def _flowables(items: list[dict], width: float, subtitle: str, with_sections: bool = True) -> list:
    out = [X.header_card("Glossaire des fraudes", "Typologies de fraude & de blanchiment", subtitle, width),
           Spacer(1, 12)]
    current = None
    for f in items:
        if with_sections and f["categorie"] != current:
            current = f["categorie"]
            n = sum(1 for x in items if x["categorie"] == current)
            out += [Spacer(1, 4), X.section_title(f"{current} · {n} fiche{'s' if n > 1 else ''}", width),
                    Spacer(1, 7)]
        out.append(_card(f, width))
    out += [Spacer(1, 6), X.footer_line(
        "Glossaire à visée pédagogique : signaux indicatifs, à adapter à l'approche par les risques "
        "de l'établissement (GAFI, TRACFIN, ACPR)", width)]
    return out


def glossaire_pdf(items: list[dict], subtitle: str) -> bytes:
    w = X.CONTENT_W
    return X.build_pdf(_flowables(items, w, subtitle), title="CWP — Glossaire des fraudes")


def glossaire_png(items: list[dict], subtitle: str) -> bytes:
    w = X.CONTENT_W
    return X.pdf_to_png(X.build_fitted_pdf(lambda: _flowables(items, w, subtitle, with_sections=len(items) > 1),
                                           title="CWP — Glossaire"))


@st.cache_data(show_spinner=False)
def _cached(kind: str, nums: tuple, subtitle: str) -> bytes:
    by_num = {f["num"]: f for f in _numbered()}
    items = [by_num[n] for n in nums]
    return glossaire_pdf(items, subtitle) if kind == "pdf" else glossaire_png(items, subtitle)


# --------------------------------------------------------------------------- #
# Aperçu HTML
# --------------------------------------------------------------------------- #
def _card_html(f: dict) -> str:
    c, col = X.HEX, CAT_COLOR.get(f["categorie"], X.HEX["navy"])
    h = lambda t: X.esc(t).replace("<br/>", "<br>")  # noqa: E731
    alias = f'<span style="color:{c["grey"]};font-weight:400;font-size:13px"> — {h(f["alias"])}</span>' \
        if f.get("alias") else ""
    return f"""
<div style="border:1px solid {c['line']};border-top:3px solid {col};border-radius:8px;padding:12px 14px;
            background:#fff;color:{c['ink']};break-inside:avoid;margin-bottom:12px">
  <div style="font-weight:700;color:{c['navy']};font-size:15.5px">
     <span style="color:{c['gold']}">{f['num']:02d}</span>&nbsp; {h(f['nom'])}{alias}</div>
  <div style="color:{col};font-size:10.5px;font-weight:700;letter-spacing:.05em;margin:2px 0 6px">
     {h(f['categorie']).upper()}</div>
  <div style="font-size:13.5px;line-height:1.5;color:{c['ink']}">{h(f['description'])}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:9px">
    <div style="background:{c['row_alt']};border-left:3px solid {c['red']};padding:7px 9px;font-size:12.5px;color:{c['ink']};line-height:1.45">
      <div style="font-size:10px;font-weight:700;color:{c['grey']};letter-spacing:.05em">COMMENT L'IDENTIFIER</div>
      {h(f['identifier'])}</div>
    <div style="background:{c['row_alt']};border-left:3px solid {c['green']};padding:7px 9px;font-size:12.5px;color:{c['ink']};line-height:1.45">
      <div style="font-size:10px;font-weight:700;color:{c['grey']};letter-spacing:.05em">COMMENT LA COMBATTRE</div>
      {h(f['combattre'])}</div>
  </div>
</div>"""


# --------------------------------------------------------------------------- #
# Onglet
# --------------------------------------------------------------------------- #
def render_glossaire_fraudes() -> None:
    items_all = _numbered()

    st.markdown("# 🕵️ Glossaire des fraudes")
    st.caption(f"{len(items_all)} typologies courantes — description, signaux dans une transaction "
               f"et moyens de lutte. Filtrez, puis exportez en PDF ou en image.")

    a, b = st.columns([1.3, 2])
    q = a.text_input("🔎 Rechercher", placeholder="mule, RIB, crypto, TVA, sanctions…", key="gl_q")
    cats = b.multiselect("Catégories", CATEGORIES, key="gl_cats", placeholder="Toutes les catégories")

    items = [f for f in items_all
             if (not cats or f["categorie"] in cats)
             and (not q or _norm(q) in _norm(" ".join([f["nom"], f.get("alias", ""), f["categorie"],
                                                         f["description"], f["identifier"], f["combattre"]])))]

    # Compteurs par catégorie
    counts = {c: sum(1 for f in items if f["categorie"] == c) for c in CATEGORIES}
    chips = " ".join(
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:2px 9px;border-radius:12px;'
        f'border:1px solid {CAT_COLOR[c]};color:{CAT_COLOR[c]};font-size:12px">{c} · {n}</span>'
        for c, n in counts.items() if n)
    st.markdown(chips or "", unsafe_allow_html=True)

    if not items:
        st.info("Aucune fiche ne correspond à la recherche.")
        return

    # ---- Exports
    subtitle = (f"{len(items)} fiche{'s' if len(items) > 1 else ''}"
                + (f" · {', '.join(cats)}" if cats else " · toutes catégories")
                + (f" · recherche « {q} »" if q else "")
                + f" · édition du {datetime.now():%d/%m/%Y}")
    nums = tuple(f["num"] for f in items)
    stamp = f"{datetime.now():%Y%m%d}"

    with st.container(border=True):
        st.markdown("**Exporter**")
        e1, e2, e3 = st.columns([1, 1, 1.4])
        with e1:
            st.download_button(f"⬇️ PDF — {len(items)} fiche(s)", _cached("pdf", nums, subtitle),
                               f"cwp_glossaire_fraudes_{stamp}.pdf", "application/pdf",
                               width="stretch")
        with e2:
            if len(items) <= PNG_MAX:
                st.download_button(f"🖼️ Image — {len(items)} fiche(s)", _cached("png", nums, subtitle),
                                   f"cwp_glossaire_planche_{stamp}.png", "image/png",
                                   width="stretch")
            else:
                st.button(f"🖼️ Image (≤ {PNG_MAX} fiches)", disabled=True, width="stretch",
                          help="Filtrez la liste ou utilisez l'export d'une fiche à droite.")
        with e3:
            labels = {f"{f['num']:02d} · {f['nom']}": f["num"] for f in items}
            pick = st.selectbox("Fiche unique", list(labels), key="gl_pick", label_visibility="collapsed")
            n = labels[pick]
            f1 = next(f for f in items if f["num"] == n)
            st.download_button("🖼️ Image de cette fiche",
                               _cached("png", (n,), f"Fiche {n:02d} · {f1['categorie']}"),
                               f"cwp_fiche_{n:02d}_{X.slug(f1['nom'])}.png", "image/png",
                               width="stretch")
        st.download_button("💾 Données (.json)", json.dumps({"_signature": X.signature_meta(), "fiches": items},
                                      ensure_ascii=False, indent=2).encode(),
                           f"cwp_glossaire_{stamp}.json", "application/json")

    # ---- Fiches (2 colonnes)
    left, right = st.columns(2, gap="medium")
    for i, f in enumerate(items):
        (left if i % 2 == 0 else right).markdown(_card_html(f), unsafe_allow_html=True)
