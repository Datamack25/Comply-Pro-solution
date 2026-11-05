"""
cwp.data.reports — rapports téléchargeables (PDF, HTML interactif, Excel).

Tous les fichiers portent la mention « CWP – Compliance Watch Platform, une plateforme créée
par la mention © Mackenson Cineus ». Les sources sont citées par leur nom, sans lien.
"""
from __future__ import annotations

import html
import io
from datetime import datetime

import pandas as pd
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

from cwp.exports import common as X

SIG = X.SIGNATURE
RISK_HEX = {"Faible": "#2E8B57", "Modéré": "#D68910", "Élevé": "#C0392B"}


def _p(txt, style="small"):
    return Paragraph(X.esc(txt), X.styles()[style])


def _table(df: pd.DataFrame, cols: list[tuple], width: float, max_rows=40, font_size=7.8):
    """cols : [(colonne, libellé, fraction de largeur)]"""
    st = X.S("tc", font_size, X.FONT, X.INK, leading=font_size * 1.3)
    sh = X.S("th", font_size - 0.6, X.FONT_B, X.INK, leading=font_size * 1.25)
    data = [[Paragraph(X.esc(l).upper(), sh) for _, l, _ in cols]]
    for _, r in df.head(max_rows).iterrows():
        data.append([Paragraph(X.esc(str(r.get(c, "")))[:400], st) for c, _, _ in cols])
    if len(data) == 1:
        data.append([Paragraph("Aucun élément.", st)] + [""] * (len(cols) - 1))
    t = Table(data, colWidths=[width * f for _, _, f in cols], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.1, X.GOLD), ("LINEBELOW", (0, 1), (-1, -1), 0.25, X.LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, X.ROW_ALT]), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    extra = [Spacer(1, 2), _p(f"… {len(df) - max_rows} ligne(s) supplémentaire(s) dans l'export Excel.", "small_grey")] \
        if len(df) > max_rows else []
    return [t] + extra


def _kv(pairs, width):
    s = X.styles()
    data = [[Paragraph(X.esc(k).upper(), s["label"]), Paragraph(X.esc(str(v)), s["value"])] for k, v in pairs]
    t = Table(data, colWidths=[width * 0.32, width * 0.68])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, X.LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _bars(items: list[tuple], width, color="#1F3A5F", max_v=None, h_row=15):
    """Barres horizontales (facteurs de risque, comptages) dessinées en vectoriel."""
    if not items:
        return Spacer(1, 1)
    lab_w = width * 0.52
    max_v = max_v or max(v for _, v in items) or 1
    d = Drawing(width, h_row * len(items) + 4)
    for i, (lab, v) in enumerate(reversed(items)):
        y = 2 + i * h_row
        d.add(String(0, y + 4, str(lab)[:70], fontName=X.FONT, fontSize=7.4, fillColor=X.INK))
        bw = (width - lab_w - 40) * v / max_v
        d.add(Rect(lab_w, y + 2, (width - lab_w - 40), 9, fillColor=colors.HexColor("#F1EEE4"), strokeColor=None))
        d.add(Rect(lab_w, y + 2, max(bw, 1), 9, fillColor=colors.HexColor(color), strokeColor=None, rx=2, ry=2))
        d.add(String(lab_w + bw + 4, y + 4, f"{v:g}", fontName=X.FONT_B, fontSize=7.4, fillColor=X.INK))
    return d


def _score_card(score, niveau, vigilance, width):
    col = colors.HexColor(RISK_HEX.get(niveau, "#7A7A7A"))
    s = X.styles()
    big = X.S("big", 30, X.FONT_B, col, leading=32)
    cell1 = [Paragraph(f"{score:.0f}<font size=11 color='#7A7A7A'> / 100</font>", big)]
    cell2 = [Paragraph(X.esc(f"RISQUE {niveau.upper()}"), X.S("lv", 12, X.FONT_B, col, leading=15)),
             Paragraph(X.esc(vigilance), s["body"])]
    t = Table([[cell1, cell2]], colWidths=[width * 0.3, width * 0.7])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, X.GOLD_LIGHT), ("BACKGROUND", (0, 0), (-1, -1), X.CREAM),
                           ("LINEBEFORE", (0, 0), (0, -1), 4, col), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return t


DISCLAIMER = ("Résultat indicatif produit automatiquement à partir de sources publiques ouvertes. Une correspondance "
              "de nom n'est pas une identification : confirmer l'identité (date de naissance, nationalité, numéro "
              "d'immatriculation) sur la source officielle avant toute décision de gel, de refus ou de déclaration.")


# --------------------------------------------------------------------------- #
# Rapport d'entité
# --------------------------------------------------------------------------- #
def sources_profil(p) -> list[str]:
    s = ["OFAC – Trésor américain", "Commission européenne (FSF)", "Conseil de sécurité des Nations unies",
         "FCDO – Royaume-Uni", "DG Trésor"]
    if p.get("ppe") or not p.get("ppe_df", pd.DataFrame()).empty: s.append("Wikidata")
    if p.get("nb_presse_negative"): s.append("GDELT Project")
    if p.get("lei") or not p.get("lei_df", pd.DataFrame()).empty: s.append("GLEIF")
    if p.get("siren"): s.append("INSEE / INPI (API Recherche d'entreprises)")
    if p.get("geo"): s.append("OpenStreetMap")
    if p.get("fiche"): s.append("Wikidata / Wikipédia")
    if p.get("fin_sec") is not None and not p["fin_sec"].empty: s.append("SEC EDGAR")
    if p.get("plateforme", {}).get("actualites") is not None and len(p["plateforme"]["actualites"]): s.append("Archives de veille CWP")
    if p.get("score_pays"): s += ["Banque mondiale (WGI)", "GAFI"]
    return s


def entity_pdf(p: dict) -> bytes:
    W = X.CONTENT_W
    st = X.styles()
    story = [X.header_card("Profil d'entité · filtrage LCB-FT", p["nom"],
                           f"{p['type']} · {p.get('pays_nom') or 'pays non renseigné'} · analyse du {p['date']}", W),
             Spacer(1, 8), _score_card(p["score"], p["niveau"], p["vigilance"], W), Spacer(1, 10)]
    sy = p.get("synthese")
    if sy:
        story += [X.section_title("Synthèse de l'analyste", W), Spacer(1, 4)] + [Paragraph(X.esc(t), st["body"]) for t in sy["texte"]]
        story += [Spacer(1, 6), X.section_title("Prochaines étapes", W), Spacer(1, 3)] + \
                 [Paragraph(f"{i}. {X.esc(t)}", st["body"]) for i, t in enumerate(sy["etapes"], 1)] + [Spacer(1, 8)]
    if p.get("trames_recommandees"):
        from cwp.pedago.methodes import by_id
        story += [X.section_title("Trames d'analyse recommandées (espace pédagogique CWP)", W), Spacer(1, 3)] + \
                 [Paragraph(f"• <b>{X.esc(by_id(m)['titre'])}</b> — {X.esc(w)}", st["body"]) for m, w in p["trames_recommandees"]] + [Spacer(1, 8)]
    story += [X.section_title("Facteurs du score", W), Spacer(1, 4),
              _bars([(a, b) for a, b in p["contributions"]], W, "#C0392B", max_v=60) if p["contributions"]
              else _p("Aucun facteur de risque détecté."), Spacer(1, 10)]
    ident = [("Nom analysé", p["nom"]), ("Type", p["type"]), ("Pays", p.get("pays_nom") or "—"),
             ("Année de naissance", p.get("annee") or "—"), ("LEI", p.get("lei") or "—"),
             ("Statut LEI", p.get("lei_statut") or "—"), ("Société mère directe", p.get("lei_parent") or "—"),
             ("Société mère ultime", p.get("lei_parent_ultime") or "—"), ("SIREN", p.get("siren") or "—"),
             ("Dirigeants", p.get("dirigeants") or "—"),
             ("Adresse", p.get("adresse") or (p.get("geo") or {}).get("label", "") or "—")]
    f = p.get("fiche") or {}
    for k, lab in (("description_courte", "Description (Wikidata)"), ("secteur", "Secteur"), ("creation", "Création"),
                   ("naissance", "Naissance"), ("siege", "Siège"), ("dirigeant", "Dirigeant (Wikidata)"),
                   ("societe_mere", "Société mère (Wikidata)"), ("fonctions", "Fonctions (Wikidata)"), ("bourse", "Cotation")):
        if f.get(k):
            ident.append((lab, str(f[k])[:300]))
    story += [KeepTogether([X.section_title("Identification", W), Spacer(1, 4), _kv(ident, W)]), Spacer(1, 10)]
    fin = p.get("fin_sec")
    if fin is not None and not fin.empty:
        cols = [c for c in fin.columns if c not in ("societe", "ticker", "cik")]
        story += [X.section_title("Données financières SEC EDGAR (USD)", W), Spacer(1, 4)] + _table(
            fin.assign(**{c: fin[c].map(lambda v: f"{float(v):,.0f}".replace(",", " ") if str(v) not in ("", "nan") else "")
                         for c in cols[1:]}), [(c, str(c), 1 / len(cols)) for c in cols], W) + [Spacer(1, 10)]
    hits = p["hits"]
    sanc = hits[hits.liste != "PPE (Wikidata)"] if not hits.empty else hits
    story += [X.section_title(f"Correspondances sur les listes de sanctions ({len(sanc)})", W), Spacer(1, 4)]
    story += _table(sanc, [("liste", "Liste", .15), ("nom", "Nom inscrit", .22), ("variante", "Variante", .17),
                           ("programme", "Programme", .2), ("pays", "Pays", .08), ("score", "Score", .07),
                           ("niveau", "Niveau", .11)], W)
    ppe = p.get("ppe_df", pd.DataFrame())
    if not ppe.empty:
        ppe = ppe.rename(columns={"programme": "fonction"}) if "fonction" not in ppe else ppe
        story += [Spacer(1, 10), X.section_title(f"Fonctions politiques exposées ({len(ppe)})", W), Spacer(1, 4)]
        story += _table(ppe, [("nom", "Personne", .25), ("fonction", "Fonction", .4), ("debut", "Début", .12),
                              ("fin", "Fin", .12), ("en_fonction", "En fonction", .11)], W)
    pr = p.get("presse", pd.DataFrame())
    story += [Spacer(1, 10), X.section_title(f"Presse négative ({len(pr)})", W), Spacer(1, 4)]
    if not pr.empty:
        cnt = pr.categorie.value_counts()
        story += [_bars(list(cnt.items()), W * 0.7, "#D68910"), Spacer(1, 6)]
    story += _table(pr.sort_values("date", ascending=False) if not pr.empty else pr,
                    [("date", "Date", .11), ("media", "Média", .19), ("categorie", "Catégorie", .13),
                     ("titre", "Titre", .57)], W, max_rows=25)
    if p.get("score_pays"):
        story += [Spacer(1, 10), KeepTogether([X.section_title("Risque pays", W), Spacer(1, 4), _kv(
            [("Pays", p.get("pays_nom")), ("Score pays", f"{float(p['score_pays']):.0f}/100 ({p.get('pays_niveau', '')})"),
             ("Statut GAFI", p.get("pays_gafi") or "—")], W)])]
    story += [Spacer(1, 10), X.section_title("Sources consultées", W), Spacer(1, 4),
              _p(" · ".join(sources_profil(p))), Spacer(1, 8), _p(DISCLAIMER, "small_grey"), Spacer(1, 10),
              X.footer_line("Profil d'entité", W)]
    return X.build_pdf(story, title=f"CWP – Profil {p['nom']}")


# --------------------------------------------------------------------------- #
# Rapport risque pays
# --------------------------------------------------------------------------- #
def country_pdf(df: pd.DataFrame, focus: list[str] | None = None, titre="Cartographie des risques pays") -> bytes:
    size = landscape(A4)
    W = size[0] - 2 * X.MARGIN - 2 * X.FRAME_PAD
    d = df.copy()
    d["score_risque"] = pd.to_numeric(d.score_risque, errors="coerce")
    d = d.sort_values("score_risque", ascending=False)
    n_el, n_mo = (d.niveau == "Élevé").sum(), (d.niveau == "Modéré").sum()
    story = [X.header_card("Risque pays · LCB-FT & sanctions", titre,
                           f"{len(d)} pays · {n_el} à risque élevé · {n_mo} modéré · méthode : gouvernance (WGI), "
                           "listes GAFI, régimes de sanctions, entités inscrites", W), Spacer(1, 10)]
    if focus:
        f = d[d.iso2.isin(focus)]
        story += [X.section_title("Pays suivis", W), Spacer(1, 4)]
        story += _table(f, [("nom", "Pays", .16), ("score_risque", "Score", .07), ("niveau", "Niveau", .08),
                            ("gafi", "GAFI", .1), ("regime_sanctions", "Régime sanctions", .1),
                            ("nb_entites_sanctionnees", "Entités inscrites", .1), ("wgi_corruption", "WGI corruption", .1),
                            ("wgi_etat_droit", "WGI État de droit", .1), ("segment", "Segment ML", .19)], W)
        story.append(Spacer(1, 10))
    story += [X.section_title("Top 20 des pays les plus risqués", W), Spacer(1, 4),
              _bars([(r.nom, r.score_risque) for r in d.head(20).itertuples()], W * 0.8, "#C0392B", max_v=100, h_row=12.5),
              Spacer(1, 10), X.section_title("Tableau complet", W), Spacer(1, 4)]
    story += _table(d, [("nom", "Pays", .17), ("region", "Région", .13), ("score_risque", "Score", .07),
                        ("niveau", "Niveau", .08), ("gafi", "GAFI", .1), ("regime_sanctions", "Régime", .07),
                        ("nb_entites_sanctionnees", "Entités inscrites", .09), ("score_gouvernance", "Gouvernance", .09),
                        ("annee_wgi", "Année WGI", .08), ("gafi_maj", "Liste GAFI au", .12)], W, max_rows=260, font_size=7)
    story += [Spacer(1, 8), _p("Sources : Banque mondiale (Worldwide Governance Indicators) · GAFI · OFAC · Union européenne "
                               "· Nations unies · FCDO · DG Trésor. Listes GAFI à confirmer après chaque plénière.", "small_grey"),
              Spacer(1, 8), X.footer_line("Risque pays", W)]
    return X.build_pdf(story, pagesize=size, title="CWP – Risque pays")


# --------------------------------------------------------------------------- #
# Rapport de veille (nouvelles inscriptions + actualités)
# --------------------------------------------------------------------------- #
def veille_pdf(new_entries: pd.DataFrame, removed: pd.DataFrame, news: pd.DataFrame, depuis: str) -> bytes:
    size = landscape(A4)
    W = size[0] - 2 * X.MARGIN - 2 * X.FRAME_PAD
    story = [X.header_card("Rapport de veille sanctions", "Nouvelles inscriptions & radiations",
                           f"Depuis le {depuis} · {len(new_entries)} inscription(s) · {len(removed)} radiation(s) · "
                           f"{len(news)} actualité(s)", W), Spacer(1, 10)]
    if not new_entries.empty:
        story += [X.section_title("Répartition par liste", W), Spacer(1, 4),
                  _bars(list(new_entries.liste.value_counts().items()), W * 0.6, "#1F3A5F"), Spacer(1, 10)]
    cols = [("liste", "Liste", .12), ("nom", "Nom", .22), ("type", "Type", .07), ("programme", "Programme", .22),
            ("pays", "Pays", .08), ("date_inscription", "Inscrit le", .09), ("premiere_vue", "Détecté par CWP", .2)]
    story += [X.section_title("Nouvelles inscriptions détectées", W), Spacer(1, 4)] + _table(new_entries, cols, W, 120)
    story += [Spacer(1, 10), X.section_title("Radiations détectées", W), Spacer(1, 4)] + _table(
        removed, cols[:6] + [("retire_le", "Retiré le", .2)], W, 60)
    if not news.empty:
        story += [Spacer(1, 10), X.section_title("Actualités sanctions & conformité", W), Spacer(1, 4)]
        story += _table(news, [("date", "Date", .1), ("entite", "Entité", .14), ("mesure", "Mesure", .1),
                               ("pays", "Pays", .1), ("titre", "Titre", .44), ("media", "Média", .12)], W, 60)
    story += [Spacer(1, 10), X.footer_line("Rapport de veille sanctions", W)]
    return X.build_pdf(story, pagesize=size, title="CWP – Rapport de veille")


# --------------------------------------------------------------------------- #
# HTML interactif (graphiques Plotly, carte OSM, impression PDF par le navigateur)
# --------------------------------------------------------------------------- #
HTML_CSS = """
:root{--gold:#C9A227;--navy:#1F3A5F;--ink:#2B2B2B;--grey:#7A7A7A;--line:#E4E0D5;--cream:#FAF6EA;--bg:#ffffff}
*{box-sizing:border-box}body{margin:0;background:#f3f1ea;color:var(--ink);font:15px/1.5 'Inter','Segoe UI',system-ui,sans-serif}
.page{max-width:1080px;margin:24px auto;background:var(--bg);border-radius:14px;box-shadow:0 8px 30px #0001;padding:34px 40px}
@media(max-width:700px){.page{padding:18px 16px;margin:0;border-radius:0}}
header.h{background:var(--cream);border:1px solid #EADFB4;border-radius:12px;padding:18px 22px;margin-bottom:22px}
.k{font-size:11px;letter-spacing:.18em;font-weight:700;color:var(--gold);text-transform:uppercase}
h1{margin:4px 0;font-size:30px;color:var(--gold);font-weight:600}h2{font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--navy);
border-bottom:2px solid var(--gold);padding-bottom:6px;margin:28px 0 12px}
.sub{color:var(--grey)}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;font-size:11px;letter-spacing:.08em;
text-transform:uppercase;border-bottom:2px solid var(--gold);padding:7px 8px;background:#fcfbf7}td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#faf8f2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.tile{border:1px solid var(--line);border-radius:12px;padding:12px 14px}.tile .l{font-size:11px;letter-spacing:.12em;color:var(--grey);text-transform:uppercase}
.tile .v{font-size:26px;font-weight:700;color:var(--navy)}.score{display:flex;gap:22px;align-items:center;border:1px solid #EADFB4;background:var(--cream);
border-radius:12px;padding:16px 20px;border-left:6px solid var(--c)}.score .n{font-size:46px;font-weight:800;color:var(--c);line-height:1}
.pill{display:inline-block;border:1px solid;border-radius:20px;padding:2px 10px;font-size:12px;margin:0 6px 6px 0}
footer{margin-top:30px;border-top:1px solid #EADFB4;padding-top:10px;font-size:12px;color:var(--grey)}footer b{color:var(--navy)}
.print{position:fixed;right:18px;bottom:18px;background:var(--navy);color:#fff;border:0;border-radius:24px;padding:10px 18px;font-weight:600;cursor:pointer}
iframe{width:100%;height:440px;border:1px solid var(--line);border-radius:12px}
@media print{body{background:#fff}.page{box-shadow:none;margin:0;max-width:none}.print{display:none}}
"""


def _df_html(df, cols, max_rows=200):
    if df is None or df.empty:
        return "<p class='sub'>Aucun élément.</p>"
    th = "".join(f"<th>{html.escape(l)}</th>" for _, l in cols)
    trs = "".join("<tr>" + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c, _ in cols) + "</tr>"
                  for _, r in df.head(max_rows).iterrows())
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def html_page(kicker, title, subtitle, body, context) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — CWP</title><meta name="author" content="{html.escape(X.AUTHOR)}">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"></script><style>{HTML_CSS}</style></head>
<body><div class="page"><header class="h"><div class="k">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1>
<div class="sub">{html.escape(subtitle)}</div></header>{body}
<footer><b>{html.escape(SIG)}</b><br><i>{html.escape(X.DISCLAIMER)}</i><br>{html.escape(context)} · généré le {now}</footer></div>
<button class="print" onclick="window.print()">Imprimer / PDF</button></body></html>"""


def _fig(fig):
    if fig is None:
        return ""
    import plotly.graph_objects as go
    g = go.Figure(fig.to_dict())
    g.update_layout(template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                    font=dict(color="#2B2B2B", family="Inter, Segoe UI, sans-serif"))
    g.update_xaxes(gridcolor="#eeeae0", tickfont=dict(color="#555")); g.update_yaxes(gridcolor="#eeeae0", tickfont=dict(color="#555"))
    g.update_layout(title_font_color="#1F3A5F", legend_font_color="#2B2B2B")
    g.update_traces(textfont_color="#2B2B2B", selector=dict(type="bar"))
    if any(t.type in ("choropleth", "scattergeo") for t in g.data):
        g.update_geos(bgcolor="#ffffff", landcolor="#ece9df", oceancolor="#f7f6f1", countrycolor="#ffffff")
    return g.to_html(include_plotlyjs=False, full_html=False, config={"displaylogo": False, "responsive": True})


def entity_html(p: dict, figs: list | None = None, map_html: str | None = None) -> str:
    col = RISK_HEX.get(p["niveau"], "#7A7A7A")
    pills = "".join(f"<span class='pill' style='color:#C0392B'>⚠ {html.escape(l)}</span>" for l in p["listes_touchees"])
    if p["ppe"]:
        pills += "<span class='pill' style='color:#7B3FC4'>★ PPE</span>"
    body = (f"<div class='score' style='--c:{col}'><div class='n'>{p['score']:.0f}</div><div><b style='color:{col}'>"
            f"RISQUE {p['niveau'].upper()}</b><br>{html.escape(p['vigilance'])}<div style='margin-top:6px'>{pills}</div></div></div>")
    sy = p.get("synthese")
    if sy:
        body += "<h2>Synthèse de l'analyste</h2>" + "".join(f"<p>{html.escape(t)}</p>" for t in sy["texte"])
        body += "<h2>Prochaines étapes</h2><ol>" + "".join(f"<li>{html.escape(t)}</li>" for t in sy["etapes"]) + "</ol>"
    if p.get("trames_recommandees"):
        from cwp.pedago.methodes import by_id
        body += "<h2>Trames recommandées</h2><ul>" + "".join(f"<li><b>{html.escape(by_id(m)['titre'])}</b> — {html.escape(w)}</li>"
                                                            for m, w in p["trames_recommandees"]) + "</ul>"
    if (p.get("fiche") or {}).get("resume"):
        body += f"<h2>Présentation (Wikipédia)</h2><p>{html.escape(p['fiche']['resume'])}</p>"
    body += "<h2>Facteurs du score</h2>" + _df_html(pd.DataFrame(p["contributions"], columns=["f", "p"]),
                                                     [("f", "Facteur"), ("p", "Points")])
    for f in figs or []:
        body += f"<div>{_fig(f)}</div>"
    ident = pd.DataFrame([("Type", p["type"]), ("Pays", p.get("pays_nom") or "—"), ("LEI", p.get("lei") or "—"),
                          ("Société mère", p.get("lei_parent") or "—"), ("SIREN", p.get("siren") or "—"),
                          ("Dirigeants", p.get("dirigeants") or "—"),
                          ("Adresse", p.get("adresse") or (p.get("geo") or {}).get("label", "—"))], columns=["k", "v"])
    body += "<h2>Identification</h2>" + _df_html(ident, [("k", "Champ"), ("v", "Valeur")])
    hits = p["hits"]
    body += "<h2>Correspondances (sanctions & PPE)</h2>" + _df_html(
        hits, [("liste", "Liste"), ("nom", "Nom inscrit"), ("variante", "Variante"), ("programme", "Programme / fonction"),
               ("pays", "Pays"), ("score", "Score"), ("niveau", "Niveau"), ("ajustements", "Ajustements")])
    pr = p.get("presse", pd.DataFrame())
    body += f"<h2>Presse négative ({len(pr)})</h2>" + _df_html(
        pr.sort_values("date", ascending=False) if not pr.empty else pr,
        [("date", "Date"), ("media", "Média"), ("categorie", "Catégorie"), ("titre", "Titre")])
    if map_html:
        body += f"<h2>Localisation (OpenStreetMap)</h2><iframe srcdoc=\"{html.escape(map_html)}\"></iframe>"
    body += (f"<h2>Sources consultées</h2><p>{html.escape(' · '.join(sources_profil(p)))}</p>"
             f"<p class='sub'>{html.escape(DISCLAIMER)}</p>")
    return html_page("Profil d'entité · filtrage LCB-FT", p["nom"],
                     f"{p['type']} · {p.get('pays_nom') or 'pays non renseigné'} · analyse du {p['date']}", body,
                     "Profil d'entité")


def generic_html(kicker, title, subtitle, sections: list[tuple], context) -> str:
    """sections : (titre, contenu) où contenu est un DataFrame+cols, une figure Plotly ou du HTML."""
    body = ""
    for t, c in sections:
        body += f"<h2>{html.escape(t)}</h2>"
        if isinstance(c, tuple):
            body += _df_html(*c)
        elif hasattr(c, "to_html") and hasattr(c, "data"):
            body += _fig(c)
        else:
            body += str(c)
    return html_page(kicker, title, subtitle, body, context)


def tiles_html(items):
    return "<div class='grid'>" + "".join(f"<div class='tile'><div class='l'>{html.escape(l)}</div>"
                                         f"<div class='v'>{html.escape(str(v))}</div></div>" for l, v in items) + "</div>"


def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"CWP": [SIG, X.DISCLAIMER, f"Généré le {datetime.now():%d/%m/%Y %H:%M}"]}).to_excel(xw, sheet_name="Signature", index=False)
        for n, df in sheets.items():
            (df if df is not None and not df.empty else pd.DataFrame({"info": ["Aucun élément"]})).to_excel(
                xw, sheet_name=n[:31], index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col[:200]) + 2))
    return buf.getvalue()
