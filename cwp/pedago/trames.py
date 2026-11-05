"""
Générateur de trames d'analyse (PDF à imprimer / remplir + Excel avec listes, scoring et décision).
Une même spécification (cwp_pedago.methodes) produit les deux formats.
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

from cwp.exports import common as X
from .methodes import DECISIONS, METHODES, PUBLICS

SIG = X.SIGNATURE


def parse_field(f: str) -> dict:
    """Décode la syntaxe compacte d'un champ."""
    f = f.strip()
    if " :: " in f:
        lab, opts = f.split(" :: ", 1)
        return dict(label=lab.strip(), kind="choice", options=[o.strip() for o in opts.split(" / ")])
    for tag, kind in (("[long]", "long"), ("[date]", "date"), ("[montant]", "amount")):
        if f.endswith(tag):
            return dict(label=f[: -len(tag)].strip(), kind=kind)
    if f.endswith("?"):
        return dict(label=f, kind="yesno")
    return dict(label=f, kind="text")


def thresholds(m):
    tot = sum(w for _, w in m["indicateurs"])
    return tot, round(tot * 0.25), round(tot * 0.5)


GUIDE_COMMUN = [
    "Renseignez l'en-tête (référence du dossier, analyste, date) avant de commencer.",
    "Remplissez chaque section dans l'ordre : les sections suivent les étapes de la méthodologie.",
    "Cochez ou sélectionnez « Oui / Non / N.A. » pour chaque question fermée ; « N.A. » doit rester exceptionnel et justifié.",
    "Dans la grille de cotation, marquez « Présent » pour chaque indicateur constaté : le total donne le niveau de risque (dans l'Excel, le calcul est automatique).",
    "Passez en revue la liste des signaux d'alerte : chacun coché doit être commenté dans la motivation.",
    "Choisissez une seule décision, motivez-la de façon factuelle (pièces consultées, éléments comparés), puis faites valider par le N+1 ou la conformité.",
    "Conservez la trame complétée et les pièces au moins 5 ans (CMF art. L561-12) ; ne communiquez jamais au client l'existence d'une déclaration de soupçon.",
]


# =========================================================================== #
# PDF
# =========================================================================== #
def _st():
    s = X.styles()
    s["cell"] = X.S("cell", 8.6, X.FONT, X.INK, leading=11)
    s["cellb"] = X.S("cellb", 8.6, X.FONT_B, X.NAVY, leading=11)
    s["hd"] = X.S("hd", 7.6, X.FONT_B, X.INK, leading=9.5)
    return s


def _lst(items, s, numbered=False):
    return [Paragraph(f"{i + 1}. {X.esc(t)}" if numbered else f"• {X.esc(t)}", s["body"]) for i, t in enumerate(items)]


def _box_row(label, kind, W, s, options=None):
    box = X.BOX_EMPTY
    if kind == "yesno":
        val = Paragraph(f"{box} Oui &nbsp;&nbsp; {box} Non &nbsp;&nbsp; {box} N.A.", s["cell"])
    elif kind == "choice":
        val = Paragraph(" &nbsp; ".join(f"{box} {X.esc(o)}" for o in options), s["cell"])
    elif kind == "date":
        val = Paragraph("____ / ____ / ________", s["cell"])
    elif kind == "amount":
        val = Paragraph("&nbsp;" * 60 + " €", s["cell"])
    else:
        val = Paragraph("", s["cell"])
    return [Paragraph(X.esc(label), s["cellb"]), val], (44 if kind == "long" else 19)


def _form_section(title, fields, W, s):
    rows, heights = [], []
    for f in fields:
        p = parse_field(f)
        r, h = _box_row(p["label"], p["kind"], W, s, p.get("options"))
        rows.append(r); heights.append(h if p["kind"] != "choice" or len(" ".join(p["options"])) < 70 else 30)
    t = Table(rows, colWidths=[W * 0.36, W * 0.64], rowHeights=heights)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, X.LINE), ("BACKGROUND", (0, 0), (0, -1), X.CREAM),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("LEFTPADDING", (0, 0), (-1, -1), 5)]))
    return [KeepTogether([X.section_title(title, W), Spacer(1, 4), t]), Spacer(1, 10)]


def _table_section(title, cols, n, W, s):
    data = [[Paragraph(X.esc(c).upper(), s["hd"]) for c in cols]] + [[""] * len(cols) for _ in range(n)]
    t = Table(data, colWidths=[W / len(cols)] * len(cols), rowHeights=[None] + [18] * n, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, X.LINE), ("LINEBELOW", (0, 0), (-1, 0), 1.1, X.GOLD),
                           ("BACKGROUND", (0, 0), (-1, 0), X.CREAM), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [X.section_title(title, W), Spacer(1, 4), t, Spacer(1, 10)]


def trame_pdf(m: dict) -> bytes:
    W = X.CONTENT_W
    s = _st()
    tot, t1, t2 = thresholds(m)
    pub = ", ".join(PUBLICS[p] for p in m["publics"])
    story = [X.header_card(f"Trame d'analyse · {m['famille']}", m["titre"], f"Public : {pub} · CWP – espace pédagogique", W),
             Spacer(1, 8), Paragraph(f"<b>Objectif.</b> {X.esc(m['objectif'])}", s["body"]), Spacer(1, 8)]
    two = Table([[[X.section_title("Quand l'utiliser", W * 0.48), Spacer(1, 3)] + _lst(m["declencheurs"], s),
                  [X.section_title("Livrable attendu", W * 0.48), Spacer(1, 3), Paragraph(X.esc(m["livrable"]), s["body"])]]],
                colWidths=[W * 0.5, W * 0.5])
    two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [two, Spacer(1, 8), X.section_title("Méthodologie pas à pas", W), Spacer(1, 4)]
    steps = Table([[Paragraph(f"<b>{i + 1}</b>", X.S("n", 12, X.FONT_B, X.GOLD)), Paragraph(f"<b>{X.esc(a)}</b> — {X.esc(b)}", s["body"])]
                   for i, (a, b) in enumerate(m["etapes"])], colWidths=[10 * mm, W - 10 * mm])
    steps.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.25, X.LINE),
                               ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [steps, Spacer(1, 8), X.section_title("Comment utiliser cette trame", W), Spacer(1, 4)] + _lst(GUIDE_COMMUN, s, True)
    sm = s["small"]
    two2 = Table([[[X.section_title("Points de contrôle qualité", W * 0.48), Spacer(1, 3)] +
                   [Paragraph(f"• {X.esc(t)}", sm) for t in m["controles"]],
                   [X.section_title("Erreurs fréquentes", W * 0.48), Spacer(1, 3)] +
                   [Paragraph(f"• {X.esc(t)}", sm) for t in m["erreurs"]]]], colWidths=[W * 0.5, W * 0.5])
    two2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [Spacer(1, 6), two2, Spacer(1, 6), X.section_title("Sources à consulter · textes de référence", W), Spacer(1, 3),
              Paragraph(X.esc(" · ".join(m["sources"])), sm), Spacer(1, 2),
              Paragraph(X.esc(" · ".join(m["textes"])), s["small_grey"]), PageBreak()]
    # ----- formulaire
    story += _form_section("En-tête du dossier", ["Référence du dossier", "Analyste", "Date d'analyse [date]", "Entité analysée",
                                                  "Origine :: Alerte outil / Signalement interne / Entrée en relation / Revue périodique / Réquisition / Autre"], W, s)
    for sec in m["trame"]:
        if isinstance(sec, tuple) and sec and sec[0] == "TABLE":
            _, title, cols, n = sec
            story += _table_section(title, cols, n, W, s)
        else:
            title, fields = sec
            story += _form_section(title, fields, W, s)
    # ----- cotation
    data = [[Paragraph(h, s["hd"]) for h in ("INDICATEUR", "POIDS", "PRÉSENT", "POINTS")]]
    data += [[Paragraph(X.esc(t), s["cell"]), Paragraph(str(w), s["cell"]), Paragraph(f"{X.BOX_EMPTY} Oui  {X.BOX_EMPTY} Non", s["cell"]), ""]
             for t, w in m["indicateurs"]]
    data += [[Paragraph("<b>TOTAL</b>", s["cell"]), Paragraph(f"<b>/ {tot}</b>", s["cell"]), "", ""]]
    t = Table(data, colWidths=[W * 0.58, W * 0.1, W * 0.2, W * 0.12], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, X.LINE), ("LINEBELOW", (0, 0), (-1, 0), 1.1, X.GOLD),
                           ("BACKGROUND", (0, 0), (-1, 0), X.CREAM), ("BACKGROUND", (0, -1), (-1, -1), X.CREAM)]))
    story += [KeepTogether([X.section_title("Grille de cotation du risque", W), Spacer(1, 4), t, Spacer(1, 4),
                            Paragraph(f"Lecture : 0 à {t1 - 1} = <b>faible</b> · {t1} à {t2 - 1} = <b>modéré</b> · {t2} et plus = <b>élevé</b> "
                                      "(un seul indicateur de poids 5 justifie à lui seul une escalade).", s["small"])]), Spacer(1, 10)]
    rf = Table([[Paragraph(X.BOX_EMPTY, s["cell"]), Paragraph(X.esc(r), s["cell"])] for r in m["red_flags"]], colWidths=[8 * mm, W - 8 * mm])
    rf.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, X.LINE), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [KeepTogether([X.section_title("Signaux d'alerte constatés", W), Spacer(1, 4), rf]), Spacer(1, 10)]
    dec = Table([[Paragraph(X.BOX_EMPTY, s["cell"]), Paragraph(X.esc(d), s["cell"])] for d in DECISIONS], colWidths=[8 * mm, W - 8 * mm])
    dec.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, X.LINE)]))
    story += [KeepTogether([X.section_title("Décision", W), Spacer(1, 4), dec, Spacer(1, 6)] +
                           _form_section("Motivation et validation", ["Motivation factuelle [long]", "Pièces consultées [long]", "Analyste — signature",
                                                                       "Validation N+1 / conformité — nom et signature", "Date de validation [date]"], W, s)),
              Spacer(1, 6), Paragraph("Document confidentiel — ne pas transmettre au client. " + X.esc(SIG), s["small_grey"]),
              X.footer_line(f"Trame « {m['titre']} »", W)]
    return X.build_pdf(story, title=f"CWP – Trame {m['titre']}")


# =========================================================================== #
# EXCEL
# =========================================================================== #
def trame_xlsx(m: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule, FormulaRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    NAVY, GOLD, CREAM, INPUT = "1F3A5F", "C9A227", "FAF6EA", "FFF8D6"
    thin = Side(style="thin", color="E4E0D5")
    B = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")
    f_title, f_h, f_b = Font(size=16, bold=True, color=GOLD), Font(bold=True, color="FFFFFF"), Font(bold=True, color=NAVY)
    fill_h, fill_c, fill_in = PatternFill("solid", fgColor=NAVY), PatternFill("solid", fgColor=CREAM), PatternFill("solid", fgColor=INPUT)
    tot, t1, t2 = thresholds(m)

    wb = Workbook()
    # ---------- Mode d'emploi
    ws = wb.active; ws.title = "Mode d'emploi"
    ws.column_dimensions["A"].width = 4; ws.column_dimensions["B"].width = 120
    ws["B1"] = m["titre"]; ws["B1"].font = f_title
    ws["B2"] = f"Trame d'analyse · {m['famille']} · public : {', '.join(PUBLICS[p] for p in m['publics'])}"
    ws["B2"].font = Font(italic=True, color="7A7A7A")
    r = 4

    def block(title, lines, numbered=False):
        nonlocal r
        ws.cell(r, 2, title.upper()).font = f_b
        ws.cell(r, 2).fill = fill_c; r += 1
        for i, l in enumerate(lines):
            c = ws.cell(r, 2, f"{i + 1}. {l}" if numbered else f"• {l}"); c.alignment = wrap; r += 1
        r += 1

    block("Objectif", [m["objectif"]])
    block("Quand utiliser cette trame", m["declencheurs"])
    block("Méthodologie pas à pas", [f"{a} — {b}" for a, b in m["etapes"]], True)
    block("Comment remplir ce classeur", [
        "Onglet « Trame » : saisissez dans les cellules jaunes ; les cellules avec liste déroulante n'acceptent que les valeurs proposées.",
        "Onglets de tableaux : un onglet par tableau (flux, acteurs, détention…) ; ajoutez des lignes si nécessaire.",
        "Onglet « Cotation » : choisissez Oui/Non pour chaque indicateur ; le total, le pourcentage et le niveau se calculent automatiquement.",
        f"Seuils : {t1} points = modéré, {t2} points = élevé (total maximal {tot}).",
        "Onglet « Décision » : cochez les signaux constatés, sélectionnez la décision, motivez-la et faites valider.",
    ] + GUIDE_COMMUN[5:], True)
    block("Points de contrôle qualité", m["controles"])
    block("Erreurs fréquentes", m["erreurs"])
    block("Sources à consulter", m["sources"])
    block("Textes de référence", m["textes"])
    ws.cell(r, 2, SIG).font = Font(bold=True, color=NAVY)
    ws.cell(r + 1, 2, f"Modèle généré le {datetime.now():%d/%m/%Y} — document confidentiel une fois complété.").font = Font(color="7A7A7A")

    # ---------- Trame (champs)
    wt = wb.create_sheet("Trame")
    wt.column_dimensions["A"].width = 46; wt.column_dimensions["B"].width = 70; wt.column_dimensions["C"].width = 40
    wt["A1"] = m["titre"]; wt["A1"].font = f_title
    wt["A2"] = "Cellules jaunes = à remplir"; wt["A2"].font = Font(italic=True, color="7A7A7A")
    for col, h in zip("ABC", ("Champ", "Saisie", "Commentaire")):
        wt[f"{col}4"] = h; wt[f"{col}4"].font = f_h; wt[f"{col}4"].fill = fill_h
    wt.freeze_panes = "A5"
    dv_yn = DataValidation(type="list", formula1='"Oui,Non,N.A."', allow_blank=True); wt.add_data_validation(dv_yn)
    row = 5
    sections = [("En-tête du dossier", ["Référence du dossier", "Analyste", "Date d'analyse [date]", "Entité analysée",
                                        "Origine :: Alerte outil / Signalement interne / Entrée en relation / Revue périodique / Réquisition / Autre"])]
    tables = []
    for sec in m["trame"]:
        if isinstance(sec, tuple) and sec and sec[0] == "TABLE":
            tables.append(sec)
        else:
            sections.append(sec)
    for title, fields in sections:
        wt.cell(row, 1, title.upper()).font = f_b
        for c in range(1, 4):
            wt.cell(row, c).fill = fill_c
        row += 1
        for f in fields:
            p = parse_field(f)
            a = wt.cell(row, 1, p["label"]); a.alignment = wrap; a.border = B
            b = wt.cell(row, 2); b.fill = fill_in; b.border = B; b.alignment = wrap
            wt.cell(row, 3).border = B
            if p["kind"] == "yesno":
                dv_yn.add(b)
            elif p["kind"] == "choice":
                opts = ",".join(o.replace(",", " ") for o in p["options"])
                if len(opts) < 250:
                    dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True); wt.add_data_validation(dv); dv.add(b)
                else:
                    wt.cell(row, 3, "Choix : " + " / ".join(p["options"]))
            elif p["kind"] == "date":
                b.number_format = "DD/MM/YYYY"
                dv = DataValidation(type="date", operator="greaterThan", formula1="DATE(1900,1,1)", allow_blank=True); wt.add_data_validation(dv); dv.add(b)
            elif p["kind"] == "amount":
                b.number_format = '#,##0.00 "€"'
            elif p["kind"] == "long":
                wt.row_dimensions[row].height = 60
            row += 1
        row += 1

    # ---------- Tableaux
    for _, title, cols, n in tables:
        name = title[:28].replace("/", "-").replace(":", "")
        name = name if name not in wb.sheetnames else name[:25] + "_2"
        w = wb.create_sheet(name)
        w["A1"] = title; w["A1"].font = f_title
        for j, c in enumerate(cols, 1):
            cell = w.cell(3, j, c); cell.font = f_h; cell.fill = fill_h; cell.alignment = wrap
            w.column_dimensions[cell.column_letter].width = max(14, min(40, len(c) + 8))
        for i in range(4, 4 + max(n, 10) + 10):
            for j in range(1, len(cols) + 1):
                cell = w.cell(i, j); cell.border = B; cell.fill = fill_in
                if any(k in cols[j - 1].lower() for k in ("montant", "prix", "valeur")):
                    cell.number_format = '#,##0.00'
                if "date" in cols[j - 1].lower():
                    cell.number_format = "DD/MM/YYYY"
        w.freeze_panes = "A4"

    # ---------- Cotation
    wc = wb.create_sheet("Cotation")
    for col, wd in zip("ABCD", (70, 10, 14, 12)):
        wc.column_dimensions[col].width = wd
    wc["A1"] = "Grille de cotation du risque"; wc["A1"].font = f_title
    for col, h in zip("ABCD", ("Indicateur", "Poids", "Présent ?", "Points")):
        wc[f"{col}3"] = h; wc[f"{col}3"].font = f_h; wc[f"{col}3"].fill = fill_h
    dv2 = DataValidation(type="list", formula1='"Oui,Non"', allow_blank=True); wc.add_data_validation(dv2)
    first = 4
    for i, (t, w_) in enumerate(m["indicateurs"]):
        rr = first + i
        wc.cell(rr, 1, t).alignment = wrap; wc.cell(rr, 2, w_)
        c = wc.cell(rr, 3, "Non"); c.fill = fill_in; dv2.add(c)
        wc.cell(rr, 4, f'=IF(C{rr}="Oui",B{rr},0)')
        for j in range(1, 5):
            wc.cell(rr, j).border = B
    last = first + len(m["indicateurs"]) - 1
    tr = last + 2
    wc.cell(tr, 1, "TOTAL").font = f_b; wc.cell(tr, 2, f"=SUM(B{first}:B{last})"); wc.cell(tr, 4, f"=SUM(D{first}:D{last})").font = Font(bold=True, size=13)
    wc.cell(tr + 1, 1, "Score (% du maximum)").font = f_b; wc.cell(tr + 1, 4, f"=IF(B{tr}=0,0,D{tr}/B{tr})").number_format = "0%"
    wc.cell(tr + 2, 1, "Indicateur de poids 5 présent ?").font = f_b
    wc.cell(tr + 2, 4, f'=IF(COUNTIFS(B{first}:B{last},5,C{first}:C{last},"Oui")>0,"Oui","Non")')
    wc.cell(tr + 3, 1, "NIVEAU DE RISQUE").font = Font(bold=True, size=13, color=NAVY)
    lv = wc.cell(tr + 3, 4, f'=IF(OR(D{tr}>={t2},D{tr + 2}="Oui"),"Élevé",IF(D{tr}>={t1},"Modéré","Faible"))')
    lv.font = Font(bold=True, size=13)
    for txt, col in (("Élevé", "F4C7C3"), ("Modéré", "FCE8B2"), ("Faible", "CDEFD8")):
        wc.conditional_formatting.add(f"D{tr + 3}", CellIsRule(operator="equal", formula=[f'"{txt}"'], fill=PatternFill("solid", fgColor=col)))
    wc.conditional_formatting.add(f"A{first}:D{last}", FormulaRule(formula=[f'$C{first}="Oui"'], fill=PatternFill("solid", fgColor="FBE3E1")))
    wc.cell(tr + 5, 1, f"Seuils : modéré à partir de {t1} points, élevé à partir de {t2} points ou dès qu'un indicateur de poids 5 est présent.").font = Font(italic=True, color="7A7A7A")

    # ---------- Décision
    wd = wb.create_sheet("Décision")
    wd.column_dimensions["A"].width = 80; wd.column_dimensions["B"].width = 18; wd.column_dimensions["C"].width = 50
    wd["A1"] = "Signaux d'alerte et décision"; wd["A1"].font = f_title
    for col, h in zip("ABC", ("Signal d'alerte", "Constaté ?", "Commentaire")):
        wd[f"{col}3"] = h; wd[f"{col}3"].font = f_h; wd[f"{col}3"].fill = fill_h
    dv3 = DataValidation(type="list", formula1='"Oui,Non"', allow_blank=True); wd.add_data_validation(dv3)
    rr = 4
    for t in m["red_flags"]:
        wd.cell(rr, 1, t).alignment = wrap
        c = wd.cell(rr, 2); c.fill = fill_in; dv3.add(c)
        wd.cell(rr, 3).fill = fill_in
        for j in range(1, 4):
            wd.cell(rr, j).border = B
        rr += 1
    rr += 1
    wd.cell(rr, 1, "Niveau de risque (calculé)").font = f_b; wd.cell(rr, 2, f"=Cotation!D{tr + 3}").font = Font(bold=True); rr += 1
    wd.cell(rr, 1, "Décision").font = f_b
    dvd = DataValidation(type="list", formula1='"' + ",".join(DECISIONS) + '"', allow_blank=True); wd.add_data_validation(dvd)
    c = wd.cell(rr, 2); c.fill = fill_in; dvd.add(c); wd.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=3); rr += 1
    for lab, h in (("Motivation factuelle", 90), ("Pièces consultées", 50), ("Analyste", 18), ("Date", 18),
                   ("Validation N+1 / conformité", 18), ("Date de validation", 18)):
        wd.cell(rr, 1, lab).font = f_b
        c = wd.cell(rr, 2); c.fill = fill_in; c.alignment = wrap
        wd.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=3); wd.row_dimensions[rr].height = h
        if "Date" in lab:
            c.number_format = "DD/MM/YYYY"
        rr += 1
    wd.cell(rr + 1, 1, "Document confidentiel — ne pas transmettre au client. " + SIG).font = Font(italic=True, color="7A7A7A")

    for sh in wb.worksheets:
        sh.page_setup.orientation = "landscape"; sh.page_setup.fitToWidth = 1; sh.sheet_properties.pageSetUpPr.fitToPage = True
        sh.oddFooter.center.text = SIG
    wb.properties.creator = f"{X.AUTHOR} — CWP"
    wb.properties.title = m["titre"]
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def pack_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for m in METHODES:
            base = f"{m['famille']}_{m['id']}".replace(" ", "_").replace("/", "-")
            z.writestr(f"CWP_trames/{base}.pdf", trame_pdf(m))
            z.writestr(f"CWP_trames/{base}.xlsx", trame_xlsx(m))
        z.writestr("CWP_trames/LISEZMOI.txt",
                   "Trames d'analyse CWP : chaque trame existe en PDF (à imprimer ou annoter) et en Excel (listes déroulantes, "
                   "cotation automatique, décision). Le mode d'emploi figure en première page du PDF et dans l'onglet « Mode d'emploi ».\n"
                   + SIG + "\n")
    return buf.getvalue()
