"""
cwp.data.notoriete — recherche de notoriété négative (adverse media) automatisée et analysée.

Pour chaque entité (jusqu'à 7 par lot) :
 1. combine le nom (expression exacte) avec des mots-clés négatifs (FR / EN / ES / créole), par groupes OR
    ou mot par mot (mode approfondi), et interroge :
      • Google Actualités (flux RSS publics — plusieurs dizaines de résultats par requête)
      • GDELT (presse mondiale, 65 langues)
      • facultatif : moteur web via API officielle (Google Programmable Search ou Brave Search) si une clé est
        configurée dans les secrets — 4 pages de 10 résultats par requête, comme une recherche Google manuelle ;
 2. lit, si demandé, le texte des articles les plus pertinents ;
 3. note chaque article (0–100) : présence du nom, gravité des mots-clés, proximité nom / mot-clé,
    titre vs corps, crédibilité du média, fraîcheur, contextes atténuants (victime, acquittement, homonymie) ;
 4. classe l'entité sur 5 niveaux de criticité et rédige une conclusion ;
 5. produit un PDF unique par entité (tous les articles pertinents, liens, résumés, méthode) et un Excel.
Tout est stocké dans data/notoriete_recherches.csv et data/notoriete_articles.csv.
"""
from __future__ import annotations

import html as _html
import io
import math
import re
import time
import unicodedata
from datetime import datetime
from urllib.parse import quote, quote_plus, urlparse

import pandas as pd

from . import store
from .sources import S, _uid

# --------------------------------------------------------------------------- #
# Mots-clés : (expression, poids de gravité 1–5, langue)
# --------------------------------------------------------------------------- #
KEYWORDS = [
    # français
    ("blanchiment", 5, "fr"), ("financement du terrorisme", 5, "fr"), ("terrorisme", 5, "fr"), ("gel des avoirs", 5, "fr"),
    ("sanctions", 4, "fr"), ("sanctionné", 4, "fr"), ("corruption", 4, "fr"), ("pot-de-vin", 4, "fr"), ("détournement", 4, "fr"),
    ("fraude", 4, "fr"), ("escroquerie", 4, "fr"), ("arnaque", 3, "fr"), ("condamné", 4, "fr"), ("condamnation", 4, "fr"),
    ("mis en examen", 4, "fr"), ("inculpé", 4, "fr"), ("arrêté", 3, "fr"), ("arrestation", 3, "fr"), ("enquête", 3, "fr"),
    ("perquisition", 3, "fr"), ("procès", 3, "fr"), ("amende", 3, "fr"), ("évasion fiscale", 4, "fr"), ("fraude fiscale", 4, "fr"),
    ("trafic", 4, "fr"), ("contrebande", 3, "fr"), ("extorsion", 4, "fr"), ("enlèvement", 4, "fr"), ("gang", 3, "fr"),
    ("abus de biens sociaux", 4, "fr"), ("plainte", 2, "fr"), ("scandale", 2, "fr"), ("liquidation judiciaire", 2, "fr"),
    # anglais
    ("money laundering", 5, "en"), ("terrorist financing", 5, "en"), ("asset freeze", 5, "en"), ("sanctioned", 4, "en"),
    ("OFAC", 4, "en"), ("corruption", 4, "en"), ("bribery", 4, "en"), ("embezzlement", 4, "en"), ("fraud", 4, "en"),
    ("scam", 3, "en"), ("Ponzi", 4, "en"), ("convicted", 4, "en"), ("indicted", 4, "en"), ("charged", 3, "en"),
    ("arrested", 3, "en"), ("investigation", 3, "en"), ("probe", 3, "en"), ("lawsuit", 2, "en"), ("fined", 3, "en"),
    ("tax evasion", 4, "en"), ("trafficking", 4, "en"), ("smuggling", 3, "en"), ("extortion", 4, "en"), ("kidnapping", 4, "en"),
    ("gang", 3, "en"), ("scandal", 2, "en"), ("bankruptcy", 2, "en"),
    # espagnol
    ("lavado de dinero", 5, "es"), ("corrupción", 4, "es"), ("fraude", 4, "es"), ("sancionado", 4, "es"),
    ("narcotráfico", 4, "es"), ("detenido", 3, "es"), ("condenado", 4, "es"),
    # créole haïtien
    ("kòripsyon", 4, "ht"), ("lajan sal", 5, "ht"), ("arete", 3, "ht"), ("gang", 3, "ht"),
]
LANGS = {"fr": ("fr", "FR", "FR:fr"), "en": ("en-US", "US", "US:en"), "es": ("es-419", "MX", "MX:es-419"), "ht": ("fr", "FR", "FR:fr")}
LANG_LABEL = {"fr": "Français", "en": "Anglais", "es": "Espagnol", "ht": "Créole haïtien"}

# contextes atténuants : l'entité est victime, blanchie, ou l'article dément
MITIGANTS = [(r"\bvictime[s]? d", -20, "victime"), (r"\bvictim[s]? of\b", -20, "victime"), (r"acquitt", -30, "acquittement"),
             (r"\brelax[ée]", -25, "relaxe"), (r"non-lieu", -30, "non-lieu"), (r"innocent", -20, "innocenté"),
             (r"cleared of", -30, "blanchi"), (r"dismiss(ed)? (the )?(case|charges)", -25, "classement"),
             (r"\bdément|\bdenies\b|\bdenied\b", -8, "démenti"), (r"\blutte contre (le |la |l')?(blanchiment|corruption|fraude|terroris)|\bfight(ing)? against\b|\bcombat(tre|ting)?\b", -25, "lutte contre (rôle positif)"),
             (r"\banti[- ]?(money[- ]laundering|blanchiment|corruption|fraude|fraud)\b|\bLCB-?FT\b|\bcompliance officer\b|\bresponsable conformit", -15, "fonction de conformité / prévention"),
             (r"\bnomm[ée]|\bappointed\b|\bprix\b|\baward\b|\bconférence\b|\bconference\b", -8, "contexte institutionnel")]

SEVERE = {"blanchiment", "money laundering", "lavado de dinero", "lajan sal", "terrorisme", "financement du terrorisme",
          "terrorist financing", "gel des avoirs", "asset freeze", "sanctions", "sanctionné", "sanctioned", "OFAC"}

CRED_HIGH = ["reuters", "bloomberg", "afp", "associated press", "apnews", "ft.com", "financial times", "lemonde", "le monde",
             "lesechos", "nytimes", "washingtonpost", "wsj", "bbc", "theguardian", "le figaro", "franceinfo", "rfi", "france24",
             "lenouvelliste", "le nouvelliste", "ayibopost", "haitilibre", "icihaiti", "loophaiti", "occrp", "icij", "insightcrime",
             "justice.gov", "treasury.gov", "europa.eu", "un.org", "gouv"]
CRED_LOW = ["blogspot", "wordpress", "medium.com", "facebook", "tiktok", "youtube", "x.com", "twitter", "reddit", "pinterest"]

LEVELS = [  # (seuil bas, libellé, couleur écran, couleur PDF, conclusion)
    (0, "1 — Aucune information négative", "#0ca30c", "#2E8B57", "Aucune information négative pertinente n'a été trouvée."),
    (15, "2 — Information négative faible", "#7cc242", "#6B9E2F", "Quelques mentions sans gravité ou peu liées à l'entité : pas d'impact attendu, à consigner."),
    (35, "3 — Information négative modérée", "#fab219", "#C99000", "Informations négatives à examiner : vérifier l'identité et les faits avant de conclure."),
    (55, "4 — Information négative élevée", "#ec835a", "#D0612F", "Informations négatives sérieuses et liées à l'entité : analyse approfondie et avis de la conformité requis."),
    (75, "5 — Information négative critique", "#d03b3b", "#B22222", "Informations graves et convergentes (sanctions, blanchiment, condamnations…) : escalade immédiate."),
]


def level(score: float) -> tuple:
    return [lv for lv in LEVELS if score >= lv[0]][-1]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# --------------------------------------------------------------------------- #
# Collecte
# --------------------------------------------------------------------------- #
def _gnews_url(q, lang):
    hl, gl, ceid = LANGS[lang]
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"


def _clean(t, n=600):
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    return re.sub(r"\s+", " ", t).strip()[:n]


def queries(name: str, langs: list[str], keywords=None, approfondi=False, group=6) -> list[tuple[str, str, list[str]]]:
    """(requête, langue, mots-clés couverts)"""
    kws = keywords or KEYWORDS
    out = []
    for lg in langs:
        kl = [k for k, _, l in kws if l == lg]
        chunks = [[k] for k in kl] if approfondi else [kl[i:i + group] for i in range(0, len(kl), group)]
        for ch in chunks:
            q = f'"{name}" (' + " OR ".join(f'"{k}"' if " " in k else k for k in ch) + ")"
            out.append((q, lg, ch))
    return out


STATS = {"ok": 0, "ko": 0}


def search_gnews(name, langs, keywords=None, approfondi=False, progress=None):
    import feedparser
    qs = queries(name, langs, keywords, approfondi)
    arts = []
    for i, (q, lg, ch) in enumerate(qs):
        try:
            rr = S.get(_gnews_url(q, lg), timeout=20)
            feed = feedparser.parse(rr.content) if rr.ok else None
            STATS["ok" if rr.ok else "ko"] += 1
        except Exception:
            feed = None
            STATS["ko"] += 1
        for e in (feed.entries if feed else [])[:100]:
            src = (e.get("source") or {}).get("title", "") if isinstance(e.get("source"), dict) else ""
            title = _clean(e.get("title"), 300)
            if src and title.endswith(" - " + src):
                title = title[: -(len(src) + 3)]
            ts = time.mktime(e.get("published_parsed")) if e.get("published_parsed") else 0
            arts.append(dict(titre=title, extrait=_clean(e.get("summary")), lien=e.get("link", ""), media=src,
                             date=datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "", langue=lg,
                             moteur="Google Actualités", requete=q))
        if progress:
            progress((i + 1) / len(qs))
        time.sleep(0.25)
    return arts


def search_gdelt(name, mois=36):
    from .sources import NEG_TERMS_EN, NEG_TERMS_FR
    arts = []
    for terms in (NEG_TERMS_EN, NEG_TERMS_FR):
        url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={quote(chr(34) + name + chr(34) + ' ' + terms)}"
               f"&mode=artlist&format=json&maxrecords=100&sort=datedesc&timespan={mois}months")
        try:
            r = S.get(url, timeout=40)
            js = r.json() if r.text.strip().startswith("{") else {}
        except Exception:
            js = {}
        for a in js.get("articles", []):
            sd = a.get("seendate", "")
            arts.append(dict(titre=a.get("title", ""), extrait="", lien=a.get("url", ""), media=a.get("domain", ""),
                             date=f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}" if len(sd) >= 8 else "", langue=a.get("language", "")[:2].lower(),
                             moteur="GDELT", requete=terms))
        time.sleep(5)
    return arts


def _secret(k):
    import os
    v = os.getenv(k)
    if v:
        return v
    try:
        import streamlit as st
        return st.secrets.get(k)
    except Exception:
        return None


def web_engine():
    if _secret("GOOGLE_CSE_KEY") and _secret("GOOGLE_CSE_CX"):
        return "Google Programmable Search"
    if _secret("BRAVE_API_KEY"):
        return "Brave Search"
    return None


def search_web(name, langs, keywords=None, pages=4):
    """Recherche web (4 pages × 10 résultats par requête) via une API officielle, si une clé est configurée."""
    eng = web_engine()
    if not eng:
        return []
    arts = []
    for q, lg, _ in queries(name, langs, keywords, approfondi=False, group=8):
        for p in range(pages):
            try:
                if eng.startswith("Google"):
                    r = S.get("https://www.googleapis.com/customsearch/v1", timeout=20, params=dict(
                        key=_secret("GOOGLE_CSE_KEY"), cx=_secret("GOOGLE_CSE_CX"), q=q, start=1 + 10 * p, num=10))
                    items = [(i.get("title"), i.get("snippet"), i.get("link"), i.get("displayLink")) for i in r.json().get("items", [])]
                else:
                    r = S.get("https://api.search.brave.com/res/v1/web/search", timeout=20, params=dict(q=q, offset=p, count=10),
                              headers={"X-Subscription-Token": _secret("BRAVE_API_KEY"), "Accept": "application/json"})
                    items = [(i.get("title"), i.get("description"), i.get("url"), urlparse(i.get("url", "")).netloc)
                             for i in r.json().get("web", {}).get("results", [])]
            except Exception:
                items = []
            if not items:
                break
            for t, sn, l, d in items:
                arts.append(dict(titre=_clean(t, 300), extrait=_clean(sn), lien=l, media=d, date="", langue=lg, moteur=eng, requete=q))
            time.sleep(0.4)
    return arts


def fetch_article(url: str) -> tuple[str, str]:
    """(url réelle, texte) — réutilise le lecteur d'articles de la veille réglementaire."""
    try:
        from cwp.services.regwatch import fetch_text, resolve_url
        real = resolve_url(url)
        return real, fetch_text(real, 20_000) or ""
    except Exception:
        return url, ""


# --------------------------------------------------------------------------- #
# Analyse
# --------------------------------------------------------------------------- #
def _sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", t or "") if 30 < len(s.strip()) < 500]


def name_presence(name, text):
    """1.0 si le nom complet figure, sinon part des éléments du nom présents (≥ 3 lettres)."""
    n, t = norm(name), norm(text)
    if not n:
        return 0.0
    if re.search(rf"\b{re.escape(n)}\b", t):
        return 1.0
    toks = [x for x in n.split() if len(x) >= 3]
    if not toks:
        return 0.0
    hits = sum(bool(re.search(rf"\b{re.escape(x)}\b", t)) for x in toks)
    return round(hits / len(toks) * (0.8 if len(toks) > 1 else 0.6), 2)


def score_article(a: dict, name: str, keywords=None) -> dict:
    kws = keywords or KEYWORDS
    title, body = a.get("titre", ""), " ".join(x for x in (a.get("extrait", ""), a.get("texte", "")) if x)
    full = f"{title} {body}"
    nt, nb = norm(title), norm(body)
    pres_t, pres = name_presence(name, title), name_presence(name, full)
    found, sev = {}, 0.0
    for k, w, _ in kws:
        nk = norm(k)
        if not nk:
            continue
        in_t = bool(re.search(rf"\b{re.escape(nk)}", nt))
        cnt_b = len(re.findall(rf"\b{re.escape(nk)}", nb))
        if in_t or cnt_b:
            found[k] = max(found.get(k, 0), w)
            sev += w * (2.0 if in_t else 1.0) + min(cnt_b, 5) * w * 0.25
    # proximité : nom et mot-clé dans la même phrase
    prox, best_sent = 0, []
    nn = norm(name)
    toks = [x for x in nn.split() if len(x) >= 3]
    sents = _sentences(a.get("texte", "")) + _sentences(a.get("extrait", ""))
    for s in sents + ([title] if title else []):
        ns = norm(s)
        has_name = re.search(rf"\b{re.escape(nn)}\b", ns) or (toks and all(re.search(rf"\b{re.escape(x)}\b", ns) for x in toks))
        ks = [k for k in found if re.search(rf"\b{re.escape(norm(k))}", ns)]
        if has_name and ks:
            prox += 1
            if s is not title and norm(s) != nt and s not in best_sent:
                best_sent.append(s)
    kw_score = min(55.0, sev * 2.2)
    base = kw_score * (0.25 + 0.75 * pres) + min(prox, 3) * 5 + (8 if pres_t >= 1 and found else 0)
    if set(found) & SEVERE and pres >= 0.8:
        base += 8
    m = (a.get("media", "") + " " + a.get("lien", "")).lower()
    cred = 6 if any(x in m for x in CRED_HIGH) else -6 if any(x in m for x in CRED_LOW) else 0
    rec = 0
    if a.get("date"):
        try:
            age = (datetime.now() - datetime.strptime(a["date"][:10], "%Y-%m-%d")).days / 365
            rec = 6 if age < 1 else 3 if age < 3 else 0 if age < 6 else -4
        except ValueError:
            pass
    mit, mit_l = 0, []
    for rx, pts, lab in MITIGANTS:
        if re.search(rx, full, re.I):
            mit += pts; mit_l.append(lab)
    if pres < 0.5:
        mit -= 10; mit_l.append("nom incomplet (homonymie possible)")
    score = max(0.0, min(100.0, base + cred + rec + max(mit, -40)))
    if not found:
        score = min(score, 8)
    lv = level(score)
    return {**a, "score": round(score, 1), "niveau": lv[1], "couleur": lv[2], "mots_cles": ", ".join(sorted(found, key=lambda k: -found[k])),
            "gravite_max": max(found.values()) if found else 0, "presence_nom": pres, "proximite": prox,
            "attenuants": ", ".join(dict.fromkeys(mit_l)), "credibilite": "élevée" if cred > 0 else "faible" if cred < 0 else "standard",
            "phrases_cles": " ".join(best_sent[:3])[:900]}


def summarize(a: dict, name: str) -> str:
    """Résumé extractif : phrases citant l'entité et un mot-clé, sinon phrases les plus chargées ; repli sur l'extrait."""
    if a.get("phrases_cles"):
        return a["phrases_cles"][:500]
    sents = _sentences(a.get("texte", ""))
    if sents:
        kw = [norm(k) for k, _, _ in KEYWORDS]
        ranked = sorted(sents, key=lambda s: -(sum(k in norm(s) for k in kw) * 2 + (norm(name) in norm(s)) * 3))
        return " ".join(ranked[:2])[:500]
    ex = a.get("extrait", "")
    if ex and norm(ex) != norm(a.get("titre", "")) and not norm(a.get("titre", "")).startswith(norm(ex)[:60]):
        return ex[:500]
    return "Seul le titre est disponible : ouvrir l'article pour vérifier les faits."


def llm_summaries(arts: list[dict], name: str) -> dict:
    """Résumés par IA (facultatif, si une clé est configurée pour la veille réglementaire)."""
    try:
        import streamlit as st
        from cwp.services.regwatch import llm_provider
        secrets = st.secrets
        prov = llm_provider(secrets)
    except Exception:
        return {}
    if not prov or not arts:
        return {}
    import json
    import requests
    items = "\n".join(f"[{i}] {a['titre']} — {a.get('media', '')} — {(a.get('texte') or a.get('extrait', ''))[:1500]}" for i, a in enumerate(arts))
    prompt = (f"Tu es analyste conformité. Pour chaque article ci-dessous, écris en français un résumé factuel de 2 phrases maximum "
              f"sur ce qu'il dit de « {name} » (faits reprochés, autorité, date, statut de la procédure). Si l'article ne concerne pas "
              f"vraiment cette entité, dis-le. Réponds uniquement en JSON : {{\"0\": \"résumé\", \"1\": \"…\"}}.\n\n{items}")
    try:
        if prov == "Claude":
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
                "x-api-key": secrets["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": secrets.get("CWP_LLM_MODEL", "claude-haiku-5-5"), "max_tokens": 3000,
                      "messages": [{"role": "user", "content": prompt}]})
            txt = "".join(b.get("text", "") for b in r.json().get("content", []))
        elif prov == "Mistral":
            r = requests.post("https://api.mistral.ai/v1/chat/completions", timeout=120,
                              headers={"Authorization": f"Bearer {secrets['MISTRAL_API_KEY']}"},
                              json={"model": secrets.get("CWP_LLM_MODEL", "mistral-small-latest"),
                                    "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]})
            txt = r.json()["choices"][0]["message"]["content"]
        else:
            r = requests.post(secrets["OLLAMA_URL"].rstrip("/") + "/api/generate", timeout=240,
                              json={"model": secrets.get("CWP_LLM_MODEL", "mistral"), "prompt": prompt, "format": "json", "stream": False})
            txt = r.json().get("response", "")
        m = re.search(r"\{.*\}", txt, re.S)
        return {int(k): v for k, v in json.loads(m.group(0)).items()} if m else {}
    except Exception:
        return {}


def entity_score(arts: pd.DataFrame) -> float:
    """Score entité : article le plus grave + convergence (nombre d'articles pertinents, médias distincts)."""
    if arts.empty:
        return 0.0
    s = arts.score.sort_values(ascending=False).values
    pert = arts[arts.score >= 35]
    conv = min(15, 3 * max(len(pert) - 1, 0)) + min(10, 2 * max(pert.media.nunique() - 1, 0))
    return round(min(100.0, s[0] * 0.8 + (s[1] * 0.1 if len(s) > 1 else 0) + conv), 1)


def merge_languages(arts: list[dict]) -> list[dict]:
    """Un même article publié en français et en anglais (ou repris par plusieurs médias) n'est gardé qu'une fois :
    sinon il serait compté deux fois dans le score de l'entité. La version française est privilégiée."""
    from cwp.core.dedup import merge
    for a in arts:
        try:
            a["ts"] = datetime.strptime(a.get("date", "")[:10], "%Y-%m-%d").timestamp() if a.get("date") else 0
        except ValueError:
            a["ts"] = 0
        a["lang"] = a.get("langue", "")
        a["link"] = a.get("lien", "")
    out = merge(arts, prefer="fr", text_key="titre")
    for a in out:
        vs = a.pop("versions", [])
        a["autres_versions"] = " | ".join(f"{v['lang'] or '?'}: {v['link']}" for v in vs)
        a["nb_versions"] = len(vs) + 1
        for k in ("langs", "n_media", "ts", "lang", "link"):
            a.pop(k, None)
    return out


def run(name: str, type_="Entité", pays="", langs=("fr", "en"), keywords=None, approfondi=False, lire=True, nb_lire=15,
        gdelt=True, web=True, ia=False, progress=None) -> dict:
    t0 = time.time()
    STATS.update(ok=0, ko=0)
    arts = search_gnews(name, list(langs), keywords, approfondi, progress=lambda f: progress and progress(f * 0.5, "Google Actualités"))
    if web and web_engine():
        if progress: progress(0.55, web_engine())
        arts += search_web(name, list(langs), keywords)
    if gdelt:
        if progress: progress(0.6, "GDELT")
        arts += search_gdelt(name)
    # déduplication (lien, puis titre normalisé)
    seen, uniq = set(), []
    for a in arts:
        k = norm(a["titre"])[:120] or a["lien"]
        if k in seen or not a["lien"]:
            continue
        seen.add(k); uniq.append(a)
    uniq = merge_languages(uniq)
    scored = [score_article(a, name, keywords) for a in uniq]
    scored.sort(key=lambda a: -a["score"])
    if lire:
        cand = [a for a in scored if a["score"] >= 15][:nb_lire]
        for i, a in enumerate(cand):
            if progress: progress(0.65 + 0.3 * (i + 1) / max(len(cand), 1), f"Lecture des articles ({i + 1}/{len(cand)})")
            real, txt = fetch_article(a["lien"])
            if txt:
                a["lien"], a["texte"] = real, txt
                a.update(score_article(a, name, keywords))
        scored.sort(key=lambda a: -a["score"])
    try:
        from cwp.services.regwatch import resolve_url
        for a in scored:
            if a["score"] >= 15 and "news.google." in a["lien"]:
                a["lien"] = resolve_url(a["lien"])
    except Exception:
        pass
    for a in scored:
        a["resume"] = summarize(a, name)
    if ia:
        top = [a for a in scored if a["score"] >= 35][:12]
        res = llm_summaries(top, name)
        for i, a in enumerate(top):
            if res.get(i):
                a["resume"], a["resume_ia"] = res[i], "oui"
    df = pd.DataFrame(scored)
    sc = entity_score(df)
    lv = level(sc)
    pert = df[df.score >= 35] if not df.empty else df
    res = dict(nom=name, type=type_, pays=pays, date=datetime.now().strftime("%Y-%m-%d %H:%M"), score=sc, niveau=lv[1],
               couleur=lv[2], couleur_pdf=lv[3], conclusion=lv[4], articles=df, nb_resultats=len(df),
               nb_pertinents=len(pert), langues=list(langs), approfondi=approfondi, duree_s=round(time.time() - t0),
               moteurs=sorted(set(df.moteur)) if not df.empty else [], cles=len(keywords or KEYWORDS))
    if STATS["ok"] == 0 and df.empty:
        res.update(niveau="Recherche impossible", couleur="#8aa4ba", couleur_pdf="#7A7A7A",
                   conclusion="Les moteurs de recherche n'ont pas répondu : aucune conclusion ne peut être tirée. Relancer la recherche.")
    res["requetes_ok"], res["requetes_ko"] = STATS["ok"], STATS["ko"]
    res["synthese"] = _synthese(res)
    _save(res)
    if progress: progress(1.0, "Terminé")
    return res


def _synthese(r):
    df = r["articles"]
    if df.empty:
        if r.get("requetes_ok", 1) == 0:
            return r["conclusion"]
        return "Aucun résultat n'a été retourné par les moteurs interrogés pour les mots-clés négatifs. " + r["conclusion"]
    pert = df[df.score >= 35]
    kw = pd.Series([k.strip() for x in pert.mots_cles for k in str(x).split(",") if k.strip()]).value_counts().head(5)
    txt = (f"{r['nb_resultats']} résultat(s) analysé(s), dont {len(pert)} pertinent(s) (score ≥ 35) provenant de "
           f"{pert.media.nunique() if len(pert) else 0} média(s).")
    if len(pert):
        txt += f" Thèmes dominants : {', '.join(kw.index)}." if len(kw) else ""
        d = pert.date[pert.date != ""]
        if len(d):
            txt += f" Période couverte : {d.min()} → {d.max()}."
        att = pert[pert.attenuants != ""]
        if len(att):
            txt += f" {len(att)} article(s) comportent un contexte atténuant (victime, acquittement, homonymie possible…)."
    return txt + " " + r["conclusion"]


def _save(r):
    rid = _uid(r["nom"], r["date"], time.time())
    store.append_rows("notoriete_recherches", [dict(uid=rid, nom=r["nom"], type=r["type"], pays=r["pays"], date=r["date"],
                                                    score=r["score"], niveau=r["niveau"], nb_resultats=r["nb_resultats"],
                                                    nb_pertinents=r["nb_pertinents"], synthese=r["synthese"])], source="CWP notoriété")
    df = r["articles"]
    if not df.empty:
        keep = ["titre", "media", "date", "langue", "moteur", "lien", "score", "niveau", "mots_cles", "presence_nom", "attenuants",
                "resume", "nb_versions", "autres_versions"]
        out = df[[c for c in keep if c in df]].copy()
        out.insert(0, "entite", r["nom"]); out.insert(1, "recherche", rid)
        out["uid"] = [_uid(r["nom"], l) for l in out.lien]
        store.append_rows("notoriete_articles", out, source="CWP notoriété")


# --------------------------------------------------------------------------- #
# PDF : un seul fichier par entité
# --------------------------------------------------------------------------- #
def entity_pdf(r: dict, seuil: float = 15) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle
    from cwp.exports import common as X

    W = X.CONTENT_W
    s = X.styles()
    col = colors.HexColor(r["couleur_pdf"])
    story = [X.header_card("Recherche de notoriété négative · adverse media", r["nom"],
                           f"{r['type']}{' · ' + r['pays'] if r['pays'] else ''} · {r['date']} · {r['nb_resultats']} résultat(s) · "
                           f"{r['nb_pertinents']} pertinent(s)", W), Spacer(1, 8)]
    big = X.S("big", 30, X.FONT_B, col, leading=32)
    card = Table([[Paragraph(f"{r['score']:.0f}<font size=11 color='#7A7A7A'> / 100</font>", big),
                   [Paragraph(X.esc(r["niveau"].upper()), X.S("lv", 12, X.FONT_B, col, leading=15)),
                    Paragraph(X.esc(r["conclusion"]), s["body"])]]], colWidths=[W * 0.28, W * 0.72])
    card.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, X.GOLD_LIGHT), ("BACKGROUND", (0, 0), (-1, -1), X.CREAM),
                              ("LINEBEFORE", (0, 0), (0, -1), 5, col), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story += [card, Spacer(1, 8), X.section_title("Synthèse", W), Spacer(1, 3), Paragraph(X.esc(r["synthese"]), s["body"]), Spacer(1, 8)]
    # échelle des niveaux
    sc_rows = [[Paragraph("", s["small"]), Paragraph(X.esc(lv[1]), s["small"]), Paragraph(f"≥ {lv[0]}", s["small"]),
                Paragraph(X.esc(lv[4]), s["small_grey"])] for lv in LEVELS]
    t = Table(sc_rows, colWidths=[5 * mm, W * 0.34, 14 * mm, W - 5 * mm - W * 0.34 - 14 * mm])
    st_ = [("LINEBELOW", (0, 0), (-1, -1), 0.25, X.LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i, lv in enumerate(LEVELS):
        st_.append(("BACKGROUND", (0, i), (0, i), colors.HexColor(lv[3])))
        if lv[1] == r["niveau"]:
            st_.append(("BACKGROUND", (1, i), (-1, i), X.CREAM))
    t.setStyle(TableStyle(st_))
    story += [KeepTogether([X.section_title("Échelle de criticité", W), Spacer(1, 3), t]), Spacer(1, 10)]
    df = r["articles"]
    pert = df[df.score >= seuil] if not df.empty else df
    story += [X.section_title(f"Articles pertinents ({len(pert)}) — classés par score", W), Spacer(1, 4)]
    if pert.empty:
        story.append(Paragraph("Aucun article au-dessus du seuil de pertinence.", s["body"]))
    for _, a in pert.iterrows():
        c = colors.HexColor(level(a.score)[3])
        link = X.esc(a.lien)
        head = Paragraph(f"<b>{X.esc(a.titre)}</b>", X.S("at", 9.6, X.FONT_B, X.NAVY, leading=12.5))
        meta = Paragraph(X.esc(f"{a.media or '—'} · {a.date or 'date inconnue'} · {LANG_LABEL.get(a.langue, a.langue)} · {a.moteur} · "
                               f"score {a.score:.0f} · {a.niveau}"), s["small_grey"])
        kw = Paragraph(X.esc(f"Mots-clés : {a.mots_cles or '—'}" + (f" · Atténuants : {a.attenuants}" if a.attenuants else "")), s["small"])
        res = Paragraph(X.esc(a.resume), s["body"])
        lk = Paragraph(f'<link href="{link}" color="#1a4e8a">{X.esc(a.lien[:110])}</link>', s["small"])
        box = Table([["", [head, meta, Spacer(1, 2), res, Spacer(1, 2), kw, lk]]], colWidths=[3 * mm, W - 3 * mm])
        box.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), c), ("LINEBELOW", (0, 0), (-1, -1), 0.3, X.LINE),
                                 ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 8),
                                 ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [KeepTogether([box]), Spacer(1, 3)]
    rest = df[df.score < seuil] if not df.empty else df
    if len(rest):
        story += [Spacer(1, 8), X.section_title(f"Autres résultats écartés ({len(rest)}) — titres seulement", W), Spacer(1, 3)]
        story += [Paragraph(X.esc(f"• {a.titre} — {a.media} ({a.score:.0f})"), s["small_grey"]) for _, a in rest.head(60).iterrows()]
    story += [Spacer(1, 10), X.section_title("Méthode", W), Spacer(1, 3), Paragraph(X.esc(
        f"Moteurs : {', '.join(r['moteurs']) or '—'}. Langues : {', '.join(LANG_LABEL.get(l, l) for l in r['langues'])}. "
        f"{r['cles']} mots-clés négatifs combinés au nom exact ({'un par requête' if r['approfondi'] else 'par groupes'}). "
        "Score article (0–100) : gravité et position des mots-clés (titre ×2), présence du nom complet, nom et mot-clé dans la même "
        "phrase, crédibilité du média, fraîcheur, contextes atténuants (victime, acquittement, homonymie). Score entité : article le plus "
        "grave + convergence des sources. Résultat indicatif : l'analyste doit lire les articles et confirmer l'identité."), s["small"]),
        Spacer(1, 8), X.footer_line("Recherche de notoriété négative", W)]
    return X.build_pdf(story, title=f"CWP – Notoriété {r['nom']}")


def batch_zip(results: list[dict]) -> bytes:
    import zipfile
    from cwp.exports.common import slug
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for r in results:
            z.writestr(f"notoriete_{slug(r['nom'])}.pdf", entity_pdf(r))
    return buf.getvalue()
