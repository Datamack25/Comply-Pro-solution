"""
🗄️ Centre de données — enrichissement des CSV (un clic = un enrichissement), inventaire,
journal des mises à jour, explorateur, sauvegarde / restauration.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from cwp.ui import components as C
from cwp.data import sources, store, viz
from cwp.data.countries import ref

from cwp.config import COPYRIGHT as SIG  # noqa: E402


def _msg(kind, text):
    st.session_state.setdefault("cwp_msgs", []).append((kind, text))


def _run(label, fn, *a, **kw):
    try:
        with st.spinner(f"{label}…"):
            r = fn(*a, **kw)
        if isinstance(r, dict):
            _msg("success", f"{label} : +{r.get('ajoutes', 0)} nouvelle(s), {r.get('maj', 0)} mise(s) à jour, "
                            f"{r.get('retires', 0)} retrait(s) détecté(s) · {r.get('total', 0)} lignes au total")
        else:
            _msg("success", f"{label} : {len(r)} élément(s) récupéré(s) et ajouté(s) aux données.")
        if fn is sources.enrichir_pays:
            pr = store.load("pays_risque")
            if "wgi_corruption" not in pr or not (pr.wgi_corruption.fillna("") != "").any():
                _msg("warning", "Banque mondiale injoignable : score pays calculé sans les indicateurs WGI "
                                "(GAFI et sanctions seulement). Réessayez plus tard.")
        return r
    except Exception as e:
        _msg("error", f"{label} : source injoignable ou format modifié — {e}")
        return None


def _done():
    st.cache_data.clear()
    st.rerun()


def render_centre_donnees(helpers: dict | None = None):
    C.css()
    helpers = helpers or {}
    st.markdown("# 🗄️ Centre de données")
    st.caption("Chaque bouton télécharge la source officielle et **enrichit** le fichier CSV correspondant : "
               "les nouvelles entrées sont ajoutées et datées, les entrées disparues passent au statut « retiré ». "
               "Rien n'est effacé : l'historique s'accumule à chaque clic.")

    for kind, text in st.session_state.pop("cwp_msgs", []):
        getattr(st, kind)(text)
    stt = store.status()
    sc = C.sanctions()
    j = store.journal()
    last = j.horodatage.max() if not j.empty else "—"
    st.markdown(viz.kpis([
        ("Entrées de sanctions actives", f"{len(sc):,}".replace(",", " "), f"{sc.liste.nunique() if len(sc) else 0} listes", "#e66767"),
        ("Lignes stockées", f"{int(stt.lignes.sum()):,}".replace(",", " "), f"{(stt.lignes > 0).sum()} jeux de données", "#00d4ff"),
        ("Nouveautés du dernier lot", int(stt.nouveaux_dernier_lot.sum()), "toutes sources", "#00ff88"),
        ("Dernier enrichissement", last[:16], f"{len(j)} opérations journalisées", "#f5c542"),
    ]), unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["⚡ Enrichir", "🔎 Explorer les données", "📜 Journal & nouveautés", "💾 Sauvegarde"])

    # ------------------------------------------------------------------ Enrichir
    with t1:
        st.markdown("<div class='sect'>Listes de sanctions officielles</div>", unsafe_allow_html=True)
        if st.button("🔄 Tout enrichir (5 listes + risque pays + actualités)", type="primary", width="stretch"):
            prog = st.progress(0.0)
            steps = list(sources.SANCTION_SOURCES.items())
            for i, (name, (label, fn)) in enumerate(steps):
                _run(label, fn); prog.progress((i + 1) / (len(steps) + 2))
            _run("Risque pays", sources.enrichir_pays); prog.progress((len(steps) + 1) / (len(steps) + 2))
            _persist_news(helpers); prog.progress(1.0)
            _done()
        cols = st.columns(len(sources.SANCTION_SOURCES))
        for col, (name, (label, fn)) in zip(cols, sources.SANCTION_SOURCES.items()):
            row = stt[stt.jeu == name].iloc[0]
            col.markdown(f"<div class='kt' style='--acc:#e66767'><div class='l'>{label}</div>"
                         f"<div class='v'>{int(row.actives):,}</div><div class='s'>actives · maj {row.derniere_maj[:10]}</div></div>"
                         .replace(",", " "), unsafe_allow_html=True)
            if col.button("Enrichir", key=f"enr_{name}", width="stretch"):
                _run(label, fn); _done()

        st.markdown("<div class='sect'>Référentiels & veille</div>", unsafe_allow_html=True)
        a, b, c = st.columns(3)
        with a:
            st.markdown("**🌍 Risque pays**  \nBanque mondiale (6 indicateurs WGI + PIB/hab.), listes GAFI, "
                        "régimes de sanctions, nombre d'entités inscrites.")
            if st.button("Enrichir le risque pays", width="stretch"):
                _run("Risque pays", sources.enrichir_pays); _done()
        with b:
            st.markdown("**📰 Actualités**  \nArchive les articles de la veille CWP (entité, pays, mesure, montant) "
                        "pour l'historique et l'apprentissage automatique.")
            if st.button("Enrichir les actualités", width="stretch"):
                _persist_news(helpers); _done()
        with c:
            st.markdown("**★ PPE (Wikidata)**  \nChefs d'État et de gouvernement, ministres, parlementaires, "
                        "juges suprêmes, banquiers centraux, ambassadeurs.")
            r = ref()
            opts = dict(zip(r.nom, r.iso2))
            sel = st.multiselect("Pays", list(opts), default=["Haïti"], key="ppe_pays", label_visibility="collapsed", placeholder="Toutes / tous")
            if st.button("Enrichir les PPE", width="stretch"):
                for n in sel:
                    _run(f"PPE {n}", sources.ppe_pays, opts[n])
                _done()

        with st.expander("📥 Importer un indice pays externe (IPC Transparency International, Basel AML Index…)"):
            st.caption("Fichier CSV ou Excel avec une colonne pays (ISO2, ISO3 ou nom) et une colonne valeur. "
                       "L'IPC est intégré au score (0–100, plus bas = plus corrompu).")
            up = st.file_uploader("Fichier", type=["csv", "xlsx"], key="imp_idx")
            kind = st.selectbox("Indice", ["cpi", "basel_aml"], format_func=lambda x: {"cpi": "IPC (corruption perçue)",
                                                                                        "basel_aml": "Basel AML Index"}[x])
            if up and st.button("Importer l'indice"):
                df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                n = sources.importer_indice_pays(df, kind)
                st.success(f"{n} pays mis à jour.")

    # ------------------------------------------------------------------ Explorer
    with t2:
        names = [n for n in store.CATALOGUE if not store.load(n).empty]
        if not names:
            C.empty_state("Aucune donnée pour l'instant.", "Lancez un enrichissement dans l'onglet ⚡ Enrichir.")
        else:
            c1, c2, c3 = st.columns([1.4, 2, 1])
            n = c1.selectbox("Jeu de données", names, format_func=lambda x: store.CATALOGUE[x][0])
            q = c2.text_input("Filtrer (texte libre)", key="exp_q")
            only = c3.selectbox("Statut", ["tous", "actif", "retiré"])
            df = store.load(n)
            if q:
                df = df[df.apply(lambda r: q.lower() in " ".join(r.astype(str)).lower(), axis=1)]
            if only != "tous" and "statut" in df:
                df = df[df.statut == only]
            st.caption(f"{len(df):,} ligne(s) · source : {store.CATALOGUE[n][1]}".replace(",", " "))
            st.dataframe(df, width="stretch", height=460, hide_index=True)
            d1, d2 = st.columns(2)
            d1.download_button("📥 CSV filtré", df.to_csv(index=False).encode("utf-8-sig"), f"cwp_{n}.csv", "text/csv",
                               width="stretch")
            from cwp.data.reports import to_excel
            d2.download_button("📥 Excel filtré", to_excel({n: df}), f"cwp_{n}.xlsx", width="stretch")

    # ------------------------------------------------------------------ Journal
    with t3:
        if j.empty:
            C.empty_state("Journal vide.", "Il se remplit à chaque enrichissement.")
        else:
            jj = j.copy()
            jj["jour"] = jj.horodatage.str[:10]
            jj["ajoutes"] = pd.to_numeric(jj.ajoutes, errors="coerce").fillna(0)
            agg = jj.groupby(["jour", "jeu"], as_index=False).ajoutes.sum()
            agg["jeu"] = agg.jeu.map(lambda x: store.CATALOGUE.get(x, (x,))[0])
            if agg.ajoutes.sum():
                C.plot(viz.stacked_bar(agg, "jour", "ajoutes", "jeu", title="Lignes ajoutées par jour et par jeu de données"))
            st.dataframe(j.sort_values("horodatage", ascending=False), width="stretch", hide_index=True, height=300)
        st.markdown("<div class='sect'>Dernières inscriptions détectées sur les listes</div>", unsafe_allow_html=True)
        full = sources.sanctions_consolidees(actives_only=False)
        if not full.empty:
            new = full.sort_values("premiere_vue", ascending=False)
            first_batch = full.groupby("liste").premiere_vue.transform("min")
            new = new[new.premiere_vue > first_batch.loc[new.index]]  # hors chargement initial
            if new.empty:
                st.info("Pas encore de nouveauté : les nouvelles inscriptions apparaîtront à partir du 2ᵉ enrichissement "
                        "d'une liste (le premier constitue la base de référence).")
            st.dataframe(new[["premiere_vue", "liste", "nom", "type", "programme", "pays", "date_inscription"]].head(300),
                         width="stretch", hide_index=True)
            gone = full[full.statut == "retiré"]
            if not gone.empty:
                st.markdown(f"**Radiations détectées : {len(gone)}**")
                st.dataframe(gone[["retire_le", "liste", "nom", "type", "programme", "pays"]], width="stretch",
                             hide_index=True)

    # ------------------------------------------------------------------ Sauvegarde
    with t4:
        st.info("Sur Streamlit Community Cloud, le disque est réinitialisé à chaque redémarrage de l'application. "
                "Téléchargez régulièrement la sauvegarde ZIP (ou committez le dossier `data/`) ; la restauration "
                "fusionne les fichiers sans rien perdre.")
        a, b = st.columns(2)
        a.download_button("💾 Sauvegarde complète (ZIP de tous les CSV)", store.export_zip(),
                          f"cwp_donnees_{datetime.now():%Y%m%d_%H%M}.zip", "application/zip", width="stretch")
        if b.button("📊 Préparer l'export Excel complet", width="stretch"):
            st.session_state["xl_full"] = store.export_excel()
        if "xl_full" in st.session_state:
            b.download_button("📥 Télécharger l'Excel complet", st.session_state["xl_full"],
                              f"cwp_donnees_{datetime.now():%Y%m%d}.xlsx", width="stretch")
        up = st.file_uploader("♻️ Restaurer une sauvegarde ZIP", type=["zip"])
        if up and st.button("Restaurer et fusionner"):
            done = store.import_zip(up.read())
            st.cache_data.clear()
            st.success(f"{len(done)} fichier(s) fusionné(s) : {', '.join(done)}")
        st.dataframe(stt, width="stretch", hide_index=True)
        st.caption(SIG)


def _persist_news(helpers):
    fa, fac, enrich = helpers.get("fetch_all"), helpers.get("fetch_actions"), helpers.get("enrich")
    if not (fa and enrich):
        _msg("warning", "Module de veille indisponible.")
        return
    with st.spinner("Archivage des actualités…"):
        fa.clear()
        items = fa() + ([i for i in fac()] if fac else [])
        if not items:
            _msg("warning", "Actualités : aucun article reçu (flux de presse injoignables).")
            return
        from cwp.services.news import archive
        r = archive(items)
    _msg("success", f"Actualités : +{r['ajoutes']} nouvelle(s) · {r['total']} au total dans l'historique.")
