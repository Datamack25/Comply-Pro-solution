"""
cwp.exports.common — Socle d'export PDF / PNG commun aux onglets CWP.

- Polices DejaVu embarquées (assets/fonts) : accents et symboles (☐ ☑ é è à ç…) OK,
  ce qui corrige les carrés ▯ visibles sur les anciens exports.
- PDF généré avec ReportLab, PNG obtenu en rastérisant ce même PDF (pypdfium2)
  → l'image et le PDF sont strictement identiques.

Dépendances : reportlab, pypdfium2, pillow
"""
from __future__ import annotations

import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --------------------------------------------------------------------------- #
# Palette CWP (reprise du modèle « Weekly Watch »)
# --------------------------------------------------------------------------- #
GOLD = colors.HexColor("#C9A227")
GOLD_LIGHT = colors.HexColor("#EADFB4")
CREAM = colors.HexColor("#FAF6EA")
ROW_ALT = colors.HexColor("#F8F6F0")
NAVY = colors.HexColor("#1F3A5F")
INK = colors.HexColor("#2B2B2B")
GREY = colors.HexColor("#7A7A7A")
LINE = colors.HexColor("#E4E0D5")
PURPLE = colors.HexColor("#7B3FC4")
RED = colors.HexColor("#C0392B")
ORANGE = colors.HexColor("#D68910")
GREEN = colors.HexColor("#2E8B57")

HEX = {  # mêmes couleurs pour l'aperçu HTML Streamlit
    "gold": "#C9A227", "gold_light": "#EADFB4", "cream": "#FAF6EA", "row_alt": "#F8F6F0",
    "navy": "#1F3A5F", "ink": "#2B2B2B", "grey": "#7A7A7A", "line": "#E4E0D5",
    "purple": "#7B3FC4", "red": "#C0392B", "orange": "#D68910", "green": "#2E8B57",
}

# --------------------------------------------------------------------------- #
# Polices
# --------------------------------------------------------------------------- #
from cwp import config as _cfg  # noqa: E402

_FONT_DIRS = [
    _cfg.FONTS_DIR,
    "/usr/share/fonts/truetype/dejavu",
]
try:  # matplotlib embarque DejaVu : bon filet de sécurité sur Streamlit Cloud
    import matplotlib

    _FONT_DIRS.append(os.path.join(matplotlib.get_data_path(), "fonts", "ttf"))
except Exception:
    pass

FONT, FONT_B, FONT_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
UNICODE_OK = False


def _register_fonts() -> None:
    global FONT, FONT_B, FONT_I, UNICODE_OK
    for d in _FONT_DIRS:
        reg, bold, ital = (os.path.join(d, f) for f in
                           ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"))
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("CWP", reg))
            pdfmetrics.registerFont(TTFont("CWP-B", bold))
            pdfmetrics.registerFont(TTFont("CWP-I", ital if os.path.exists(ital) else reg))
            FONT, FONT_B, FONT_I, UNICODE_OK = "CWP", "CWP-B", "CWP-I", True
            return


_register_fonts()

BOX_EMPTY = "☐" if UNICODE_OK else "[ ]"
BOX_CHECKED = "☑" if UNICODE_OK else "[x]"


def esc(text: str) -> str:
    """Échappe le texte pour les Paragraph ReportLab (et l'HTML)."""
    return (str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))


# --------------------------------------------------------------------------- #
# Styles
# --------------------------------------------------------------------------- #
def S(name, size=9.5, font=None, color=INK, leading=None, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=font or FONT, fontSize=size, textColor=color,
                          leading=leading or size * 1.38, alignment=TA_LEFT, **kw)


def styles() -> dict:
    return {
        "kicker": S("kicker", 8, FONT_B, GOLD, spaceAfter=2),
        "title": S("title", 19, FONT, GOLD, leading=23),
        "subtitle": S("subtitle", 10, FONT, GREY),
        "label": S("label", 7.2, FONT_B, GREY, leading=9),
        "value": S("value", 9.5, FONT, INK),
        "section": S("section", 8.5, FONT_B, NAVY, leading=11),
        "body": S("body", 9.3, FONT, INK, leading=13.4),
        "body_b": S("body_b", 9.3, FONT_B, INK, leading=13.4),
        "small": S("small", 8.2, FONT, INK, leading=11.2),
        "small_grey": S("small_grey", 7.6, FONT, GREY, leading=10),
        "footer": S("footer", 7, FONT, GREY, leading=9),
        "num": S("num", 13, FONT_B, GOLD, leading=15),
        "card_title": S("card_title", 11, FONT_B, NAVY, leading=14),
        "tag": S("tag", 7.2, FONT_B, PURPLE, leading=9),
    }


# --------------------------------------------------------------------------- #
# Blocs graphiques réutilisables
# --------------------------------------------------------------------------- #
def header_card(kicker: str, title: str, subtitle: str, width: float) -> Table:
    st = styles()
    cell = [Paragraph(esc(kicker).upper(), st["kicker"]),
            Paragraph(esc(title), st["title"]),
            Spacer(1, 3),
            Paragraph(esc(subtitle), st["subtitle"])]
    t = Table([[cell]], colWidths=[width], cornerRadii=[8, 8, 8, 8])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 1, GOLD_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def section_title(text: str, width: float) -> Table:
    """Titre de section souligné d'un filet or (comme l'en-tête du tableau Weekly Watch)."""
    t = Table([[Paragraph(esc(text).upper(), styles()["section"])]], colWidths=[width])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.4, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# --------------------------------------------------------------------------- #
# Signature de la plateforme (apposée sur chaque fichier généré)
# --------------------------------------------------------------------------- #
PLATFORM = _cfg.PLATFORM
AUTHOR = _cfg.OWNER
COPYRIGHT = _cfg.COPYRIGHT
DISCLAIMER = _cfg.DISCLAIMER
SIGNATURE = COPYRIGHT          # apposée sur chaque page / chaque fichier
CREDIT = COPYRIGHT             # compatibilité avec les anciens appels


def signature_meta() -> dict:
    """Bloc de signature à insérer dans les exports JSON."""
    return {"plateforme": PLATFORM, "copyright": COPYRIGHT, "avertissement": DISCLAIMER,
            "genere_le": datetime.now().strftime("%d/%m/%Y %H:%M")}


def footer_line(context: str, width: float | None = None) -> Table:
    """Pied de page en petits caractères : copyright + avertissement + contexte + date."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    st = styles()
    sig = Paragraph(f'<font name="{FONT_B}" color="{HEX["navy"]}">{esc(COPYRIGHT)}</font>',
                    S("sig", 7, FONT, NAVY, leading=9))
    disc = Paragraph(esc(DISCLAIMER), S("disc", 6.3, FONT_I, GREY, leading=8))
    ctx = Paragraph(f"{esc(context)} · généré le {now}", st["footer"])
    t = Table([[sig], [disc], [ctx]], colWidths=[width or CONTENT_W])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, GOLD_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("TOPPADDING", (0, 1), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# --------------------------------------------------------------------------- #
# Construction PDF / PNG
# --------------------------------------------------------------------------- #
MARGIN = 14 * mm
FRAME_PAD = 6  # padding par défaut des Frame ReportLab
CONTENT_W = A4[0] - 2 * MARGIN - 2 * FRAME_PAD  # largeur utile réelle


def build_pdf(flowables, pagesize=A4, title="CWP", page_numbers=True) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=pagesize, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN, title=title,
                            author=AUTHOR, creator=SIGNATURE, subject=PLATFORM)

    def _page(canvas, d):
        if page_numbers and d.page > 0:  # PDF multipage : signature sur chaque page
            canvas.saveState()
            canvas.setFont(FONT, 6.5)
            canvas.setFillColor(GREY)
            canvas.drawString(MARGIN + FRAME_PAD, 8.5 * mm, SIGNATURE)
            canvas.setFont(FONT_I, 5.6)
            canvas.drawString(MARGIN + FRAME_PAD, 5.5 * mm, DISCLAIMER)
            canvas.setFont(FONT, 6.5)
            canvas.drawRightString(pagesize[0] - MARGIN - FRAME_PAD, 8.5 * mm, f"{d.page}")
            canvas.restoreState()

    doc.build(list(flowables), onFirstPage=_page, onLaterPages=_page)
    return buf.getvalue()


def build_fitted_pdf(make_flowables, width=A4[0], title="CWP") -> bytes:
    """PDF d'une seule page dont la hauteur s'ajuste au contenu (idéal pour une image).
    `make_flowables` est une fonction sans argument qui renvoie une liste neuve de flowables
    (une liste sert à mesurer, l'autre au rendu)."""
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import KeepTogether

    def _flat():  # page unique : KeepTogether inutile, on l'aplatit
        out = []
        for f in make_flowables():
            out.extend(f._content if isinstance(f, KeepTogether) else [f])
        return out

    avail = width - 2 * MARGIN - 2 * FRAME_PAD
    dummy = Canvas(io.BytesIO())
    total = 0.0
    for f in _flat():
        _, h = f.wrapOn(dummy, avail, 100_000)
        total += h + f.getSpaceBefore() + f.getSpaceAfter()
    height = total + 2 * MARGIN + 2 * FRAME_PAD + 4
    return build_pdf(_flat(), pagesize=(width, height), title=title, page_numbers=False)


def pdf_to_png(pdf_bytes: bytes, scale: float = 2.4) -> bytes:
    """Rastérise toutes les pages et les empile verticalement en un PNG."""
    import pypdfium2 as pdfium
    from PIL import Image

    pdf = pdfium.PdfDocument(pdf_bytes)
    pages = []
    for i in range(len(pdf)):
        page = pdf[i]
        pages.append(page.render(scale=scale).to_pil().convert("RGB"))
        page.close()
    pdf.close()
    if len(pages) == 1:
        img = pages[0]
    else:
        w = max(p.width for p in pages)
        img = Image.new("RGB", (w, sum(p.height for p in pages)), "white")
        y = 0
        for p in pages:
            img.paste(p, (0, y))
            y += p.height
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()


def slug(text: str, maxlen: int = 40) -> str:
    import re
    import unicodedata

    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").lower()
    return (t or "cwp")[:maxlen]
