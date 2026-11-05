"""
cwp.ui.pages.regulatory_flash — Onglet « Regulatory Flash » de CWP.

Veille réglementaire automatique : la page interroge les régulateurs et institutions de référence
(ACPR, TRACFIN, AMF, DG Trésor, Journal officiel, AFA, AMLA, EBA, ESMA, BCE, UE, GAFI, OFAC, FinCEN,
Comité de Bâle — voir regwatch.SOURCES), liste leurs dernières publications et transforme chacune
en fiche « Regulatory Flash » : référence, calendrier, cible, 3 points clés, checklist d'impacts
(KYC, filtrage, gouvernance) et « L'essentiel ».
Exports : PDF A4 et image PNG par fiche, bulletin PDF multi-fiches.

Synthèse : par IA si une clé est présente dans .streamlit/secrets.toml
(ANTHROPIC_API_KEY, MISTRAL_API_KEY ou OLLAMA_URL), sinon extraction automatique.

Intégration :  from cwp.ui.pages.regulatory_flash import render_regulatory_flash ; render_regulatory_flash()
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

from cwp.exports import common as X
from cwp.services import regwatch as rw

IMPACTS = ["Fort", "Modéré", "Faible"]
ESSENTIEL_TITRES = ["Contexte & objet", "Nouveautés & typologies", "Impacts opérationnels"]


def _essentiel(d: dict) -> list[str]:
    """Les 3 paragraphes de « L'essentiel » (compatible avec les anciennes fiches à 2 paragraphes)."""
    e = d.get("essentiel")
    if isinstance(e, list) and len(e) == 3:
        return e
    return [d.get("contexte", ""), "", d.get("risque", "")]

DOMAINES = list(rw.DOMAINS)
PERIODES = {"7 jours": 7, "30 jours": 30, "90 jours": 90}
BULLETIN_MAX = 10

# --------------------------------------------------------------------------- #
# Rendu PDF (ReportLab)
# --------------------------------------------------------------------------- #
_IMPACT_COLOR = {"Fort": X.RED, "Modéré": X.ORANGE, "Faible": X.GREEN}
_IMPACT_HEX = {"Fort": X.HEX["red"], "Modéré": X.HEX["orange"], "Faible": X.HEX["green"]}


def _flowables(d: dict, width: float) -> list:
    s = X.styles()
    out = [X.header_card("Regulatory Flash" + (f" · {d['type']}" if d.get("type") else ""), d["titre"] or "Titre du texte",
                         d["reference"] or "Référence complète", width), Spacer(1, 12)]

    # Bandeau méta : pays / calendrier / cible
    cal = f"Adoption : {d['adoption'] or '—'}<br/>Application : {d['application'] or '—'}"
    meta = [[
        [Paragraph("PAYS / SOURCE", s["label"]), Spacer(1, 2), Paragraph(X.esc(d["pays_source"] or "—"), s["value"])],
        [Paragraph("CALENDRIER", s["label"]), Spacer(1, 2), Paragraph(cal, s["value"])],
        [Paragraph("CIBLE PRIORITAIRE", s["label"]), Spacer(1, 2), Paragraph(X.esc(d["cible"] or "—"), s["value"])],
    ]]
    t = Table(meta, colWidths=[width * 0.30, width * 0.28, width * 0.42])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.6, X.LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 2),
    ]))
    out += [t, Spacer(1, 14)]

    # En 3 points
    rows = [[Paragraph(str(i + 1), s["num"]), Paragraph(X.esc(p or "—"), s["body"])]
            for i, p in enumerate(d["points"])]
    t = Table(rows, colWidths=[22, width - 22])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [X.colors.white, X.ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, X.LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
    ]))
    out += [KeepTogether([X.section_title("En 3 points", width), t]), Spacer(1, 14)]

    # Checklist
    rows = []
    for it in d["checklist"]:
        box = X.BOX_CHECKED if it["fait"] else X.BOX_EMPTY
        imp = it["impact"]
        rows.append([
            Paragraph(f'<font size="12" color="{X.HEX["navy"]}">{box}</font>', s["body"]),
            Paragraph(X.esc(it["domaine"]), s["body_b"]),
            Paragraph(X.esc(it["texte"] or "—"), s["small"]),
            Paragraph(f'<font color="{_IMPACT_HEX.get(imp, X.HEX["grey"])}"><b>{X.esc(imp)}</b></font>', s["small"]),
        ])
    head = [Paragraph("", s["label"]), Paragraph("DOMAINE", s["label"]),
            Paragraph("ACTION À MENER", s["label"]), Paragraph("IMPACT", s["label"])]
    t = Table([head] + rows, colWidths=[20, width * 0.24, width * 0.62 - 20, width * 0.14])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [X.colors.white, X.ROW_ALT]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, X.LINE),
        ("TOPPADDING", (0, 1), (-1, -1), 6), ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (0, -1), 4),
    ]))
    out += [KeepTogether([X.section_title("Impacts systèmes & process — checklist réglementaire", width), t]),
            Spacer(1, 14)]

    # L'essentiel
    ess = [X.section_title("L'essentiel — lecture 2 min", width), Spacer(1, 6)]
    for i, (titre, para) in enumerate(zip(ESSENTIEL_TITRES, _essentiel(d))):
        if para:
            ess += [Paragraph(titre, s["body_b"]), Spacer(1, 2), Paragraph(X.esc(para), s["body"]), Spacer(1, 8)]
    out += ess
    if d.get("sources"):
        out += [Spacer(1, 8), Paragraph(f"<b>Sources :</b> {X.esc(d['sources'])}", s["small_grey"])]

    out += [Spacer(1, 12), X.footer_line(
        "Regulatory Flash · fiche de synthèse : se référer au texte officiel (EUR-Lex, Légifrance, OFAC…)")]
    return out


def flash_pdf(d: dict) -> bytes:
    w = X.CONTENT_W
    return X.build_pdf(_flowables(d, w), title=f"Regulatory Flash — {d['titre']}")


def flash_png(d: dict) -> bytes:
    w = X.CONTENT_W
    return X.pdf_to_png(X.build_fitted_pdf(lambda: _flowables(d, w), title="Regulatory Flash"))


def bulletin_pdf(flashes: list[dict], titre: str) -> bytes:
    """Un PDF regroupant plusieurs flashs (une fiche par page)."""
    w = X.CONTENT_W
    story = []
    for i, d in enumerate(flashes):
        if i:
            story.append(PageBreak())
        story += _flowables(d, w)
    return X.build_pdf(story, title=titre)


@st.cache_data(show_spinner=False)
def _cached_exports(payload: str) -> tuple[bytes, bytes]:
    d = json.loads(payload)
    return flash_pdf(d), flash_png(d)


# --------------------------------------------------------------------------- #
# Aperçu HTML (même charte)
# --------------------------------------------------------------------------- #
def _h(t: str) -> str:
    return X.esc(t).replace("<br/>", "<br>")


def _preview_html(d: dict) -> str:
    c = X.HEX
    pts = "".join(
        f'<div style="display:flex;gap:12px;padding:8px 6px;border-bottom:1px solid {c["line"]};'
        f'background:{"#fff" if i % 2 == 0 else c["row_alt"]}">'
        f'<div style="color:{c["gold"]};font-weight:700;font-size:18px;min-width:16px">{i + 1}</div>'
        f'<div>{_h(p) or "—"}</div></div>' for i, p in enumerate(d["points"]))
    cl = "".join(
        f'<div style="display:grid;grid-template-columns:24px 1.1fr 3fr 70px;gap:10px;padding:8px 6px;'
        f'border-bottom:1px solid {c["line"]};background:{"#fff" if i % 2 == 0 else c["row_alt"]}">'
        f'<div style="font-size:17px;color:{c["navy"]}">{"☑" if it["fait"] else "☐"}</div>'
        f'<div style="font-weight:600">{_h(it["domaine"])}</div>'
        f'<div style="font-size:13px">{_h(it["texte"]) or "—"}</div>'
        f'<div style="font-weight:700;font-size:13px;color:{_IMPACT_HEX.get(it["impact"], c["grey"])}">'
        f'{_h(it["impact"])}</div></div>' for i, it in enumerate(d["checklist"]))
    sec = (f'style="text-transform:uppercase;font-size:12px;font-weight:700;color:{c["navy"]};'
           f'letter-spacing:.04em;border-bottom:2px solid {c["gold"]};padding:0 2px 5px;margin:18px 0 4px"')
    lab = f'style="font-size:10.5px;font-weight:700;color:{c["grey"]};letter-spacing:.05em"'
    ess = "".join(
        f'<div style="font-weight:600;margin-top:{6 if i == 0 else 10}px;color:{c["navy"]}">{_h(t)}</div>'
        f'<div style="color:{c["ink"]}">{_h(p)}</div>'
        for i, (t, p) in enumerate(zip(ESSENTIEL_TITRES, _essentiel(d))) if p)
    src = (f'<div style="color:{c["grey"]};font-size:12px;margin-top:10px"><b>Sources :</b> '
           f'{_h(d["sources"])}</div>') if d.get("sources") else ""
    return f"""
<div style="font-family:Inter,system-ui,sans-serif;color:{c['ink']};font-size:14px;line-height:1.5;
            background:#fff;padding:18px;border-radius:10px;border:1px solid {c['line']}">
  <div style="background:{c['cream']};border:1px solid {c['gold_light']};border-radius:12px;padding:14px 18px">
    <div style="color:{c['gold']};font-weight:700;font-size:11px;letter-spacing:.08em">REGULATORY FLASH{(' · ' + _h(d['type']).upper()) if d.get('type') else ''}</div>
    <div style="color:{c['gold']};font-size:26px;line-height:1.2">{_h(d['titre']) or 'Titre du texte'}</div>
    <div style="color:{c['grey']};font-size:13.5px;margin-top:4px">{_h(d['reference']) or 'Référence complète'}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:0;margin-top:14px">
    <div style="padding-right:10px"><div {lab}>PAYS / SOURCE</div>{_h(d['pays_source']) or '—'}</div>
    <div style="padding:0 10px;border-left:1px solid {c['line']}"><div {lab}>CALENDRIER</div>
      Adoption : {_h(d['adoption']) or '—'}<br>Application : {_h(d['application']) or '—'}</div>
    <div style="padding-left:10px;border-left:1px solid {c['line']}"><div {lab}>CIBLE PRIORITAIRE</div>{_h(d['cible']) or '—'}</div>
  </div>
  <div {sec}>En 3 points</div>{pts}
  <div {sec}>Impacts systèmes &amp; process — checklist réglementaire</div>{cl}
  <div {sec}>L'essentiel — lecture 2 min</div>
  {ess}{src}
  <div style="border-top:1px solid {c['gold_light']};margin-top:14px;padding-top:6px;font-size:12px;color:{c['navy']}">
    <b>{X.COPYRIGHT}</b></div>
  <div style="color:{c['grey']};font-size:10px;font-style:italic">{X.DISCLAIMER}</div>
  <div style="color:{c['grey']};font-size:11px">Regulatory Flash · fiche de synthèse : se référer au texte officiel</div>
</div>"""


# --------------------------------------------------------------------------- #
# Collecte & génération (avec cache)
# --------------------------------------------------------------------------- #
def _secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:  # noqa: BLE001  (pas de secrets.toml)
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch(days: int, sources: tuple) -> tuple[list[dict], list[dict]]:
    return rw.fetch_publications(days, list(sources) or None)


@st.cache_data(ttl=86_400, show_spinner=False, max_entries=300)
def _flash(item_json: str, provider: str | None) -> dict:
    item = json.loads(item_json)
    return rw.build_flash(item, _secrets() if provider else None, use_ai=bool(provider))


def _get_flash(item: dict, provider: str | None) -> dict:
    d = dict(_flash(json.dumps(item, ensure_ascii=False, sort_keys=True), provider))
    edits = st.session_state.get("rf_edits", {}).get(item["link"])
    if edits:
        d.update(edits)
    return d


def _label(it: dict) -> str:
    date = datetime.fromtimestamp(it["ts"]).strftime("%d/%m") if it["ts"] else "--/--"
    return f"{date} · {it['source']} · {it['kind']} — {X.esc(it['title'])[:110]}"


# --------------------------------------------------------------------------- #
# Retouche manuelle (facultative)
# --------------------------------------------------------------------------- #
def _edit_form(link: str, d: dict) -> None:
    with st.expander("✏️ Retoucher la fiche avant export", expanded=False):
        with st.form(f"rf_form_{abs(hash(link))}"):
            e = {}
            e["titre"] = st.text_input("Nom du texte", d["titre"])
            e["reference"] = st.text_area("Référence complète", d["reference"], height=70)
            a, b, c = st.columns(3)
            e["pays_source"] = a.text_input("Pays / source", d["pays_source"])
            e["adoption"] = b.text_input("Adoption / publication", d["adoption"])
            e["application"] = c.text_input("Entrée en application", d["application"])
            e["cible"] = st.text_input("Cible prioritaire", d["cible"])
            labels = ["Objectif central", "Obligation technique clé", "Sanction ou contrainte majeure"]
            e["points"] = [st.text_area(f"{i + 1}. {lab}", d["points"][i], height=70) for i, lab in enumerate(labels)]
            cl = []
            for i, it in enumerate(d["checklist"]):
                x, y = st.columns([4, 1])
                txt = x.text_area(it["domaine"], it["texte"], height=70)
                imp = y.selectbox("Impact", IMPACTS, IMPACTS.index(it["impact"]) if it["impact"] in IMPACTS else 1,
                                  key=f"rf_imp_{i}_{abs(hash(link))}")
                done = y.checkbox("Fait", it.get("fait", False), key=f"rf_done_{i}_{abs(hash(link))}")
                cl.append(dict(domaine=it["domaine"], texte=txt, impact=imp, fait=done))
            e["checklist"] = cl
            cur = _essentiel(d)
            e["essentiel"] = [st.text_area(f"L'essentiel — {t}", cur[i], height=130, key=f"rf_ess_{i}_{abs(hash(link))}")
                              for i, t in enumerate(ESSENTIEL_TITRES)]
            e["contexte"], e["risque"] = e["essentiel"][0], e["essentiel"][2]
            s1, s2 = st.columns(2)
            if s1.form_submit_button("💾 Appliquer les retouches", width="stretch"):
                st.session_state.setdefault("rf_edits", {})[link] = e
                st.rerun()
            if s2.form_submit_button("↩️ Revenir à la fiche générée", width="stretch"):
                st.session_state.setdefault("rf_edits", {}).pop(link, None)
                st.rerun()


# --------------------------------------------------------------------------- #
# Onglet
# --------------------------------------------------------------------------- #
def render_regulatory_flash(show_header: bool = True) -> None:
    if show_header:
        st.markdown("# 📌 Regulatory Flash")
    st.caption("Publications récentes des régulateurs (ACPR, TRACFIN, AMF, AMLA, EBA, GAFI, OFAC…) : "
               f"chaque publication devient une fiche Regulatory Flash.")

    provider = rw.llm_provider(_secrets())

    # ---- Filtres
    c1, c2, c3, c4 = st.columns([1, 2.4, 2, 1.2])
    periode = c1.selectbox("Période", list(PERIODES), index=1, key="rf_periode")
    sources = c2.multiselect("Régulateurs", list(rw.SOURCES), key="rf_sources", placeholder="Tous les régulateurs")
    types = c3.multiselect("Type de publication", [k for k, _ in rw.KINDS] + ["Communiqué / actualité"],
                           key="rf_types", placeholder="Tous les types")
    with c4:
        st.write("")
        only_rel = st.toggle("Conformité uniquement", True, key="rf_rel",
                             help="Masque les publications sans lien avec la conformité, la LCB-FT ou les sanctions.")
    b1, _ = st.columns([1, 3])
    if b1.button("🔄 Actualiser la veille", width="stretch", key="rf_refresh"):
        _fetch.clear()
        st.rerun()

    with st.spinner("Interrogation des régulateurs…"):
        items, status = _fetch(PERIODES[periode], tuple(sorted(sources)))
    if types:
        items = [i for i in items if i["kind"] in types]
    if only_rel:
        items = [i for i in items if i["relevant"]]

    m1, m2, m3 = st.columns(3)
    m1.metric("Publications", len(items))
    m2.metric("Sources actives", f"{sum(1 for s in status if s['Publications'])}/{len(status)}")
    m3.metric("Synthèse", f"IA · {provider}" if provider else "Extraction auto")
    with st.expander("📡 État des sources", expanded=False):
        st.dataframe(pd.DataFrame(status), hide_index=True, width="stretch")
        if not provider:
            st.caption("Pour des fiches rédigées par IA, ajoutez dans les secrets Streamlit "
                       "`ANTHROPIC_API_KEY`, `MISTRAL_API_KEY` ou `OLLAMA_URL` (modèle optionnel : `CWP_LLM_MODEL`).")

    if not items:
        st.warning("Aucune publication trouvée sur la période avec ces filtres. Élargissez la période ou "
                   "consultez « État des sources » pour vérifier que les flux répondent.")
        return

    # ---- Liste + fiche
    by_link = {i["link"]: i for i in items}
    left, right = st.columns([1, 1.55], gap="large")
    with left:
        st.markdown(f"**Publications détectées** · {periode}")
        with st.container(height=760):
            link = st.radio("Publication", list(by_link), format_func=lambda l: _label(by_link[l]),
                            key="rf_sel", label_visibility="collapsed")
    item = by_link.get(link) or items[0]

    with right:
        with st.spinner("Rédaction de la fiche…"):
            d = _get_flash(item, provider)
        retouche = " · retouchée" if item["link"] in st.session_state.get("rf_edits", {}) else ""
        st.caption(f"{d.get('mode', '')}{retouche} · [Lire la publication d'origine]({item['link']})")
        st.markdown(_preview_html(d), unsafe_allow_html=True)
        pdf_b, png_b = _cached_exports(json.dumps(d, ensure_ascii=False, sort_keys=True))
        name = f"regulatory_flash_{X.slug(item['source'])}_{X.slug(d['titre'], 30)}_{datetime.now():%Y%m%d}"
        e1, e2 = st.columns(2)
        e1.download_button("⬇️ PDF (A4)", pdf_b, f"{name}.pdf", "application/pdf", width="stretch")
        e2.download_button("🖼️ Image PNG", png_b, f"{name}.png", "image/png", width="stretch")
        _edit_form(item["link"], d)

    # ---- Bulletin multi-fiches
    st.divider()
    st.markdown("### 📦 Bulletin réglementaire")
    st.caption(f"Regroupe jusqu'à {BULLETIN_MAX} fiches dans un seul PDF (une fiche par page).")
    default = [i["link"] for i in items if i["kind"] != "Communiqué / actualité"][:5] or list(by_link)[:5]
    chosen = st.multiselect("Publications à inclure", list(by_link), default=default,
                            format_func=lambda l: _label(by_link[l]), max_selections=BULLETIN_MAX,
                            key="rf_bulletin")
    if st.button("Générer le bulletin PDF", disabled=not chosen, key="rf_gen_bulletin"):
        prog = st.progress(0.0, "Rédaction des fiches…")
        flashes = []
        for k, l in enumerate(chosen):
            flashes.append(_get_flash(by_link[l], provider))
            prog.progress((k + 1) / len(chosen), f"Fiche {k + 1}/{len(chosen)}")
        st.session_state["rf_bulletin_pdf"] = bulletin_pdf(
            flashes, f"Bulletin réglementaire CWP — {datetime.now():%d/%m/%Y}")
        prog.empty()
    if st.session_state.get("rf_bulletin_pdf"):
        st.download_button("⬇️ Télécharger le bulletin", st.session_state["rf_bulletin_pdf"],
                           f"cwp_bulletin_reglementaire_{datetime.now():%Y%m%d}.pdf", "application/pdf")
