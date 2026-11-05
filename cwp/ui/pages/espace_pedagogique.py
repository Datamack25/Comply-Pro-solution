"""
🎓 Espace pédagogique — glossaire (rédigé + Wikipédia + personnel), méthodologies d'analyse,
cas d'étude, trames PDF / Excel téléchargeables, quiz.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import viz
from cwp.pedago import cas, exports, glossaire, methodes, trames

PUB_FILTER = {"Tous": None, **{v: k for k, v in methodes.PUBLICS.items()}}


@st.cache_data(show_spinner=False)
def tpdf(mid):
    return trames.trame_pdf(methodes.by_id(mid))


@st.cache_data(show_spinner=False)
def txls(mid):
    return trames.trame_xlsx(methodes.by_id(mid))


@st.cache_data(show_spinner=False)
def cpdf(cid, corrige):
    return exports.case_pdf(cas.by_id(cid), corrige)


def render_espace_pedagogique():
    C.css()
    st.markdown("# 🎓 Espace pédagogique")
    st.caption("Pour l'analyste conformité, l'analyste financier, l'expert sanctions & embargos et l'analyste fraude : "
               "glossaire, méthodologies pas à pas, cas d'étude corrigés et trames prêtes à l'emploi (PDF et Excel).")
    g = _glossary()
    st.markdown(viz.kpis([
        ("Termes au glossaire", f"{len(g):,}".replace(",", " "), f"{g.categorie.nunique()} catégories", "#00d4ff"),
        ("Méthodologies", len(methodes.METHODES), "N1, N2, KYC, sanctions, fraude…", "#00ff88"),
        ("Cas d'étude", len(cas.CAS), f"{sum(c['type'] == 'Affaire publique' for c in cas.CAS)} affaires publiques", "#f5c542"),
        ("Trames", len(methodes.METHODES) * 2, "PDF + Excel", "#9085e9")]), unsafe_allow_html=True)
    t = st.tabs(["📖 Glossaire", "🧭 Méthodologies", "📂 Cas d'étude", "🗂️ Trames à télécharger", "🎯 Quiz"])
    with t[0]:
        _tab_glossaire(g)
    with t[1]:
        _tab_methodes()
    with t[2]:
        _tab_cas()
    with t[3]:
        _tab_trames()
    with t[4]:
        _tab_quiz(g)


@st.cache_data(show_spinner=False)
def _glossary_cached(key):
    return glossaire.load()


def _glossary():
    import os
    from cwp.data import store
    key = tuple(os.path.getmtime(store.path(n)) if os.path.exists(store.path(n)) else 0 for n in ("glossaire_wiki", "glossaire_perso"))
    return _glossary_cached(key)


# --------------------------------------------------------------------------- glossaire
def _tab_glossaire(g):
    c1, c2, c3, c4 = st.columns([2.2, 1.4, 1, 1])
    q = c1.text_input("Rechercher un terme ou un mot de la définition", key="gq")
    cats = c2.multiselect("Catégories", sorted(g.categorie.unique()), key="gcat", placeholder="Toutes / tous")
    niv = c3.multiselect("Niveau", sorted(g.niveau.unique()), key="gniv", placeholder="Toutes / tous")
    lettre = c4.selectbox("Lettre", ["Toutes"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), key="glet")
    d = g
    if q:
        k = glossaire.norm(q)
        d = d[d.cle.str.contains(k, regex=False) | d.definition.map(glossaire.norm).str.contains(k, regex=False)]
        d = d.assign(_p=~d.cle.str.contains(k, regex=False)).sort_values(["_p", "terme"]).drop(columns="_p")
    if cats:
        d = d[d.categorie.isin(cats)]
    if niv:
        d = d[d.niveau.isin(niv)]
    if lettre != "Toutes":
        d = d[d.cle.str.upper().str.startswith(lettre)]
    st.caption(f"{len(d)} terme(s)")
    per = 40
    pages = max(1, (len(d) - 1) // per + 1)
    pg = st.number_input("Page", 1, pages, 1, key="gpage") if pages > 1 else 1
    for r in d.iloc[(pg - 1) * per: pg * per].itertuples():
        src = f"Source : {r.source}"
        link = f" · <a href='{html.escape(r.lien)}' target='_blank'>article</a>" if getattr(r, "lien", "") else ""
        st.markdown(f"<div class='card'><span class='tag'>{html.escape(r.categorie)}</span><span class='tag new'>{html.escape(r.niveau)}</span>"
                    f"<b style='font-size:1.08rem;color:#e8f4ff'>{html.escape(r.terme)}</b><br>"
                    f"<span style='color:#b8cde0'>{html.escape(r.definition)}</span>"
                    + (f"<br><span class='meta'>Actualité : {html.escape(r.actualite)}</span>" if getattr(r, "actualite", "") else "")
                    + f"<div class='srcline'>{html.escape(src)}{link}</div></div>", unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    cols = ["terme", "categorie", "niveau", "definition", "source", "lien"]
    e1.download_button("📥 Glossaire filtré (CSV)", d[cols].to_csv(index=False).encode("utf-8-sig"), "cwp_glossaire.csv", width="stretch")
    from cwp.data.reports import to_excel
    e2.download_button("📊 Glossaire filtré (Excel)", to_excel({"Glossaire": d[cols]}), "cwp_glossaire.xlsx", width="stretch")
    if e3.button("📄 Préparer le PDF du glossaire filtré", width="stretch"):
        st.session_state["gl_pdf"] = exports.glossary_pdf(d.head(1500))
    if "gl_pdf" in st.session_state:
        e3.download_button("📄 Télécharger le PDF", st.session_state["gl_pdf"], "cwp_glossaire.pdf", "application/pdf", width="stretch")

    with st.expander("🌐 Enrichir le glossaire depuis Wikipédia (plusieurs milliers de termes possibles)"):
        st.caption("Importe le résumé des articles de catégories Wikipédia (2 phrases, licence CC BY-SA, source citée). "
                   "Chaque clic ajoute les termes absents ; les définitions rédigées par CWP restent prioritaires.")
        dom = st.multiselect("Domaines", list(glossaire.WIKI_CATEGORIES), default=list(glossaire.WIKI_CATEGORIES)[:6], placeholder="Toutes / tous")
        n = st.slider("Articles maximum par catégorie Wikipédia", 50, 500, 200, 50)
        extra = st.text_input("Catégorie Wikipédia supplémentaire (facultatif)", placeholder="ex. Droit pénal des affaires")
        if st.button("Enrichir depuis Wikipédia", type="primary"):
            bar = st.progress(0.0); tot = 0
            jobs = [(d_, c) for d_ in dom for c in glossaire.WIKI_CATEGORIES[d_]] + ([("Autre", extra)] if extra else [])
            for i, (d_, c) in enumerate(jobs):
                r = glossaire.enrich_wikipedia([c], d_, n)
                tot += r.get("ajoutes", 0)
                bar.progress((i + 1) / len(jobs), f"{c} · +{r.get('ajoutes', 0)}")
            st.cache_data.clear()
            if tot:
                st.success(f"{tot} terme(s) ajouté(s).")
            else:
                st.warning("Aucun terme ajouté : Wikipédia injoignable ou catégories déjà importées.")
    with st.expander("➕ Importer vos propres termes (CSV ou Excel : terme, definition, categorie)"):
        up = st.file_uploader("Fichier", type=["csv", "xlsx"], key="gl_up")
        if up and st.button("Importer"):
            df = pd.read_csv(up, sep=None, engine="python") if up.name.endswith(".csv") else pd.read_excel(up)
            r = glossaire.import_perso(df); st.cache_data.clear()
            st.success(f"{r['ajoutes']} terme(s) ajouté(s), {r['maj']} mis à jour.")


# --------------------------------------------------------------------------- méthodologies
def _tab_methodes():
    c1, c2 = st.columns(2)
    pub = c1.selectbox("Je suis…", list(PUB_FILTER))
    fam = c2.selectbox("Famille", ["Toutes"] + sorted({m["famille"] for m in methodes.METHODES}))
    ms = [m for m in methodes.METHODES if (PUB_FILTER[pub] is None or PUB_FILTER[pub] in m["publics"])
          and (fam == "Toutes" or m["famille"] == fam)]
    for m in ms:
        with st.expander(f"{m['famille']} · {m['titre']}"):
            st.markdown(f"**Objectif.** {m['objectif']}")
            a, b = st.columns(2)
            a.markdown("**Quand l'utiliser**\n" + "\n".join(f"- {x}" for x in m["declencheurs"]))
            b.markdown("**Livrable**\n\n" + m["livrable"])
            st.markdown("<div class='sect'>Méthodologie pas à pas</div>", unsafe_allow_html=True)
            for i, (t_, d_) in enumerate(m["etapes"], 1):
                st.markdown(f"**{i}. {t_}** — {d_}")
            a, b = st.columns(2)
            a.markdown("<div class='sect'>Signaux d'alerte</div>" + "".join(f"<div>⚑ {html.escape(x)}</div>" for x in m["red_flags"]),
                       unsafe_allow_html=True)
            b.markdown("<div class='sect'>Grille de cotation</div>" + "".join(
                f"<div class='fl'><span>{html.escape(t_)}</span><span>{w}</span></div>" for t_, w in m["indicateurs"]), unsafe_allow_html=True)
            a, b = st.columns(2)
            a.markdown("**Points de contrôle**\n" + "\n".join(f"- {x}" for x in m["controles"]))
            b.markdown("**Erreurs fréquentes**\n" + "\n".join(f"- {x}" for x in m["erreurs"]))
            st.markdown(f"**Sources :** {' · '.join(m['sources'])}  \n**Textes :** {' · '.join(m['textes'])}")
            lies = [c for c in cas.CAS if c["methode"] == m["id"]]
            if lies:
                st.markdown("**Cas d'étude liés :** " + " · ".join(c["titre"] for c in lies))
            d1, d2 = st.columns(2)
            d1.download_button("📄 Trame PDF (mode d'emploi + formulaire)", tpdf(m['id']), f"cwp_trame_{m['id']}.pdf",
                               "application/pdf", key=f"mp_{m['id']}", width="stretch")
            d2.download_button("📊 Trame Excel (cotation automatique)", txls(m['id']), f"cwp_trame_{m['id']}.xlsx",
                               key=f"mx_{m['id']}", width="stretch")


# --------------------------------------------------------------------------- cas
def _tab_cas():
    c1, c2, c3 = st.columns(3)
    typ = c1.selectbox("Type", ["Tous", "Cas pédagogique", "Affaire publique"])
    themes = sorted({c["theme"] for c in cas.CAS})
    th = c2.selectbox("Thème", ["Tous"] + themes)
    niv = c3.selectbox("Niveau", ["Tous"] + sorted({c["niveau"] for c in cas.CAS}))
    cs = [c for c in cas.CAS if (typ == "Tous" or c["type"] == typ) and (th == "Tous" or c["theme"] == th)
          and (niv == "Tous" or c["niveau"] == niv)]
    for c in cs:
        m = methodes.by_id(c["methode"])
        with st.expander(f"{'📘' if c['type'] == 'Cas pédagogique' else '🏛️'} {c['titre']} · {c['theme']} · {c['niveau']}"):
            st.markdown(f"**Contexte.** {c['contexte']}")
            st.markdown("**Faits constatés**\n" + "\n".join(f"- {x}" for x in c["faits"]))
            st.markdown("**À vous de jouer**\n" + "\n".join(f"- {x}" for x in c["questions"]))
            if st.toggle("Afficher le corrigé", key=f"cor_{c['id']}"):
                st.markdown("**Signaux d'alerte**\n" + "\n".join(f"- ⚑ {x}" for x in c["signaux"]))
                st.markdown("**Démarche**\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(c["demarche"], 1)))
                st.success(c["conclusion"])
            st.caption(("Cas fictif à visée pédagogique." if c["type"] == "Cas pédagogique"
                        else "Faits publics simplifiés — vérifier les sources officielles avant de citer.")
                       + f" Trame à utiliser : {m['titre']}.")
            d1, d2, d3 = st.columns(3)
            d1.download_button("📄 Énoncé (PDF)", cpdf(c['id'], False), f"cwp_cas_{c['id']}_enonce.pdf", "application/pdf",
                               key=f"ce_{c['id']}", width="stretch")
            d2.download_button("📄 Énoncé + corrigé (PDF)", cpdf(c['id'], True), f"cwp_cas_{c['id']}_corrige.pdf",
                               "application/pdf", key=f"cc_{c['id']}", width="stretch")
            d3.download_button("📊 Trame Excel à remplir", txls(m['id']), f"cwp_trame_{m['id']}.xlsx", key=f"ct_{c['id']}",
                               width="stretch")


# --------------------------------------------------------------------------- trames
def _tab_trames():
    st.markdown("Chaque trame existe en **PDF** (première page = mode d'emploi et méthodologie, puis formulaire à remplir, "
                "grille de cotation, signaux d'alerte et décision) et en **Excel** (cellules jaunes à remplir, listes déroulantes, "
                "onglets de tableaux, **cotation et niveau de risque calculés automatiquement**, onglet décision).")
    rows = []
    for m in methodes.METHODES:
        tot, t1, t2 = trames.thresholds(m)
        rows.append(dict(Trame=m["titre"], Famille=m["famille"], Public=", ".join(methodes.PUBLICS[p] for p in m["publics"]),
                         Quand=" ; ".join(m["declencheurs"][:2]), Seuils=f"modéré ≥ {t1} · élevé ≥ {t2} / {tot}"))
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    with st.expander("ℹ️ Comment utiliser une trame (procédure commune)"):
        for i, x in enumerate(trames.GUIDE_COMMUN, 1):
            st.markdown(f"{i}. {x}")
    for m in methodes.METHODES:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{m['titre']}**  \n<span class='meta'>{html.escape(m['objectif'])}</span>", unsafe_allow_html=True)
        c2.download_button("📄 PDF", tpdf(m['id']), f"cwp_trame_{m['id']}.pdf", "application/pdf", key=f"tp_{m['id']}", width="stretch")
        c3.download_button("📊 Excel", txls(m['id']), f"cwp_trame_{m['id']}.xlsx", key=f"tx_{m['id']}", width="stretch")
    if st.button("📦 Préparer le pack complet (toutes les trames PDF + Excel, ZIP)", type="primary"):
        with st.spinner("Génération…"):
            st.session_state["pack"] = trames.pack_zip()
    if "pack" in st.session_state:
        st.download_button("⬇️ Télécharger le pack complet", st.session_state["pack"], "cwp_trames.zip", "application/zip")


# --------------------------------------------------------------------------- quiz
def _tab_quiz(g):
    c1, c2, c3 = st.columns([2, 1, 1])
    cat = c1.selectbox("Catégorie", ["Toutes"] + sorted(g[g.niveau == "Fondamental"].categorie.unique()), key="qcat")
    n = c2.slider("Questions", 5, 20, 10, key="qn")
    if c3.button("🎲 Nouveau quiz", width="stretch") or "quiz" not in st.session_state:
        base = g[g.niveau.isin(["Fondamental", "Approfondi"])]
        st.session_state["quiz"] = glossaire.quiz(base, n, None if cat == "Toutes" else cat)
        st.session_state["quiz_done"] = False
    qs = st.session_state["quiz"]
    with st.form("quiz_form"):
        answers = [st.radio(f"**{i}.** {q['definition']}", q["options"], index=None, key=f"qq{i}") for i, q in enumerate(qs, 1)]
        ok = st.form_submit_button("Corriger", type="primary")
    if ok:
        good = sum(a == q["reponse"] for a, q in zip(answers, qs))
        st.markdown(viz.kpis([("Score", f"{good} / {len(qs)}", f"{good / max(len(qs), 1):.0%}", "#00ff88" if good / max(len(qs), 1) >= .7 else "#fab219")]),
                    unsafe_allow_html=True)
        for i, (a, q) in enumerate(zip(answers, qs), 1):
            if a != q["reponse"]:
                st.markdown(f"**{i}.** ✗ votre réponse : {a or '—'} · bonne réponse : **{q['reponse']}**")
