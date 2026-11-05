"""🇭🇹 Haïti & Caraïbes — dispositif LCB-FT, seuils, contexte, veille régionale, 29 pays de la Caraïbe et renseignements internes."""
from __future__ import annotations

import html
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import store, viz
from cwp.data.countries import ref
from cwp.data.sources import S, _uid
from cwp.pedago import haiti as H
from cwp.ui.pages.caraibes import render_caraibes

STATUS_COL = {"vérifié": "#0ca30c", "source secondaire": "#fab219", "à vérifier": "#d03b3b"}


def _st_color(s):
    for k, v in STATUS_COL.items():
        if s.startswith(k):
            return v
    return "#8aa4ba"


def render_haiti():
    C.css()
    st.markdown("# 🇭🇹 Haïti & Caraïbes — conformité")
    st.caption(f"Base de connaissances CWP · état au {H.VERIFIE_LE}. Chaque élément porte un statut : vérifié, source secondaire ou à vérifier.")
    t = st.tabs(["🏛️ Dispositif & institutions", "📏 Seuils & obligations", "🌪️ Contexte & rapport", "📡 Veille Caraïbes",
                 "🌎 Caraïbe — 29 pays", "🔒 Renseignements internes"])
    with t[0]:
        for i in H.INSTITUTIONS:
            col = _st_color(i["statut"])
            st.markdown(
                f"<div class='card'><span class='tag'>{html.escape(i['type'])}</span><b style='font-size:1.2rem;color:#e8f4ff'>"
                f"{html.escape(i['sigle'])}</b> — {html.escape(i['nom'])}<br><span style='color:#b8cde0'>{html.escape(i['role'])}</span>"
                f"<div style='margin-top:6px'><b>Textes</b> : {html.escape(' ; '.join(i['textes']))}</div>"
                f"<div><b>Assujettis</b> : {html.escape(i['assujettis'])}</div>"
                + "".join(f"<div>▸ {html.escape(x)}</div>" for x in i["a_retenir"])
                + f"<div class='srcline' style='color:{col}'>● {html.escape(i['statut'])}</div></div>", unsafe_allow_html=True)
        st.markdown("Circulaires officielles : page des circulaires de la [BRH](https://www.brh.ht/notes-de-presse/?act=circulaires) · "
                    "évaluation d'Haïti sur le site du [GAFI](https://www.fatf-gafi.org/en/publications/Mutualevaluations/Mer-haiti-2019.html).")
    with t[1]:
        rows = "".join(f"<tr><td>{html.escape(x['texte'])}</td><td style='color:#f5c542;font-family:Share Tech Mono;white-space:nowrap'>"
                       f"{html.escape(x['seuil'])}</td><td>{html.escape(x['obligation'])}</td>"
                       f"<td style='color:{_st_color(x['statut'])}'>● {html.escape(x['statut'])}</td></tr>" for x in H.SEUILS)
        st.markdown(f"<div class='wwrap'><table class='wtable'><thead><tr><th>Texte</th><th>Seuil</th><th>Obligation</th><th>Statut</th></tr>"
                    f"</thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
        st.warning("Le seuil de 1 300 000 gourdes évoqué dans une vidéo d'AyiboPost n'a pas pu être rattaché à un texte : la circulaire "
                   "99-2 de 2018 fixe 600 000 HTG pour l'identification des opérations en espèces. Une circulaire plus récente a pu modifier "
                   "ce montant : consultez la liste des circulaires de la BRH, puis mettez à jour `cwp/pedago/haiti.py` (SEUILS).")
    with t[2]:
        for titre, pts in H.CONTEXTE + H.CARAIBES:
            st.markdown(f"<div class='sect'>{html.escape(titre)}</div>", unsafe_allow_html=True)
            for p in pts:
                st.markdown(f"- {p}")
        st.download_button("📄 Rapport PDF : économie informelle, instabilité et conformité en Haïti et dans la Caraïbe",
                           H.rapport_pdf(), "cwp_rapport_haiti_caraibes.pdf", "application/pdf", type="primary")
    with t[3]:
        _veille()
    with t[4]:
        st.caption("Dispositif LCB-FT, seuils, statuts GAFI / UE / ONU et veille dans la langue de chaque pays : République dominicaine, "
                   "Cuba, Venezuela, Trinité-et-Tobago, Jamaïque, Bahamas, Barbade, Guyana, Suriname, OECO, territoires britanniques, "
                   "néerlandais, français et américains. Chaque information a son lien « Vérifier ».")
        render_caraibes()
    with t[5]:
        _renseignements()


def _veille():
    st.markdown("Articles récents sur la conformité, le blanchiment, la corruption et les sanctions en Haïti et dans la Caraïbe "
                "(Google Actualités, médias haïtiens). Chaque clic enrichit `data/veille_caraibes.csv`.")
    sel = st.multiselect("Thèmes", list(H.VEILLE_QUERIES), default=list(H.VEILLE_QUERIES), placeholder="Thèmes")
    if st.button("📡 Mettre à jour la veille Caraïbes", type="primary"):
        import feedparser
        from cwp.data.notoriete import _clean
        rows = []
        bar = st.progress(0.0)
        qs = [(th, q) for th in sel for q in H.VEILLE_QUERIES[th]]
        for i, (th, q) in enumerate(qs):
            try:
                f = feedparser.parse(S.get(f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=fr&gl=FR&ceid=FR:fr", timeout=20).content)
            except Exception:
                f = None
            for e in (f.entries if f else [])[:40]:
                src = (e.get("source") or {}).get("title", "") if isinstance(e.get("source"), dict) else ""
                ts = time.mktime(e.get("published_parsed")) if e.get("published_parsed") else 0
                title = _clean(e.get("title"), 300)
                if src and title.endswith(" - " + src):
                    title = title[: -(len(src) + 3)]
                rows.append(dict(uid=_uid(e.get("link", "")), theme=th, titre=title, media=src, lien=e.get("link", ""),
                                 date=datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "", requete=q))
            bar.progress((i + 1) / len(qs))
        if rows:
            r = store.append_rows("veille_caraibes", rows, source="Google Actualités")
            st.success(f"+{r['ajoutes']} article(s) · {r['total']} au total.")
        else:
            st.warning("Aucun article reçu (flux injoignables).")
    v = store.load("veille_caraibes")
    if v.empty:
        C.empty_state("Veille vide.", "Cliquez sur « Mettre à jour la veille Caraïbes ».")
        return
    v = v[v.theme.isin(sel)] if sel else v
    q = st.text_input("Filtrer", key="vc_q")
    if q:
        v = v[v.titre.str.contains(q, case=False, na=False)]
    for _, a in v.sort_values("date", ascending=False).head(80).iterrows():
        st.markdown(f"<div style='padding:4px 0;border-bottom:1px solid #12263a'><span class='tag'>{html.escape(a.theme)}</span>"
                    f"<a href='{html.escape(a.lien)}' target='_blank' style='color:#e8f4ff'>{html.escape(a.titre)}</a>"
                    f" <span class='meta'>· {html.escape(a.media)} · {html.escape(a.date)}</span></div>", unsafe_allow_html=True)


FIELDS = ["nom", "type", "pays", "categorie", "description", "source", "date_info", "fiabilite", "credibilite", "confidentialite", "auteur"]


def _renseignements():
    st.markdown("Consignez des informations **non publiques ou locales** (rapports ULCC, communiqués UCREF, décisions de justice haïtiennes, "
                "informations de terrain…) sur des personnes ou entités d'Haïti et de la Caraïbe. Elles sont intégrées au filtrage des noms "
                "et au profil d'entité 360° (liste « Renseignement interne »).")
    st.info("Usage interne : ne saisir que des informations utiles à la conformité, obtenues légalement, avec leur source ; pas de données "
            "sensibles (santé, opinions, vie privée). Évaluer la fiabilité de la source (A–F) et la crédibilité de l'information (1–6). "
            "Durée de conservation et accès restreint à définir avec le DPO (RGPD).")
    r = ref()
    with st.form("rens", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1.3])
        nom = c1.text_input("Nom de la personne / entité *")
        typ = c2.selectbox("Type", ["Personne", "Entité", "Navire"])
        pays = c3.selectbox("Pays", r.nom.tolist(), index=r.nom.tolist().index("Haïti") if "Haïti" in r.nom.tolist() else 0)
        c4, c5, c6 = st.columns(3)
        cat = c4.selectbox("Catégorie", H.CATEGORIES_RENSEIGNEMENT)
        fia = c5.selectbox("Fiabilité de la source", H.FIABILITE, index=2)
        cre = c6.selectbox("Crédibilité de l'information", H.CREDIBILITE, index=2)
        desc = st.text_area("Description factuelle *", placeholder="Faits, montants, dates, procédure en cours…")
        c7, c8, c9, c10 = st.columns(4)
        src = c7.text_input("Source (nom)")
        dt = c8.date_input("Date de l'information")
        conf = c9.selectbox("Confidentialité", ["Interne", "Restreint (conformité)", "Très restreint"])
        aut = c10.text_input("Saisi par")
        alias = st.text_input("Alias / autres orthographes (séparés par « | »)")
        if st.form_submit_button("➕ Ajouter au fichier", type="primary") and nom.strip() and desc.strip():
            iso = r[r.nom == pays].iso2.iloc[0]
            row = dict(uid=_uid(nom, desc), nom=nom.strip(), alias=alias, type=typ, pays=iso, categorie=cat, description=desc.strip(),
                       source=src, date_info=dt.strftime("%Y-%m-%d"), fiabilite=fia, credibilite=cre, confidentialite=conf, auteur=aut)
            store.append_rows("renseignements_internes", [row], source="saisie manuelle")
            st.cache_data.clear()
            st.success(f"Information ajoutée pour {nom}.")
    with st.expander("📥 Import en masse (CSV / Excel avec les colonnes : " + ", ".join(FIELDS) + ")"):
        up = st.file_uploader("Fichier", type=["csv", "xlsx"], key="rens_up")
        if up and st.button("Importer"):
            df = pd.read_csv(up, dtype=str, sep=None, engine="python") if up.name.endswith(".csv") else pd.read_excel(up, dtype=str)
            df = df.fillna("")
            if "nom" not in df:
                st.error("Colonne « nom » manquante.")
            else:
                from cwp.data.countries import to_iso2
                if "pays" in df:
                    df["pays"] = df.pays.map(lambda x: to_iso2(x) or x)
                df["uid"] = [_uid(a, b) for a, b in zip(df.nom, df.get("description", df.nom))]
                res = store.append_rows("renseignements_internes", df, source="import")
                st.cache_data.clear()
                st.success(f"+{res['ajoutes']} ligne(s), {res['maj']} mise(s) à jour.")
        tpl = pd.DataFrame(columns=FIELDS + ["alias"])
        st.download_button("Modèle de fichier (CSV)", tpl.to_csv(index=False).encode("utf-8-sig"), "cwp_modele_renseignements.csv")
    d = store.load("renseignements_internes")
    if not d.empty:
        st.markdown(f"<div class='sect'>Renseignements enregistrés ({len(d)})</div>", unsafe_allow_html=True)
        st.dataframe(d.drop(columns=[c for c in ("uid",) if c in d]), width="stretch", hide_index=True)
        st.download_button("📥 Export (CSV)", d.to_csv(index=False).encode("utf-8-sig"), "cwp_renseignements_internes.csv")
