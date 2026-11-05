"""
cwp.exports.weekly_watch — exports du tableau « Weekly Watch » (PNG, PDF, Excel).

Chaque fichier porte en pied de page, en petits caractères, le copyright et l'avertissement
de non-responsabilité définis dans cwp.config.
"""
from __future__ import annotations

import io
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from cwp.config import COPYRIGHT, DISCLAIMER, FONTS_DIR
from cwp.core.classify import EXPORT_COLOR

EXPORT_COLS = [("Entité / cible", .13), ("Catégorie", .11), ("Description", .27), ("Pays", .13),
               ("Mesure", .10), ("Montant", .08), ("Date", .08), ("Autorité", .10)]
GOLD = "#C9A227"
FOOTER = "Informations issues de la presse, détectées automatiquement : à vérifier auprès des sources officielles (OFAC, UE, ONU, DG Trésor…)"
FLAG_URL = "https://flagcdn.com/w40/{}.png"
FONT_URLS = {False: "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf",
             True: "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf"}


def fmt_date(ts):
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else "—"


@st.cache_data(ttl=86400, show_spinner=False)
def flag_bytes(cc):
    """Drapeau téléchargé pour les exports (None si indisponible)."""
    if len(cc) != 2 or not cc.isalpha():
        return None
    try:
        r = requests.get(FLAG_URL.format(cc.lower()), timeout=5)
        return r.content if r.ok and r.content[:4] == b"\x89PNG" else None
    except Exception:
        return None


def _plain(s):
    return re.sub(r"[\U00010000-\U0010FFFF]", "", str(s or "")).strip()


def _ascii(s):
    s = (s.replace("—", "-").replace("–", "-").replace("’", "'").replace("‘", "'").replace("«", '"')
          .replace("»", '"').replace("…", "...").replace("€", "EUR").replace("·", "-").replace(" ", " ")
          .replace("©", "(c)"))
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def cells(r):
    return [r["entity"], r["theme"], r["headline"],
            r["country"] if r["cc"] else "—",
            r["measure"], r["amount"], fmt_date(r["ts"]),
            (" · ".join(x for x in [r["auth"], r["source"]] if x) or "—")
            + (f' (+{r["n_media"] - 1} médias)' if r.get("n_media", 1) > 1 else "")]


# --------------------------------------------------------------------------- #
# PNG
# --------------------------------------------------------------------------- #
def _font_path(bold):
    """Police avec accents : embarquée (assets/fonts) > reportlab (Vera) > système > téléchargement."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    cands = [os.path.join(FONTS_DIR, name)]
    try:
        import reportlab
        cands.append(os.path.join(os.path.dirname(reportlab.__file__), "fonts", "VeraBd.ttf" if bold else "Vera.ttf"))
    except Exception:
        pass
    cands += [f"/usr/share/fonts/truetype/dejavu/{name}"]
    for c in cands:
        if os.path.exists(c):
            return c
    local = os.path.join("/tmp", name)
    if not os.path.exists(local):
        try:
            r = requests.get(FONT_URLS[bold], timeout=10)
            if r.ok and len(r.content) > 100_000:
                open(local, "wb").write(r.content)
        except Exception:
            pass
    return local if os.path.exists(local) else None


def _font(size, bold=False):
    from PIL import ImageFont
    path = _font_path(bold)
    if path:
        try:
            f = ImageFont.truetype(path, size)
            f.has_accents = True
            return f
        except Exception:
            pass
    try:
        f = ImageFont.load_default(size=size)
    except Exception:
        f = ImageFont.load_default()
    f.has_accents = False
    return f


def _wrap(d, text, font, width, max_lines):
    lines, cur, words = [], "", []
    for w in text.split():  # mot plus large que la colonne : coupé en morceaux
        while d.textlength(w, font=font) > width and len(w) > 1:
            k = len(w)
            while k > 1 and d.textlength(w[:k], font=font) > width:
                k -= 1
            words.append(w[:k])
            w = w[k:]
        words.append(w)
    for w in words:
        t = f"{cur} {w}".strip()
        if not cur or d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and d.textlength(last + "…", font=font) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines or [""]


def make_png(rows, label, period_txt) -> bytes:
    from PIL import Image, ImageDraw
    W, M, pad, lh = 1800, 48, 12, 26
    FLAG_W = 40
    T = _plain if _font(18).has_accents else (lambda x: _ascii(_plain(x)))
    tw = W - 2 * M
    f_title, f_sub, f_head = _font(44, True), _font(22), _font(17, True)
    f_cell, f_bold, f_foot = _font(18), _font(18, True), _font(13)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    xs, x = [], M
    for _, fr in EXPORT_COLS:
        xs.append((x, int(tw * fr)))
        x += int(tw * fr)
    prepared = []
    for r in rows:
        wrapped = [_wrap(tmp, T(c), f_bold if j in (0, 4, 5) else f_cell,
                         w - 2 * pad - (FLAG_W if j == 3 and r["cc"] else 0), 4 if j == 2 else 3)
                   for j, (c, (_, w)) in enumerate(zip(cells(r), xs))]
        prepared.append((r, wrapped, max(len(l) for l in wrapped) * lh + 2 * pad))
    top, head_h = M + 150, 50
    H = top + head_h + sum(p[2] for p in prepared) + 140
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([M, M, W - M, M + 110], radius=18, fill="#fbf7ea", outline="#e8dcb0", width=2)
    d.text((M + 30, M + 16), T("Weekly Watch — Sécurité financière"), font=f_title, fill=GOLD)
    d.text((M + 32, M + 72), T(f"{label} · {period_txt}"), font=f_sub, fill="#6b6b6b")
    y = top
    for (name, _), (x0, _) in zip(EXPORT_COLS, xs):
        d.text((x0 + pad, y + 15), T(name.upper()), font=f_head, fill="#2b2b2b")
    d.line([M, y + head_h - 2, W - M, y + head_h - 2], fill=GOLD, width=3)
    y += head_h
    for i, (r, wrapped, h) in enumerate(prepared):
        if i % 2:
            d.rectangle([M, y, W - M, y + h], fill="#faf8f2")
        for j, (lines, (x0, _)) in enumerate(zip(wrapped, xs)):
            font, color = f_cell, "#1f2937"
            if j == 0:
                font, color = f_bold, "#0f3d66"
            if j == 4:
                font, color = f_bold, EXPORT_COLOR.get(r["mkey"], "#6b7c8c")
            if j == 5:
                font, color = (f_bold, "#1f2937") if r["amount_v"] else (f_cell, "#9a9a9a")
            if j == 3 and r["cc"]:
                fb = flag_bytes(r["cc"])
                if fb:
                    try:
                        fl = Image.open(io.BytesIO(fb)).convert("RGB").resize((30, 20))
                        img.paste(fl, (x0 + pad, y + pad + 4))
                    except Exception:
                        pass
            for k, line in enumerate(lines):
                d.text((x0 + pad + (FLAG_W if j == 3 and r["cc"] else 0), y + pad + k * lh), line, font=font, fill=color)
        y += h
        d.line([M, y, W - M, y], fill="#e6e2d6", width=1)
    d.text((M, y + 26), T(f"{FOOTER} · généré le {datetime.now():%d/%m/%Y %H:%M}"), font=f_foot, fill="#8a8a8a")
    d.text((M, y + 50), T(COPYRIGHT), font=_font(13, True), fill="#8a8a8a")
    d.text((M, y + 72), T(DISCLAIMER), font=f_foot, fill="#9a9a9a")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def make_pdf(rows, label, period_txt) -> bytes:
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def txt(s):  # polices PDF standard : jeu de caractères cp1252
        return escape(_plain(s).encode("cp1252", "ignore").decode("cp1252"))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=16 * mm, title="Weekly Watch – Sécurité financière",
                            author=COPYRIGHT)
    gold = colors.HexColor(GOLD)
    s_t = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=20, textColor=gold, leading=24)
    s_s = ParagraphStyle("s", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#6b6b6b"), leading=11)
    s_h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=7.5, textColor=colors.HexColor("#2b2b2b"), leading=10)
    s_c = ParagraphStyle("c", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#1f2937"))
    s_b = ParagraphStyle("b", parent=s_c, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f3d66"))

    def pays_cell(r, label_):
        fb = flag_bytes(r["cc"]) if r["cc"] else None
        if not fb:
            return Paragraph(label_, s_c)
        t = Table([[RLImage(io.BytesIO(fb), width=6 * mm, height=4 * mm), Paragraph(label_, s_c)]],
                  colWidths=[7.5 * mm, None])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    data = [[Paragraph(txt(n.upper()), s_h) for n, _ in EXPORT_COLS]]
    for r in rows:
        c = cells(r)
        link = escape(r["link"], {'"': "&quot;"})
        data.append([
            Paragraph(txt(c[0]), s_b), Paragraph(txt(c[1]), s_c),
            Paragraph(f'<link href="{link}" color="#1a4e8a">{txt(c[2])}</link>', s_c),
            pays_cell(r, txt(c[3])),
            Paragraph(f'<font color="{EXPORT_COLOR.get(r["mkey"], "#6b7c8c")}"><b>{txt(c[4])}</b></font>', s_c),
            Paragraph(f"<b>{txt(c[5])}</b>" if r["amount_v"] else txt(c[5]), s_c),
            Paragraph(txt(c[6]), s_c), Paragraph(txt(c[7]), s_c)])
    table = Table(data, colWidths=[doc.width * fr for _, fr in EXPORT_COLS], repeatRows=1)
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, gold),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#e6e2d6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf8f2")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story = [Paragraph(txt("Weekly Watch — Sécurité financière"), s_t),
             Paragraph(txt(f"{label} · {period_txt} · {len(rows)} éléments"), s_s), Spacer(1, 5 * mm), table,
             Spacer(1, 4 * mm), Paragraph(txt(f"{FOOTER} · généré le {datetime.now():%d/%m/%Y %H:%M}"), s_s)]

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#8a8a8a"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(12 * mm, 9 * mm, COPYRIGHT.encode("cp1252", "ignore").decode("cp1252"))
        canvas.setFont("Helvetica-Oblique", 6.2)
        canvas.drawString(12 * mm, 5.5 * mm, DISCLAIMER.encode("cp1252", "ignore").decode("cp1252"))
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(landscape(A4)[0] - 12 * mm, 9 * mm, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Excel
# --------------------------------------------------------------------------- #
def _with_legal_sheet(buf_writer):
    pd.DataFrame({"Compliance Watch Platform": [COPYRIGHT, DISCLAIMER,
                                                f"Généré le {datetime.now():%d/%m/%Y %H:%M}"]}).to_excel(
        buf_writer, sheet_name="Mentions", index=False)


def to_excel_watch(rows) -> bytes:
    df = pd.DataFrame([{n: v for (n, _), v in zip(EXPORT_COLS, cells(r))} | {"Lien": r["link"]} for r in rows])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name="Weekly Watch")
        _with_legal_sheet(xw)
    return buf.getvalue()


def to_excel_news(rows) -> bytes:
    df = pd.DataFrame(rows)
    df["date"] = df["ts"].apply(lambda t: datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "")
    if "lang" not in df:
        df["lang"] = ""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df[["date", "theme", "lang", "title", "desc", "source", "link"]].rename(columns={"lang": "langue"}).to_excel(
            xw, index=False, sheet_name="Veille")
        _with_legal_sheet(xw)
    return buf.getvalue()
