"""Exports PDF de l'espace pédagogique : glossaire filtré, fiche de cas d'étude, fiche méthodologique."""
from __future__ import annotations

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer

from cwp.exports import common as X


def glossary_pdf(df: pd.DataFrame, titre="Glossaire CWP") -> bytes:
    W = X.CONTENT_W
    s = X.styles()
    story = [X.header_card("Espace pédagogique · glossaire", titre,
                           f"{len(df)} termes · finance, conformité, sanctions, fraude, fiscalité, crypto-actifs", W), Spacer(1, 10)]
    for cat, g in df.groupby("categorie", sort=True):
        story += [X.section_title(f"{cat} ({len(g)})", W), Spacer(1, 4)]
        for r in g.itertuples():
            story.append(KeepTogether([Paragraph(X.esc(r.terme), s["card_title"]),
                                       Paragraph(X.esc(r.definition), s["body"]),
                                       Paragraph(X.esc(f"Source : {r.source}"), s["small_grey"]), Spacer(1, 5)]))
        story.append(Spacer(1, 6))
    story += [Paragraph("Les définitions sont des définitions de travail ; se reporter aux textes officiels pour tout usage formel. "
                        "Les termes importés de Wikipédia sont sous licence CC BY-SA 4.0.", s["small_grey"]),
              X.footer_line("Glossaire", W)]
    return X.build_pdf(story, title=titre)


def case_pdf(c: dict, avec_corrige=True) -> bytes:
    from .methodes import by_id
    W = X.CONTENT_W
    s = X.styles()
    lst = lambda items: [Paragraph(f"• {X.esc(t)}", s["body"]) for t in items]
    m = by_id(c["methode"])
    story = [X.header_card(f"Cas d'étude · {c['type']} · {c['theme']}", c["titre"], f"Niveau : {c['niveau']} · trame : {m['titre']}", W),
             Spacer(1, 10), X.section_title("Contexte", W), Spacer(1, 3), Paragraph(X.esc(c["contexte"]), s["body"]), Spacer(1, 8),
             X.section_title("Faits constatés", W), Spacer(1, 3)] + lst(c["faits"]) + [Spacer(1, 8),
             X.section_title("Questions pour l'analyste", W), Spacer(1, 3)] + lst(c["questions"]) + [Spacer(1, 8)]
    if avec_corrige:
        story += [PageBreak(), X.section_title("Corrigé — signaux d'alerte", W), Spacer(1, 3)] + lst(c["signaux"]) + [Spacer(1, 8),
                  X.section_title("Démarche d'analyse", W), Spacer(1, 3)] + \
                 [Paragraph(f"{i}. {X.esc(t)}", s["body"]) for i, t in enumerate(c["demarche"], 1)] + [Spacer(1, 8),
                  X.section_title("Conclusion", W), Spacer(1, 3), Paragraph(X.esc(c["conclusion"]), s["body_b"])]
    note = ("Cas pédagogique fictif : noms et chiffres inventés." if c["type"] == "Cas pédagogique"
            else "Résumé simplifié de faits publics : vérifier les sources officielles avant de citer.")
    story += [Spacer(1, 10), Paragraph(note, s["small_grey"]), X.footer_line("Cas d'étude", W)]
    return X.build_pdf(story, title=f"CWP – Cas {c['titre']}")


def method_pdf(m: dict) -> bytes:
    """Fiche méthodologique seule (sans formulaire) — la trame complète est générée par trames.trame_pdf."""
    from .trames import trame_pdf
    return trame_pdf(m)
