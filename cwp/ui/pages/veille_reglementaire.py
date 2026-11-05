"""
cwp.ui.pages.veille_reglementaire — Sous-onglet « Veille réglementaire » de la page Veille de CWP.

Deux vues :
- Registre & calendrier : textes adoptés depuis 2021, en vigueur, à venir ou en cours d'adoption
  (cwp/content/registre_reglementaire.py), avec prochaines échéances, frise chronologique, filtres,
  fiche Regulatory Flash par texte (PDF / PNG), export Excel et recueil PDF.
- Publications récentes : veille automatique des régulateurs (cwp/services/regwatch.py), via la page Regulatory Flash.

Intégration (app.py, page Veille) :
    from cwp.ui.pages.veille_reglementaire import render_veille_reglementaire
    render_veille_reglementaire()
"""
from __future__ import annotations

import io
import json
from datetime import date, datetime

import pandas as pd
import streamlit as st

from cwp.exports import common as X
from cwp.services import regwatch as rw
from cwp.ui.pages import regulatory_flash as T
from cwp.content.registre_reglementaire import REGISTRE, RESUMES, THEMES

STATUTS = ["En vigueur", "En vigueur · échéances à venir", "À venir", "En cours d'adoption"]
STATUT_COLOR = {"En vigueur": X.HEX["green"], "En vigueur · échéances à venir": X.HEX["navy"],
                "À venir": X.HEX["orange"], "En cours d'adoption": X.HEX["purple"]}
RECUEIL_MAX = 30

MISE_EN_OEUVRE = {
    "LCB-FT": "Mise en œuvre : mise à jour de la classification des risques, des procédures KYC et des paramètres "
              "de surveillance, avec une traçabilité des contrôles attendue par le superviseur.",
    "Sanctions & embargos": "Mise en œuvre : mise à jour des listes et des règles de filtrage, calibrage des seuils "
                            "de correspondance pour limiter les faux positifs et documentation du traitement des alertes.",
    "Crypto-actifs": "Mise en œuvre : outils d'analyse on-chain, échange des informations « travel rule » entre "
                     "prestataires et contrôles sur les adresses auto-hébergées.",
    "Paiements": "Mise en œuvre : adaptation des chaînes de paiement, des contrôles antifraude et de l'information "
                 "client, avec des tests avant chaque échéance.",
    "Résilience & numérique": "Mise en œuvre : cartographie des actifs et des prestataires, procédures de gestion "
                              "des incidents et programme de tests, sous la responsabilité de l'organe de direction.",
    "Prudentiel": "Mise en œuvre : adaptation des calculs, des données et du reporting réglementaire, sous le "
                  "contrôle de la fonction de gestion des risques.",
    "ESG & fiscalité": "Mise en œuvre : collecte et fiabilisation des données, procédures de déclaration et revue "
                       "par le contrôle interne.",
}


THEME_TOPIC = {"Sanctions & embargos": "sanctions et embargos", "Crypto-actifs": "crypto-actifs",
               "Paiements": "fraude aux paiements", "Résilience & numérique": "résilience opérationnelle et numérique",
               "Prudentiel": "exigences prudentielles", "ESG & fiscalité": "durabilité et fiscalité"}


def _emetteur(e: dict) -> str:
    ref = e["reference"]
    if e.get("emetteur"):
        return e["emetteur"]
    if ref.startswith("EBA"):
        return "l'Autorité bancaire européenne (EBA)"
    if "GAFI" in e["juridiction"]:
        return "le GAFI"
    if e["id"] == "dac8":
        return "le Conseil de l'Union européenne"
    if e["juridiction"] == "Union européenne":
        return "le Parlement européen et le Conseil de l'Union européenne"
    if ref.startswith("Arrêté"):
        return "le ministre de l'Économie et des Finances"
    if ref.startswith("Ordonnance"):
        return "le Gouvernement"
    return e["juridiction"]


def _topics(e: dict) -> list[dict]:
    first = [rw.topic(THEME_TOPIC[e["theme"]])] if e["theme"] in THEME_TOPIC else []
    text = " ".join([e["nom"], RESUMES.get(e["id"], ""), e["obligation"]])
    rest = [t for t in rw.detect_topics(text, 3) if t not in first]
    return (first + rest)[:2]


def _source_names(e: dict) -> str:
    names = []
    if e["reference"].startswith("EBA"):
        names.append("EBA")
    if "GAFI" in e["juridiction"]:
        names.append("GAFI")
    names.append(rw.source_name(e["lien"], e["juridiction"]))
    return " · ".join(dict.fromkeys(n for n in names if n))


# --------------------------------------------------------------------------- #
# Calculs sur le registre
# --------------------------------------------------------------------------- #
def _d(s: str | None) -> date | None:
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


def _fr(s: str | None) -> str:
    return _d(s).strftime("%d/%m/%Y") if s else "—"


def statut(e: dict, today: date | None = None) -> str:
    today = today or date.today()
    if e.get("projet"):
        return "En cours d'adoption"
    app = _d(e.get("application"))
    if app and app > today:
        return "À venir"
    if any(_d(d) > today for d, _ in e.get("jalons", [])):
        return "En vigueur · échéances à venir"
    return "En vigueur"


def milestones(entries: list[dict]) -> list[dict]:
    rows = []
    for e in entries:
        pts = [(e["adoption"], "Adoption" if not e.get("projet") else "Accord / proposition")]
        if e.get("application") and e["application"] not in {d for d, _ in e.get("jalons", [])}:
            pts.append((e["application"], "Application" if e["type"] not in ("Directive",) else
                        "Transposition / application"))
        pts += list(e.get("jalons", []))
        seen = set()
        for d, lab in pts:
            if (d, lab) in seen:
                continue
            seen.add((d, lab))
            rows.append(dict(id=e["id"], Texte=e["nom"], Thème=e["theme"], Date=_d(d), Étape=lab))
    return rows


def upcoming(entries: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    ms = [m for m in milestones(entries) if m["Date"] >= today and m["Étape"] not in ("Adoption",)]
    # une même date pour application et jalon identique : on garde le libellé le plus précis
    ms.sort(key=lambda m: (m["Date"], m["Texte"]))
    out, seen = [], set()
    for m in ms:
        k = (m["id"], m["Date"])
        if k in seen:
            continue
        seen.add(k)
        out.append(m)
    return out


# --------------------------------------------------------------------------- #
# Fiche Regulatory Flash à partir d'une entrée du registre
# --------------------------------------------------------------------------- #
def _month_year(s: str | None) -> str:
    if not s:
        return "Non publiée"
    d = _d(s)
    return f"{rw.MONTHS_FR[d.month - 1].capitalize()} {d.year}"


def _item(e: dict) -> dict:
    text = " ".join([RESUMES.get(e["id"], ""), e["objectif"], e["obligation"], e["contrainte"], e.get("cible", "")])
    ts = datetime.strptime(e["adoption"], "%Y-%m-%d").timestamp()
    return dict(source=e["juridiction"], juridiction=e["juridiction"], cible_defaut=e["cible"],
                title=f"{e['nom']} — {e['reference']}", desc=text, link=e["lien"], ts=ts,
                kind=e["type"], relevant=True, publisher="")


@st.cache_data(ttl=86_400, show_spinner=False, max_entries=200)
def _registre_flash(entry_json: str, provider: str | None) -> dict:
    e = json.loads(entry_json)
    item = _item(e)
    if provider:
        d = rw.build_flash(item, T._secrets(), use_ai=True)
    else:
        d = rw.extractive_flash(item, "")
    st_ = statut(e)
    jal = "; ".join(f"{_fr(dt)} : {lab}" for dt, lab in e.get("jalons", []))
    # Champs fiabilisés par le registre (priment sur l'extraction / l'IA)
    d.update(
        titre=e["nom"], reference=e["reference"], pays_source=e["juridiction"],
        adoption=_month_year(e["adoption"]) + (" (accord provisoire)" if e.get("projet") else ""),
        application=(_month_year(e["application"]) if e.get("application") else "À confirmer")
        + (" · transposition" if e["type"] == "Directive" else ""),
        cible=e["cible"], points=[e["objectif"], e["obligation"], e["contrainte"]],
        type=f"{e['type']} · {st_}",
        sources=_source_names(e),
        lien=e["lien"],
    )
    strong = [c["domaine"] for c in d["checklist"] if c["impact"] != "Faible"]
    if not (provider and d.get("mode", "").startswith("Synthèse IA")):
        date_txt = _fr(e["adoption"])
        intro = (f"« {e['nom']} » ({e['reference']}) a fait l'objet d'un accord provisoire le {date_txt}."
                 if e.get("projet") else
                 f"« {e['nom']} » ({e['reference']}) a été adopté le {date_txt} par {_emetteur(e)}.")
        complement = " ".join(x for x in [f"Calendrier : {jal}." if jal else "",
                                          f"Point à vérifier : {e['a_verifier']}" if e.get("a_verifier") else ""] if x)
        d["essentiel"] = rw.essentiel_paragraphs(
            nom=e["nom"], emetteur=e["juridiction"], date=date_txt, kind=e["type"], cible=e["cible"],
            text="", sents=[], ranked=[], strong=strong, objet=RESUMES.get(e["id"], e["objectif"]),
            nouveautes=f"Principales nouveautés : {e['obligation']} {e['contrainte']}",
            topics=_topics(e), intro=intro, complement=complement)
        d["contexte"], d["risque"] = d["essentiel"][0], d["essentiel"][2]
    return d


def registre_flash(e: dict, provider: str | None) -> dict:
    return _registre_flash(json.dumps(e, ensure_ascii=False, sort_keys=True), provider)


# --------------------------------------------------------------------------- #
# Exports
# --------------------------------------------------------------------------- #
def _excel(entries: list[dict]) -> bytes:
    rows = [{"Texte": e["nom"], "Référence": e["reference"], "Juridiction": e["juridiction"],
             "Thème": e["theme"], "Type": e["type"], "Statut": statut(e),
             "Adoption": _fr(e["adoption"]), "Application": _fr(e.get("application")),
             "Échéances": "; ".join(f"{_fr(d)} : {l}" for d, l in e.get("jalons", [])),
             "Cible": e["cible"], "Résumé": RESUMES.get(e["id"], ""), "Objectif": e["objectif"], "Obligation clé": e["obligation"],
             "Contrainte / sanction": e["contrainte"], "À vérifier": e.get("a_verifier", ""),
             "Lien officiel": e["lien"]} for e in entries]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(rows).to_excel(w, index=False, sheet_name="Registre")
        pd.DataFrame([{"Plateforme": X.PLATFORM, "Copyright": X.COPYRIGHT, "Avertissement": X.DISCLAIMER,
                       "Généré le": datetime.now().strftime("%d/%m/%Y %H:%M")}]).to_excel(
            w, index=False, sheet_name="À propos")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Vue « Registre & calendrier »
# --------------------------------------------------------------------------- #
def _timeline(entries: list[dict]) -> None:
    import altair as alt

    df = pd.DataFrame(milestones(entries))
    if df.empty:
        return
    df["Date"] = pd.to_datetime(df["Date"])
    today = pd.DataFrame({"Date": [pd.Timestamp(date.today())]})
    base = alt.Chart(df).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
        y=alt.Y("Texte:N", title=None, sort=alt.SortField("Date", order="ascending"),
                axis=alt.Axis(labelLimit=260)),
        color=alt.Color("Thème:N", legend=alt.Legend(orient="bottom", title=None)),
        tooltip=[alt.Tooltip("Texte:N"), alt.Tooltip("Étape:N"), alt.Tooltip("Date:T", format="%d/%m/%Y")])
    lines = alt.Chart(df).mark_rule(opacity=.35, strokeWidth=2).encode(
        x="min(Date):T", x2="max(Date):T", y=alt.Y("Texte:N", sort=alt.SortField("Date", order="ascending")),
        color="Thème:N")
    pts = base.mark_circle(size=90, opacity=.95)
    rule = alt.Chart(today).mark_rule(color=X.HEX["red"], strokeDash=[4, 4]).encode(x="Date:T")
    st.altair_chart((lines + pts + rule).properties(height=max(260, 24 * df["Texte"].nunique())),
                    width="stretch")
    st.caption("Ligne rouge en pointillés : aujourd'hui. Survolez un point pour voir l'échéance.")


def _registre_view(provider: str | None) -> None:
    today = date.today()
    years = sorted({_d(e["adoption"]).year for e in REGISTRE})

    c1, c2, c3, c4 = st.columns([1.6, 1.6, 1.6, 1.4])
    q = c1.text_input("🔎 Rechercher", placeholder="AMLR, MiCA, travel rule…", key="vr_q")
    stats = c2.multiselect("Statut", STATUTS, key="vr_statut", placeholder="Tous les statuts")
    themes = c3.multiselect("Thème", THEMES, key="vr_theme", placeholder="Tous les thèmes")
    jurs = c4.multiselect("Juridiction", sorted({e["juridiction"] for e in REGISTRE}), key="vr_jur",
                          placeholder="Toutes")
    y0, y1 = st.slider("Année d'adoption", years[0], max(years[-1], today.year), (years[0], max(years[-1], today.year)),
                       key="vr_years")

    def keep(e):
        blob = " ".join([e["nom"], e["reference"], e["objectif"], e["obligation"], e["theme"]]).lower()
        return ((not q or q.lower() in blob) and (not stats or statut(e) in stats)
                and (not themes or e["theme"] in themes) and (not jurs or e["juridiction"] in jurs)
                and y0 <= _d(e["adoption"]).year <= y1)

    entries = sorted([e for e in REGISTRE if keep(e)], key=lambda e: e["adoption"], reverse=True)

    up = upcoming(entries, today)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Textes suivis", len(entries))
    m2.metric("En vigueur", sum(1 for e in entries if statut(e).startswith("En vigueur")))
    m3.metric("À venir / en adoption", sum(1 for e in entries if statut(e) in ("À venir", "En cours d'adoption")))
    m4.metric("Prochaine échéance", up[0]["Date"].strftime("%d/%m/%Y") if up else "—",
              up[0]["Texte"][:28] if up else None, delta_color="off")

    if not entries:
        st.info("Aucun texte ne correspond aux filtres.")
        return

    # ---- Prochaines échéances
    st.markdown("#### ⏭️ Prochaines échéances")
    if up:
        cards = "".join(
            f'<div class="card" style="padding:8px 12px;margin-bottom:6px">'
            f'<span class="tag">J-{(m["Date"] - today).days}</span> '
            f'<b>{m["Date"].strftime("%d/%m/%Y")}</b> · {X.esc(m["Texte"])} '
            f'<span style="color:#9bb4c9">— {X.esc(m["Étape"])}</span></div>' for m in up[:8])
        st.markdown(cards, unsafe_allow_html=True)
    else:
        st.caption("Aucune échéance à venir pour cette sélection.")

    with st.expander("🗓️ Frise chronologique", expanded=False):
        _timeline(entries)

    # ---- Tableau
    st.markdown("#### 📚 Registre")
    table = pd.DataFrame([{"Texte": e["nom"], "Référence": e["reference"], "Juridiction": e["juridiction"],
                           "Thème": e["theme"], "Statut": statut(e), "Adoption": _d(e["adoption"]),
                           "Application": _d(e.get("application")), "Lien": e["lien"]} for e in entries])
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={
                     "Adoption": st.column_config.DateColumn(format="DD/MM/YYYY"),
                     "Application": st.column_config.DateColumn(format="DD/MM/YYYY"),
                     "Lien": st.column_config.LinkColumn("Texte officiel", display_text="Ouvrir"),
                 })

    e1, e2 = st.columns(2)
    e1.download_button("📥 Registre (Excel)", _excel(entries), f"cwp_registre_reglementaire_{today:%Y%m%d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       width="stretch")
    with e2:
        n = min(len(entries), RECUEIL_MAX)
        if st.button(f"📦 Recueil PDF des fiches ({n})", width="stretch", key="vr_recueil"):
            prog = st.progress(0.0, "Rédaction des fiches…")
            flashes = []
            for k, e in enumerate(entries[:n]):
                flashes.append(registre_flash(e, provider))
                prog.progress((k + 1) / n, f"Fiche {k + 1}/{n}")
            st.session_state["vr_recueil_pdf"] = T.bulletin_pdf(
                flashes, f"Recueil réglementaire CWP — {today:%d/%m/%Y}")
            prog.empty()
        if st.session_state.get("vr_recueil_pdf"):
            st.download_button("⬇️ Télécharger le recueil", st.session_state["vr_recueil_pdf"],
                               f"cwp_recueil_reglementaire_{today:%Y%m%d}.pdf", "application/pdf",
                               width="stretch", key="vr_recueil_dl")

    # ---- Fiche du texte sélectionné
    st.divider()
    st.markdown("#### 📌 Regulatory Flash du texte")
    ids = [e["id"] for e in entries]
    by_id = {e["id"]: e for e in entries}
    sel = st.selectbox("Texte", ids, key="vr_sel",
                       format_func=lambda i: f"{by_id[i]['nom']} — {statut(by_id[i])} "
                                             f"(application : {_fr(by_id[i].get('application'))})")
    e = by_id[sel]
    with st.spinner("Rédaction de la fiche…"):
        d = registre_flash(e, provider)
    if e.get("a_verifier"):
        st.warning(f"Point à vérifier : {e['a_verifier']}")
    st.caption(f"{d.get('mode', '')} · calendrier et points clés issus du registre · "
               f"[Ouvrir le texte officiel]({e['lien']})")
    st.markdown(T._preview_html(d), unsafe_allow_html=True)
    pdf_b, png_b = T._cached_exports(json.dumps(d, ensure_ascii=False, sort_keys=True))
    name = f"regulatory_flash_{X.slug(e['nom'], 40)}_{today:%Y%m%d}"
    b1, b2 = st.columns(2)
    b1.download_button("⬇️ PDF (A4)", pdf_b, f"{name}.pdf", "application/pdf", width="stretch",
                       key="vr_pdf")
    b2.download_button("🖼️ Image PNG", png_b, f"{name}.png", "image/png", width="stretch", key="vr_png")


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #
def render_veille_reglementaire() -> None:
    provider = rw.llm_provider(T._secrets())
    st.caption("Textes adoptés depuis 2021, en vigueur, à venir et en cours d'adoption (LCB-FT, sanctions, "
               "crypto-actifs, paiements, résilience, prudentiel, ESG) + publications récentes des régulateurs. "
               "Chaque texte peut être exporté en fiche Regulatory Flash.")
    vue = st.radio("Vue", ["🗓️ Registre & calendrier", "🆕 Publications récentes des régulateurs"],
                   horizontal=True, label_visibility="collapsed", key="vr_vue")
    if vue.startswith("🗓️"):
        _registre_view(provider)
    else:
        T.render_regulatory_flash(show_header=False)
