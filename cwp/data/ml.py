"""
cwp.data.ml — mode Machine Learning de CWP (scikit-learn, entraîné sur les CSV de data/).

1. Classifieur d'actualités  : TF-IDF + régression logistique ; apprend des étiquettes
                               automatiques puis de vos corrections (data/ml_labels.csv).
2. Segmentation pays         : standardisation + K-means + ACP (carte de proximité des profils).
3. Détection d'anomalies     : Isolation Forest sur les profils d'entités analysés.
4. Typologies de sanctions   : TF-IDF + K-means sur programmes / types / pays / motifs.
5. Tendance des inscriptions : régression linéaire sur les inscriptions mensuelles.
Les modèles sont sauvegardés dans data/models/ (joblib) et ré-entraînés à la demande.
"""
from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd

from . import store

MEASURE_LABELS = {"gel": "Gel des avoirs", "liste": "Liste GAFI", "amende": "Amende", "sanction": "Sanction",
                  "embargo": "Embargo / export", "enquete": "Enquête / poursuite", "regle": "Réglementation",
                  "news": "Actualité"}


def _model_path(name):
    return os.path.join(store.MODEL_DIR, f"{name}.joblib")


def _save(name, obj):
    import joblib
    joblib.dump(obj, _model_path(name))


def load_model(name):
    import joblib
    p = _model_path(name)
    return joblib.load(p) if os.path.exists(p) else None


# --------------------------------------------------------------------------- #
# 1. Classifieur d'actualités
# --------------------------------------------------------------------------- #
def training_set() -> pd.DataFrame:
    a = store.load("actualites")
    if a.empty:
        return pd.DataFrame(columns=["uid", "texte", "label", "origine"])
    a["texte"] = (a.titre.fillna("") + " " + a.resume.fillna("")).str.strip()
    a["label"], a["origine"] = a.mesure_cle, "heuristique"
    lab = store.load("ml_labels")
    if not lab.empty:
        m = dict(zip(lab.uid, lab.label))
        hit = a.uid.isin(m)
        a.loc[hit, "label"] = a.loc[hit, "uid"].map(m)
        a.loc[hit, "origine"] = "validé"
    return a[a.texte.str.len() > 15][["uid", "texte", "label", "origine", "date", "pays"]]


def train_news_classifier() -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import FeatureUnion, Pipeline

    df = training_set()
    vc = df.label.value_counts()
    df = df[df.label.isin(vc[vc >= 3].index)]
    if len(df) < 30 or df.label.nunique() < 2:
        raise ValueError(f"Pas assez de données : {len(df)} actualités exploitables (minimum 30, 2 classes). "
                         "Cliquez sur « Enrichir les actualités » plusieurs jours de suite.")
    # les étiquettes validées comptent 3 fois plus que les étiquettes automatiques
    w = np.where(df.origine == "validé", 3.0, 1.0)
    pipe = Pipeline([
        ("feats", FeatureUnion([
            ("mots", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, strip_accents="unicode")),
            ("car", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ])),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)),
    ])
    k = int(min(5, df.label.value_counts().min()))
    metrics = {}
    if k >= 2:
        cv = StratifiedKFold(k, shuffle=True, random_state=7)
        try:
            pred = cross_val_predict(pipe, df.texte, df.label, cv=cv, params={"clf__sample_weight": w})
        except TypeError:  # scikit-learn < 1.4
            pred = cross_val_predict(pipe, df.texte, df.label, cv=cv, fit_params={"clf__sample_weight": w})
        labels = sorted(df.label.unique())
        metrics = dict(accuracy=round(accuracy_score(df.label, pred), 3),
                       f1_macro=round(f1_score(df.label, pred, average="macro"), 3),
                       confusion=pd.DataFrame(confusion_matrix(df.label, pred, labels=labels),
                                              index=[MEASURE_LABELS.get(l, l) for l in labels],
                                              columns=[MEASURE_LABELS.get(l, l) for l in labels]),
                       report=pd.DataFrame(classification_report(df.label, pred, output_dict=True,
                                                                 zero_division=0)).T.round(3))
    pipe.fit(df.texte, df.label, clf__sample_weight=w)
    info = dict(date=datetime.now().strftime("%Y-%m-%d %H:%M"), n=len(df), classes=df.label.nunique(),
                n_valides=int((df.origine == "validé").sum()), **{k_: v for k_, v in metrics.items()
                                                                  if k_ in ("accuracy", "f1_macro")})
    _save("news_classifier", dict(model=pipe, info=info))
    metrics["info"] = info
    return metrics


def top_terms(n=12) -> pd.DataFrame:
    m = load_model("news_classifier")
    if not m:
        return pd.DataFrame()
    pipe = m["model"]
    vec = pipe.named_steps["feats"].transformer_list[0][1]
    nw = len(vec.get_feature_names_out())
    clf = pipe.named_steps["clf"]
    names = vec.get_feature_names_out()
    rows = []
    coefs = clf.coef_ if clf.coef_.shape[0] > 1 else np.vstack([-clf.coef_[0], clf.coef_[0]])
    for cls, coef in zip(clf.classes_, coefs):
        c = coef[:nw]
        for i in np.argsort(c)[::-1][:n]:
            rows.append(dict(classe=MEASURE_LABELS.get(cls, cls), terme=names[i], poids=round(float(c[i]), 3)))
    return pd.DataFrame(rows)


def predict_news(texts: list[str]) -> pd.DataFrame:
    m = load_model("news_classifier")
    if not m or not texts:
        return pd.DataFrame()
    pipe = m["model"]
    proba = pipe.predict_proba(texts)
    cls = pipe.classes_
    best = proba.argmax(1)
    return pd.DataFrame(dict(prediction=[cls[i] for i in best],
                             prediction_lib=[MEASURE_LABELS.get(cls[i], cls[i]) for i in best],
                             confiance=proba.max(1).round(3)))


def save_labels(rows: pd.DataFrame) -> dict:
    """rows : colonnes uid, label (clé de mesure)."""
    rows = rows[["uid", "label"]].copy()
    rows["valide_le"] = store.now()
    return store.append_rows("ml_labels", rows, source="validation manuelle")


# --------------------------------------------------------------------------- #
# 2. Segmentation des pays
# --------------------------------------------------------------------------- #
COUNTRY_FEATS = ["wgi_corruption", "wgi_efficacite_gouv", "wgi_stabilite", "wgi_qualite_regl", "wgi_etat_droit",
                 "wgi_voix_resp", "score_gafi", "score_regime", "score_sanctions"]


def cluster_countries(k: int = 4) -> pd.DataFrame:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler

    df = store.load("pays_risque")
    if df.empty:
        raise ValueError("Aucune donnée pays : cliquez sur « Enrichir le risque pays » dans le Centre de données.")
    feats = [c for c in COUNTRY_FEATS if c in df.columns]
    X = df[feats].apply(pd.to_numeric, errors="coerce")
    keep = X.notna().sum(axis=1) >= max(2, len(feats) // 2)
    df, X = df[keep].copy(), X[keep]
    if len(df) < k * 3:
        raise ValueError("Trop peu de pays renseignés pour la segmentation.")
    Xs = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X))
    km = KMeans(n_clusters=k, n_init=20, random_state=7).fit(Xs)
    df["score_risque"] = pd.to_numeric(df.score_risque, errors="coerce")
    df["cluster"] = km.labels_
    order = df.groupby("cluster").score_risque.mean().sort_values().index
    names = ["Profil 1 — robuste", "Profil 2 — intermédiaire", "Profil 3 — fragile", "Profil 4 — critique",
             "Profil 5 — extrême", "Profil 6"]
    df["segment"] = df.cluster.map({c: names[i] for i, c in enumerate(order)})
    xy = PCA(2, random_state=7).fit_transform(Xs)
    df["acp_x"], df["acp_y"] = xy[:, 0].round(3), xy[:, 1].round(3)
    _save("country_clusters", dict(model=km, feats=feats, date=store.now()))
    return df


# --------------------------------------------------------------------------- #
# 3. Anomalies sur les profils d'entités
# --------------------------------------------------------------------------- #
ENTITY_FEATS = ["score", "meilleur_score_sanctions", "nb_correspondances", "nb_presse_negative", "nb_presse_grave",
                "score_pays"]


def entity_anomalies(contamination: float = 0.1) -> pd.DataFrame:
    from sklearn.ensemble import IsolationForest
    df = store.load("entites_profils")
    if len(df) < 8:
        raise ValueError(f"{len(df)} profil(s) enregistré(s) : il en faut au moins 8. "
                         "Analysez des entités dans l'onglet Profil d'entité (ou en lot).")
    X = df[ENTITY_FEATS].apply(pd.to_numeric, errors="coerce").fillna(0)
    X["ppe"] = (df.ppe == "oui").astype(int)
    iso = IsolationForest(n_estimators=300, contamination=contamination, random_state=7).fit(X)
    df["anomalie"] = np.where(iso.predict(X) == -1, "atypique", "normal")
    df["score_anomalie"] = (-iso.score_samples(X)).round(3)
    _save("entity_iforest", dict(model=iso, date=store.now()))
    return df.sort_values("score_anomalie", ascending=False)


# --------------------------------------------------------------------------- #
# 4. Typologies des listes de sanctions
# --------------------------------------------------------------------------- #
def sanction_typologies(k: int = 8, max_rows: int = 40000) -> tuple[pd.DataFrame, pd.DataFrame]:
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from .sources import sanctions_consolidees

    sc = sanctions_consolidees()
    if len(sc) < 50:
        raise ValueError("Pas assez d'entrées de sanctions : enrichissez au moins une liste (OFAC, UE, ONU, UK…).")
    sc = sc.sample(min(len(sc), max_rows), random_state=7) if len(sc) > max_rows else sc
    txt = (sc.programme.fillna("") + " " + sc.type.fillna("") + " pays_" + sc.pays.fillna("").str.replace(" | ", " pays_")
           + " " + sc.remarques.fillna("").str[:200])
    vec = TfidfVectorizer(min_df=3, max_features=6000, ngram_range=(1, 2), strip_accents="unicode",
                          token_pattern=r"(?u)\b[\w-]{2,}\b")
    X = vec.fit_transform(txt)
    km = MiniBatchKMeans(n_clusters=k, n_init=5, random_state=7, batch_size=2048).fit(X)
    sc = sc.assign(typologie=km.labels_)
    terms = vec.get_feature_names_out()
    summ = []
    for c in range(k):
        top = [terms[i].replace("pays_", "🌐") for i in km.cluster_centers_[c].argsort()[::-1][:8]]
        g = sc[sc.typologie == c]
        summ.append(dict(typologie=c, effectif=len(g), mots_cles=", ".join(top),
                         type_dominant=g.type.mode().iloc[0] if len(g) else "",
                         liste_dominante=g.liste.mode().iloc[0] if len(g) else ""))
    _save("sanction_typologies", dict(model=km, vec=vec, date=store.now()))
    return sc, pd.DataFrame(summ).sort_values("effectif", ascending=False)


# --------------------------------------------------------------------------- #
# 5. Tendance mensuelle des inscriptions
# --------------------------------------------------------------------------- #
def designation_trend(months_ahead: int = 6, since: str = "2018-01-01") -> pd.DataFrame:
    from sklearn.linear_model import LinearRegression
    from .sources import sanctions_consolidees
    sc = sanctions_consolidees(actives_only=False)
    d = pd.to_datetime(sc.get("date_inscription", pd.Series(dtype=str)), errors="coerce")
    d = d.fillna(pd.to_datetime(sc.get("premiere_vue", pd.Series(dtype=str)), errors="coerce"))
    s = d[d >= since].dt.to_period("M").value_counts().sort_index()
    if len(s) < 6:
        return pd.DataFrame()
    s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"), fill_value=0)
    t = np.arange(len(s)).reshape(-1, 1)
    lr = LinearRegression().fit(t[-36:], s.values[-36:])
    fut = np.arange(len(s), len(s) + months_ahead).reshape(-1, 1)
    hist = pd.DataFrame(dict(mois=s.index.astype(str), inscriptions=s.values, type="observé"))
    prev = pd.DataFrame(dict(mois=pd.period_range(s.index.max() + 1, periods=months_ahead, freq="M").astype(str),
                             inscriptions=np.clip(lr.predict(fut), 0, None).round(0), type="projection"))
    return pd.concat([hist, prev], ignore_index=True)
