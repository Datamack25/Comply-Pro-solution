"""📰 Notoriété négative — recherche multi-entités, analyse et notation des articles, 5 niveaux de criticité, PDF par entité."""
from __future__ import annotations

import html
from datetime import datetime

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import notoriete as N
from cwp.data import reports, store, viz
from cwp.data.countries import ref
from cwp.exports.common import slug


def _badge(score, lab=None):
    lv = N.level(score)
    return (f"<span style='display:inline-block;min-width:44px;text-align:center;font-family:Share Tech Mono;font-weight:700;"
            f"padding:2px 8px;border-radius:6px;background:{lv[2]}22;color:{lv[2]};border:1px solid {lv[2]}'>{score:.0f}</span> "
            f"<span style='color:{lv[2]};font-weight:700'>{html.escape(lab or lv[1])}</span>")


def render_notoriete():
    C.css()
    st.markdown("# 📰 Notoriété négative")
    st.caption("Saisissez jusqu'à 7 personnes ou entités. La plateforme combine chaque nom avec des mots-clés négatifs, interroge les "
               "moteurs, lit les articles, les note et conclut sur 5 niveaux de criticité. Un PDF unique par entité regroupe tous les "
               "articles pertinents, leurs liens et leurs résumés.")
    t1, t2, t3 = st.tabs(["🔎 Nouvelle recherche", "📊 Résultats", "🗂️ Historique"])
    with t1:
        _form()
    with t2:
        _results()
    with t3:
        _history()


def _form():
    r = ref()
    if "noto_in" not in st.session_state:
        st.session_state["noto_in"] = pd.DataFrame(dict(nom=[""] * 7, type=["Entité"] * 7, pays=[""] * 7))
    ed = st.data_editor(st.session_state["noto_in"], num_rows="fixed", width="stretch", hide_index=True, key="noto_ed",
                        column_config={"nom": st.column_config.TextColumn("Nom de la personne ou de l'entité", width="large"),
                                       "type": st.column_config.SelectboxColumn("Type", options=["Entité", "Personne", "Navire"]),
                                       "pays": st.column_config.SelectboxColumn("Pays (facultatif)", options=[""] + r.nom.tolist())})
    c1, c2, c3 = st.columns([1.6, 1.4, 1])
    langs = c1.multiselect("Langues", list(N.LANG_LABEL), default=["fr", "en"], format_func=N.LANG_LABEL.get, placeholder="Langues")
    mode = c2.radio("Profondeur", ["Rapide (mots-clés groupés)", "Approfondie (un mot-clé par requête)"], horizontal=False)
    seuil = c3.slider("Seuil de pertinence affiché", 0, 60, 15)
    o = st.columns(4)
    lire = o[0].checkbox("Lire le texte des articles", True, help="Va en profondeur dans les articles les plus pertinents.")
    nb = o[1].number_input("Articles lus / entité", 5, 40, 15, disabled=not lire)
    gd = o[2].checkbox("Inclure GDELT", True, help="Presse mondiale, 65 langues (≈ 10 s de plus par entité).")
    eng = N.web_engine()
    web = o[3].checkbox(f"Recherche web ({eng})" if eng else "Recherche web (clé API absente)", bool(eng), disabled=not eng,
                        help="Google Programmable Search ou Brave Search, 4 pages par requête. Ajouter GOOGLE_CSE_KEY + GOOGLE_CSE_CX ou BRAVE_API_KEY dans les secrets.")
    try:
        from cwp.services.regwatch import llm_provider
        prov = llm_provider(st.secrets)
    except Exception:
        prov = None
    ia = st.checkbox(f"Résumés rédigés par IA ({prov})" if prov else "Résumés rédigés par IA (aucune clé configurée — résumés extractifs)",
                     bool(prov), disabled=not prov)
    with st.expander(f"⚙️ Mots-clés négatifs ({len(N.KEYWORDS)}) — modifiables"):
        kw = pd.DataFrame(N.KEYWORDS, columns=["mot_cle", "gravite", "langue"])
        kw_ed = st.data_editor(kw, num_rows="dynamic", width="stretch", hide_index=True, key="kw_ed",
                               column_config={"gravite": st.column_config.NumberColumn("Gravité (1–5)", min_value=1, max_value=5),
                                              "langue": st.column_config.SelectboxColumn("Langue", options=list(N.LANG_LABEL))})
    rows = ed[ed.nom.fillna("").str.strip() != ""]
    if st.button(f"🚀 Lancer la recherche ({len(rows)} entité(s))", type="primary", disabled=rows.empty or not langs):
        kws = [(str(a), int(b), str(c)) for a, b, c in kw_ed.dropna().itertuples(index=False) if str(a).strip()]
        nmap = dict(zip(r.nom, r.iso2))
        out = []
        for i, row in enumerate(rows.itertuples()):
            bar = st.progress(0.0, f"{row.nom} : démarrage…")
            res = N.run(row.nom.strip(), row.type, nmap.get(row.pays, ""), langs, kws, mode.startswith("Approfondie"), lire, int(nb),
                        gd, web, ia, progress=lambda f, m="", n=row.nom: bar.progress(min(f, 1.0), f"{n} : {m}"))
            out.append(res)
            bar.progress(1.0, f"{row.nom} : {res['nb_resultats']} résultat(s), niveau {res['niveau']}")
        st.session_state["noto_res"] = out
        st.session_state["noto_seuil"] = seuil
        st.success("Recherche terminée : ouvrez l'onglet « 📊 Résultats ».")


def _results():
    res = st.session_state.get("noto_res")
    if not res:
        C.empty_state("Aucune recherche dans cette session.", "Lancez une recherche dans l'onglet « Nouvelle recherche » ou rouvrez-en une depuis l'historique.")
        return
    seuil = st.session_state.get("noto_seuil", 15)
    st.markdown("<div class='sect'>Synthèse du lot</div>", unsafe_allow_html=True)
    rows = "".join(f"<tr><td class='ent'>{html.escape(r['nom'])}</td><td>{html.escape(r['type'])}</td><td>{_badge(r['score'], r['niveau'])}</td>"
                   f"<td>{r['nb_pertinents']} / {r['nb_resultats']}</td><td class='meta'>{html.escape(r['conclusion'])}</td></tr>" for r in res)
    st.markdown(f"<div class='wwrap'><table class='wtable'><thead><tr><th>Entité</th><th>Type</th><th>Criticité</th><th>Pertinents / résultats</th>"
                f"<th>Conclusion</th></tr></thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
    legend = " ".join(f"<span style='color:{lv[2]}'>■</span> {html.escape(lv[1])} (≥ {lv[0]})" for lv in N.LEVELS)
    st.markdown(f"<div class='meta' style='margin:4px 0 12px'>{legend}</div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.download_button("📦 Tous les PDF (ZIP, un PDF par entité)", N.batch_zip(res), f"cwp_notoriete_{datetime.now():%Y%m%d_%H%M}.zip",
                      "application/zip", width="stretch")
    allx = pd.concat([r["articles"].assign(entite=r["nom"]) for r in res if not r["articles"].empty], ignore_index=True) if any(
        not r["articles"].empty for r in res) else pd.DataFrame()
    keep = [k for k in ["entite", "score", "niveau", "titre", "media", "date", "langue", "moteur", "mots_cles", "attenuants", "resume", "lien"] if k in allx]
    b.download_button("📊 Tous les articles (Excel)", reports.to_excel({"Synthèse": pd.DataFrame(
        [{k: r[k] for k in ("nom", "type", "pays", "date", "score", "niveau", "nb_resultats", "nb_pertinents", "synthese")} for r in res]),
        "Articles": allx[keep] if len(allx) else allx}), "cwp_notoriete.xlsx", width="stretch")
    pick = c.selectbox("Entité détaillée", [r["nom"] for r in res], label_visibility="collapsed")
    r = next(x for x in res if x["nom"] == pick)
    _entity(r, seuil)


def _entity(r, seuil):
    col = r["couleur"]
    st.markdown(f"<div class='pf' style='grid-template-columns:200px 1fr;border-color:{col}66'>"
                f"<div class='gauge' style='background:conic-gradient({col} {r['score'] * 3.6}deg,#13293d 0);width:180px;height:180px'>"
                f"<div class='in' style='width:134px;height:134px'><div><div class='n'>{r['score']:.0f}</div>"
                f"<div class='t' style='color:{col};font-size:.8rem'>NIVEAU {r['niveau'][0]}/5</div></div></div></div>"
                f"<div><h2>{html.escape(r['nom'])}</h2><div class='sub'>NOTORIÉTÉ NÉGATIVE · {html.escape(r['date'])} · "
                f"{' · '.join(html.escape(m) for m in r['moteurs'])}</div>"
                f"<div style='color:{col};font-weight:700;font-size:1.15rem'>{html.escape(r['niveau'])}</div>"
                f"<div style='margin-top:6px;color:#cfe3f5'>{html.escape(r['synthese'])}</div></div></div>", unsafe_allow_html=True)
    df = r["articles"]
    d1, d2 = st.columns(2)
    d1.download_button(f"📄 PDF de l'entité ({r['nom']})", N.entity_pdf(r, seuil), f"cwp_notoriete_{slug(r['nom'])}.pdf",
                       "application/pdf", width="stretch", key=f"pdf_{r['nom']}")
    if df.empty:
        st.info("Aucun résultat.")
        return
    dist = df.assign(n=1, niv=df.score.map(lambda s: N.level(s)[1])).groupby("niv", as_index=False).n.sum()
    order = [lv[1] for lv in N.LEVELS]
    import plotly.graph_objects as go
    fig = go.Figure([go.Bar(x=[int(dist[dist.niv == o].n.sum())], y=["Articles"], orientation="h", name=o,
                            marker=dict(color=lv[2], line=dict(color=viz.SURFACE, width=2)),
                            hovertemplate=f"{o} : %{{x}}<extra></extra>") for o, lv in zip(order, N.LEVELS)])
    fig.update_layout(barmode="stack", showlegend=True)
    fig.update_yaxes(showticklabels=False)
    st.markdown("<div class='sect'>Répartition des résultats par niveau</div>", unsafe_allow_html=True)
    C.plot(viz.theme(fig, 150), key=f"dist_{r['nom']}")
    pert = df[df.score >= seuil]
    st.markdown(f"<div class='sect'>Articles pertinents ({len(pert)}) — une ligne par article, résumé dessous</div>", unsafe_allow_html=True)
    for _, a in pert.iterrows():
        lv = N.level(a.score)
        st.markdown(
            f"<div style='border-left:4px solid {lv[2]};padding:6px 12px;margin:6px 0;background:#0a1a2a;border-radius:6px'>"
            f"{_badge(a.score, '')} <a href='{html.escape(a.lien)}' target='_blank' style='color:#e8f4ff;font-weight:600'>{html.escape(a.titre)}</a>"
            f" <span class='meta'>· {html.escape(a.media or '—')} · {html.escape(a.date or '')} · {html.escape(a.moteur)}</span>"
            f"<div style='color:#b8cde0;margin-top:3px'>{html.escape(a.resume)}</div>"
            f"<div class='srcline'>Mots-clés : {html.escape(a.mots_cles or '—')}"
            + (f" · atténuants : {html.escape(a.attenuants)}" if a.attenuants else "") + "</div></div>", unsafe_allow_html=True)
    rest = df[df.score < seuil]
    if len(rest):
        with st.expander(f"Résultats écartés ({len(rest)})"):
            st.dataframe(rest[["score", "titre", "media", "date", "mots_cles", "attenuants", "lien"]], width="stretch", hide_index=True,
                         column_config={"lien": st.column_config.LinkColumn("Lien", display_text="ouvrir")})


def _history():
    h = store.load("notoriete_recherches")
    if h.empty:
        C.empty_state("Aucune recherche enregistrée.", "Chaque recherche est ajoutée à data/notoriete_recherches.csv.")
        return
    h["score"] = pd.to_numeric(h.score, errors="coerce")
    st.dataframe(h.sort_values("date", ascending=False)[["date", "nom", "type", "pays", "score", "niveau", "nb_pertinents", "nb_resultats", "synthese"]],
                 width="stretch", hide_index=True,
                 column_config={"score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f")})
    pick = st.selectbox("Rouvrir une recherche", (h.nom + " · " + h.date).tolist()[::-1])
    if st.button("Rouvrir"):
        row = h[(h.nom + " · " + h.date) == pick].iloc[0]
        arts = store.load("notoriete_articles")
        arts = arts[arts.recherche == row.uid].copy() if not arts.empty else arts
        if not arts.empty:
            arts["score"] = pd.to_numeric(arts.score, errors="coerce").fillna(0)
            arts["presence_nom"] = pd.to_numeric(arts.presence_nom, errors="coerce").fillna(0)
            arts = arts.sort_values("score", ascending=False).drop_duplicates(subset=["titre"])
        lv = N.level(float(row.score))
        st.session_state["noto_res"] = [dict(nom=row.nom, type=row.type, pays=row.pays, date=row.date, score=float(row.score), niveau=row.niveau,
                                             couleur=lv[2], couleur_pdf=lv[3], conclusion=lv[4], articles=arts.sort_values("score", ascending=False),
                                             nb_resultats=int(row.nb_resultats), nb_pertinents=int(row.nb_pertinents), langues=[], approfondi=False,
                                             moteurs=sorted(set(arts.moteur)) if not arts.empty else [], cles=len(N.KEYWORDS), synthese=row.synthese)]
        st.session_state["noto_msg"] = "Recherche rouverte : onglet « 📊 Résultats »."
        st.rerun()
    if st.session_state.get("noto_msg"):
        st.success(st.session_state.pop("noto_msg"))
