"""
regwatch.py — Moteur de veille réglementaire de CWP.

1. Collecte les publications des régulateurs et institutions de référence
   (ACPR, TRACFIN, AMF, DG Trésor, Journal officiel, AMLA, EBA, ESMA, BCE, UE, GAFI, OFAC, FinCEN…)
   via leurs flux RSS officiels quand ils existent et via Google News filtré sur leur site.
2. Classe chaque publication (texte législatif, orientations, consultation, sanction, rapport…).
3. Transforme une publication en fiche « Regulatory Flash » :
   - par IA si une clé est configurée dans .streamlit/secrets.toml
     (ANTHROPIC_API_KEY, MISTRAL_API_KEY ou OLLAMA_URL) ;
   - sinon par extraction automatique (sans IA) à partir du texte de la page.

Aucune dépendance à Streamlit ici : le cache est géré dans cwp/ui/pages/regulatory_flash.py.
"""
from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import feedparser
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; CWP-Compliance-Watch/1.0)"}


def gnews(q: str, lang: str = "fr") -> str:
    fr = lang == "fr"
    return (f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={lang}"
            f"&gl={'FR' if fr else 'US'}&ceid={'FR:fr' if fr else 'US:en'}")


# --------------------------------------------------------------------------- #
# Sources (ajoutez / retirez librement des lignes)
#   label    : nom affiché        juridiction : « Pays / source » de la fiche
#   cible    : cible par défaut   rss : flux officiels      gnews : requêtes Google News
#   filtre   : True = on ne garde que les publications liées à la conformité
# --------------------------------------------------------------------------- #
SOURCES = {
    "ACPR": dict(juridiction="France — ACPR (Banque de France)", cible="Banques, assurances, PSP / EME",
                 rss=[], filtre=False,
                 gnews=[gnews("site:acpr.banque-france.fr"),
                        gnews('ACPR "Autorité de contrôle prudentiel" "lignes directrices" OR recommandation '
                              'OR instruction OR notice OR "position"')]),
    "TRACFIN": dict(juridiction="France — TRACFIN", cible="Ensemble des assujettis LCB-FT",
                    rss=[], filtre=False,
                    gnews=[gnews("site:economie.gouv.fr tracfin"),
                           gnews('Tracfin "lignes directrices" OR typologies OR rapport OR "déclaration de soupçon"')]),
    "AMF": dict(juridiction="France — AMF", cible="SGP, PSI, PSAN / CASP, émetteurs",
                rss=[], filtre=False,
                gnews=[gnews("site:amf-france.org"),
                       gnews('AMF "position-recommandation" OR "guide" OR consultation OR "règlement général" OR MiCA')]),
    "DG Trésor": dict(juridiction="France — DG Trésor", cible="Ensemble des assujettis",
                      rss=[], filtre=True,
                      gnews=[gnews('site:tresor.economie.gouv.fr "lignes directrices" OR LCB-FT OR réglementation '
                                   'OR "mesures restrictives"')]),
    "Journal officiel": dict(juridiction="France — Journal officiel / Légifrance", cible="Ensemble des assujettis",
                             rss=[], filtre=True,
                             gnews=[gnews('"Journal officiel" décret OR arrêté OR ordonnance blanchiment OR '
                                          '"financement du terrorisme" OR "code monétaire et financier"')]),
    "AFA": dict(juridiction="France — Agence française anticorruption", cible="Grandes entreprises, EPIC, banques",
                rss=[], filtre=False,
                gnews=[gnews('"Agence française anticorruption" recommandations OR contrôle OR guide')]),
    "AMLA": dict(juridiction="Union européenne — AMLA", cible="Assujettis LCB-FT de l'UE",
                 rss=[], filtre=False,
                 gnews=[gnews("site:amla.europa.eu", "en"),
                        gnews('AMLA "Anti-Money Laundering Authority" consultation OR standards OR guidelines', "en")]),
    "EBA": dict(juridiction="Union européenne — EBA", cible="Banques, PSP / EME, CASP",
                rss=["https://www.eba.europa.eu/news-press/news/rss.xml"], filtre=True,
                gnews=[gnews("site:eba.europa.eu", "en")]),
    "ESMA": dict(juridiction="Union européenne — ESMA", cible="SGP, PSI, CASP, infrastructures",
                 rss=[], filtre=True,
                 gnews=[gnews("site:esma.europa.eu", "en")]),
    "BCE / MSU": dict(juridiction="Union européenne — BCE / supervision bancaire", cible="Banques importantes (SSM)",
                      rss=["https://www.ecb.europa.eu/rss/press.html"], filtre=True,
                      gnews=[gnews("site:bankingsupervision.europa.eu", "en")]),
    "UE (Conseil / Commission)": dict(juridiction="Union européenne — Conseil / Commission",
                                      cible="Ensemble des opérateurs de l'UE", rss=[], filtre=True,
                                      gnews=[gnews('site:consilium.europa.eu "money laundering" OR regulation OR directive', "en"),
                                             gnews('"Official Journal" regulation anti-money laundering OR '
                                                   'sanctions OR MiCA OR DORA', "en")]),
    "GAFI / FATF": dict(juridiction="International — GAFI / FATF", cible="Juridictions et assujettis LCB-FT",
                        rss=[], filtre=False,
                        gnews=[gnews("site:fatf-gafi.org", "en"),
                               gnews("GAFI plénière OR recommandations OR \"liste grise\"")]),
    "OFAC (US)": dict(juridiction="États-Unis — OFAC (Trésor US)", cible="Opérateurs en USD ou liés aux US",
                      rss=[], filtre=True,
                      gnews=[gnews('site:ofac.treasury.gov guidance OR regulations OR "frequently asked questions" '
                                   'OR "compliance framework"', "en")]),
    "FinCEN (US)": dict(juridiction="États-Unis — FinCEN", cible="Institutions financières US",
                        rss=[], filtre=False,
                        gnews=[gnews('site:fincen.gov rule OR guidance OR advisory OR "final rule" OR "proposed rule"', "en")]),
    "Comité de Bâle (BIS)": dict(juridiction="International — Comité de Bâle (BIS)", cible="Banques",
                                 rss=[], filtre=True,
                                 gnews=[gnews("site:bis.org \"Basel Committee\"", "en")]),
}

# --------------------------------------------------------------------------- #
# Lexiques
# --------------------------------------------------------------------------- #
RELEVANT = re.compile(
    r"blanchi|lcb|financement du terrorisme|money laundering|\baml\b|\bcft\b|kyc|sanction|gel des avoirs|"
    r"asset freeze|embargo|conformit|compliance|amla|mica|dora|crypto|paiement|payment|\bdsp\b|\bpsd|"
    r"fraud|travel rule|vigilance|bénéficiaire effectif|beneficial owner|tracfin|orientations|guidelines|"
    r"consultation|règlement|regulation|directive|décret|arrêté|instruction|recommandation|supervis|"
    r"contrôle interne|internal control|risk|risque|prudenti|capital|solvab|liquidit|governance|gouvernance|"
    r"anticorruption|corruption|\bppe\b|\bpep\b|mesures restrictives|restrictive measures|advisory|rule\b",
    re.I)

KINDS = [  # (type, motif) — premier qui correspond
    ("Consultation", r"consultation|consults|call for evidence|appel à commentaires"),
    ("Orientations / recommandations", r"orientations|guidelines|lignes directrices|guidance|recommandation|"
                                       r"position|notice|\bq&a\b|questions-réponses|standards?\b|\brts\b|\bits\b"),
    ("Texte législatif", r"règlement|directive|regulation|décret|arrêté|ordonnance|\bloi\b|journal officiel|"
                         r"official journal|act\b|final rule|proposed rule|interim rule"),
    ("Rapport / étude", r"rapport|report|étude|survey|typolog|analyse|review|evaluation|évaluation"),
]

# Actualités écartées : amendes, décisions de sanction, désignations, gels individuels, paquets de sanctions.
# Regulatory Flash ne retient que les textes et la doctrine (le Dashboard couvre ces actualités).
NEWS_EXCLUDE = re.compile(
    r"commission des sanctions|prononc\w* (?:un |une )?(?:blâme|amende|sanction|avertissement)|amende de|"
    r"\bblâme\b|condamn|\bfine[sd]?\b|\bfining\b|penalty of|civil (?:money )?penalt|settle(?:s|d|ment)|"
    r"enforcement action|consent order|cease and desist|"
    r"designat(?:es|ed|ion)|désign\w* (?:par|comme)|sanctions? (?:on|against|contre)|treasury sanctions|"
    r"impos\w* (?:des |new |de nouvelles )?sanctions|nouvelles sanctions|new sanctions|"
    r"paquet de sanctions|sanctions package|gel des avoirs de|asset freeze on|assets? frozen|"
    r"adds? .{0,40}(?:sdn|entity list)|sdn list|delist|removes? .{0,30}from .{0,20}list",
    re.I)


def is_news(text: str) -> bool:
    return bool(NEWS_EXCLUDE.search(text or ""))


MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
             "octobre", "novembre", "décembre"]
MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december"]

CIBLES = [
    ("Banques", r"banque|établissement de crédit|credit institution|\bbanks?\b|banking"),
    ("PSP / EME", r"prestataire de services de paiement|établissement de paiement|monnaie électronique|"
                  r"payment (service|institution)|e-money|\bpsp\b|\bemi\b"),
    ("PSAN / CASP", r"\bpsan\b|crypto|\bmica\b|\bcasp\b|actifs numériques|virtual asset"),
    ("Assurances", r"assur|insurance|insurer|mutuelle"),
    ("SGP / gestion d'actifs", r"société de gestion|asset manag|\bopcvm\b|\bfia\b|\bsgp\b|fund manag"),
    ("Entreprises d'investissement", r"entreprise d'investissement|investment firm|\bpsi\b"),
    ("Professions non financières", r"notaire|avocat|agent immobilier|commissaire aux comptes|casino|dnfbp|"
                                    r"real estate|lawyer|accountant"),
]

DOMAINS = {
    "KYC / KYB & UBO": (r"kyc|kyb|connaissance (du|de la) client|vigilance|bénéficiaire effectif|beneficial owner|"
                        r"due diligence|identification|\bppe\b|\bpep\b|entrée en relation|onboarding|"
                        r"customer|clientèle"),
    "Filtrage & transactions": (r"sanction|gel des avoirs|asset freeze|filtrage|screening|transaction|virement|"
                                r"transfer|travel rule|surveillance|monitoring|alerte|embargo|paiement|payment"),
    "Gouvernance & reporting": (r"déclaration|reporting|tracfin|audit|contrôle interne|internal control|"
                                r"gouvernance|governance|dispositif|procédure|formation|training|cartographie|"
                                r"risk assessment|évaluation des risques|soupçon|suspicious|notification"),
}
DOMAIN_ACTIONS = {
    "KYC / KYB & UBO": "Revoir les procédures d'entrée en relation et de mise à jour des dossiers",
    "Filtrage & transactions": "Vérifier le paramétrage du filtrage et des scénarios de surveillance",
    "Gouvernance & reporting": "Mettre à jour procédures, contrôles et circuits de déclaration",
}

PURPOSE = re.compile(r"vise|objectif|afin de|pour renforcer|a pour but|aims?|purpose|seeks?|to ensure|"
                     r"introdu|établit|fixe|precis|précise|clarif|harmoni|renforc|strengthen", re.I)
OBLIGATION = re.compile(r"doivent|devront|obligation|exige|requiert|tenus? de|must|shall|required?|"
                        r"requirement|expects?|attendu|mettre en (place|œuvre)", re.I)
CONSTRAINT = re.compile(r"sanction|amende|blâme|pénalit|retrait d'agrément|interdiction|\bfine|penalt|"
                        r"enforcement|délai|deadline|date limite|avant le|by \d|au plus tard|"
                        r"entr\w* en (vigueur|application)|apply from|enter into force", re.I)


# --------------------------------------------------------------------------- #
# Utilitaires texte
# --------------------------------------------------------------------------- #
def clean(t: str, n: int | None = None) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t if n is None or len(t) <= n else t[: n - 1].rstrip() + "…"


def strip_publisher(title: str) -> tuple[str, str]:
    """Google News : « Titre - Éditeur » → (titre, éditeur)."""
    m = re.match(r"^(.*\S)\s+[-–—]\s+([^-–—]{2,60})$", title or "")
    return (m.group(1), m.group(2).strip()) if m else (title, "")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«\"(])", text or "")
            if 45 < len(s.strip()) < 420 and not NOISE.search(s)]


def short(s: str, n: int = 280) -> str:
    return clean(s, n)


def month_year(ts: float) -> str:
    if not ts:
        return "Non précisée"
    d = datetime.fromtimestamp(ts)
    return f"{MONTHS_FR[d.month - 1].capitalize()} {d.year}"


# --------------------------------------------------------------------------- #
# Collecte
# --------------------------------------------------------------------------- #
def _parse(url: str):
    """Télécharge un flux (avec un User-Agent navigateur) puis le parse."""
    r = requests.get(url, headers=UA, timeout=15)
    r.raise_for_status()
    return feedparser.parse(r.content)


def classify(text: str) -> str:
    for kind, pat in KINDS:
        if re.search(pat, text, re.I):
            return kind
    return "Communiqué / actualité"


def fetch_publications(days: int = 30, sources: list[str] | None = None,
                       per_feed: int = 25) -> tuple[list[dict], list[dict]]:
    """Renvoie (publications, état des sources). Les flux sont interrogés en parallèle."""
    from concurrent.futures import ThreadPoolExecutor

    cutoff = time.time() - days * 86400
    names = [n for n in SOURCES if not sources or n in sources]
    jobs = [(n, k, u) for n in names
            for k, u in [("Flux officiel", u) for u in SOURCES[n]["rss"]] + [("Google News", u) for u in SOURCES[n]["gnews"]]]

    def _get(url):
        try:
            feed = _parse(url)
            if feed.bozo and not feed.entries:
                raise ValueError("flux vide ou illisible")
            return feed, None
        except Exception as e:  # noqa: BLE001
            return None, type(e).__name__

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda j: _get(j[2]), jobs))

    items, status, seen = [], [], set()
    for name in names:
        cfg = SOURCES[name]
        n_ok, n_items, errors = 0, 0, []
        for (n, kind_url, url), (feed, err) in zip(jobs, results):
            if n != name:
                continue
            if err:
                errors.append(f"{kind_url} : {err}")
                continue
            n_ok += 1
            for e in feed.entries[:per_feed]:
                link = e.get("link") or ""
                raw_title = clean(e.get("title"), 300)
                title, publisher = strip_publisher(raw_title) if "news.google." in url else (raw_title, "")
                key = re.sub(r"\W+", "", title.lower())[:90]
                if not link or not title or key in seen:
                    continue
                pp = e.get("published_parsed") or e.get("updated_parsed")
                ts = time.mktime(pp) if pp else 0
                if ts and ts < cutoff:
                    continue
                desc = clean(e.get("summary") or e.get("description"), 1200)
                if desc.startswith(title[:40]):  # Google News répète souvent le titre
                    desc = ""
                blob = f"{title} {desc}"
                if is_news(blob):  # amendes, désignations… = actualités, pas de la réglementation
                    continue
                if cfg.get("filtre") and not RELEVANT.search(blob):
                    continue
                seen.add(key)
                n_items += 1
                src = e.get("source")
                if not publisher and isinstance(src, dict):
                    publisher = src.get("title", "")
                items.append(dict(
                    source=name, juridiction=cfg["juridiction"], cible_defaut=cfg["cible"],
                    title=title, desc=desc, link=link, ts=ts, publisher=publisher,
                    origin=kind_url, kind=classify(blob),
                    relevant=bool(RELEVANT.search(blob)),
                ))
        status.append(dict(Source=name, Flux_OK=f"{n_ok}/{len(cfg['rss']) + len(cfg['gnews'])}",
                           Publications=n_items, Erreurs=" ; ".join(errors) or "—"))
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items, status


def resolve_url(url: str) -> str:
    """Retrouve l'adresse réelle d'un lien Google News (sinon renvoie le lien tel quel)."""
    if "news.google." not in url:
        return url
    try:  # paquet optionnel « googlenewsdecoder » (requirements.txt)
        from googlenewsdecoder import gnewsdecoder

        r = gnewsdecoder(url, timeout=10)
        if isinstance(r, dict) and (r.get("success") or r.get("status")) and r.get("decoded_url"):
            return r["decoded_url"]
    except Exception:  # noqa: BLE001
        pass
    try:  # anciens liens : l'adresse est encodée en base64 dans l'identifiant
        import base64

        token = urlparse(url).path.rstrip("/").split("/")[-1]
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        m = re.search(rb"https?://[\x21-\x7e]+", raw)
        if m:
            return m.group(0).decode("ascii", "ignore")
    except Exception:  # noqa: BLE001
        pass
    return url


DOMAIN_NAMES = [
    ("tresor.economie.gouv.fr", "DG Trésor"), ("economie.gouv.fr", "TRACFIN / Ministère de l'Économie"),
    ("acpr.banque-france.fr", "ACPR"), ("banque-france.fr", "Banque de France"), ("amf-france.org", "AMF"),
    ("legifrance.gouv.fr", "Légifrance"), ("agence-francaise-anticorruption", "AFA"),
    ("eur-lex.europa.eu", "EUR-Lex (Journal officiel de l'UE)"), ("amla.europa.eu", "AMLA"),
    ("eba.europa.eu", "EBA"), ("esma.europa.eu", "ESMA"), ("bankingsupervision.europa.eu", "BCE"),
    ("ecb.europa.eu", "BCE"), ("consilium.europa.eu", "Conseil de l'UE"),
    ("europarl.europa.eu", "Parlement européen"), ("ec.europa.eu", "Commission européenne"),
    ("fatf-gafi.org", "GAFI"), ("ofac.treasury.gov", "OFAC"), ("treasury.gov", "Trésor américain"),
    ("fincen.gov", "FinCEN"), ("bis.org", "BRI / Comité de Bâle"),
]


def source_name(url: str, fallback: str = "") -> str:
    host = urlparse(url or "").netloc.lower()
    for dom, name in DOMAIN_NAMES:
        if dom in host:
            return name
    return fallback


NOISE = re.compile(r"cookie|javascript|navigateur|browser|newsletter|abonnez|subscribe|accepter|accept all|"
                   r"©|copyright|tous droits|all rights reserved|menu|se connecter|log in|partager|share this|"
                   r"aller au contenu|skip to|mentions légales|plan du site|rechercher", re.I)


def fetch_text(url: str, max_chars: int = 25_000) -> str:
    """Texte de la page officielle (le lien Google News est d'abord résolu ; vide si inaccessible)."""
    try:
        url = resolve_url(url)
        r = requests.get(url, headers=UA, timeout=15, allow_redirects=True)
        if "news.google." in urlparse(r.url).netloc:
            return ""
        ctype = r.headers.get("content-type", "")
        if "pdf" in ctype:
            return ""  # PDF : on se contente du résumé du flux
        page = r.text
        m = re.search(r"(?is)<(main|article)\b.*?</\1>", page)  # zone de contenu principale si présente
        if m and len(m.group(0)) > 1500:
            page = m.group(0)
        txt = re.sub(r"(?is)<(script|style|nav|footer|header|aside|form|noscript|button|svg).*?</\1>", " ", page)
        return clean(txt)[:max_chars]
    except Exception:  # noqa: BLE001
        return ""



# --------------------------------------------------------------------------- #
# Bibliothèque d'expertise : périmètre des émetteurs, objet par type, typologies par thème
# (sert à rédiger « L'essentiel » quand la source est courte, sans inventer de faits)
# --------------------------------------------------------------------------- #
ISSUER_SCOPE = {
    "ACPR": "autorité de supervision des secteurs bancaire, de l'assurance et des services de paiement",
    "TRACFIN": "cellule française de renseignement financier",
    "AMF": "autorité des marchés financiers, compétente notamment pour les sociétés de gestion et les PSAN",
    "DG Trésor": "autorité en charge de la mise en œuvre des mesures de gel des avoirs en France",
    "Journal officiel": "publication officielle des lois et règlements français",
    "AFA": "agence française chargée de la prévention et de la détection de la corruption",
    "AMLA": "autorité européenne de lutte contre le blanchiment de capitaux",
    "EBA": "autorité bancaire européenne",
    "ESMA": "autorité européenne des marchés financiers",
    "BCE / MSU": "superviseur des banques importantes de la zone euro",
    "UE (Conseil / Commission)": "institutions de l'Union européenne",
    "GAFI / FATF": "organisme intergouvernemental fixant les standards internationaux LCB-FT",
    "OFAC (US)": "autorité américaine d'administration des sanctions économiques",
    "FinCEN (US)": "cellule américaine de renseignement financier et régulateur LCB-FT",
    "Comité de Bâle (BIS)": "instance internationale de normalisation prudentielle bancaire",
}

ISSUER_NAME = {
    "ACPR": "l'ACPR", "TRACFIN": "TRACFIN", "AMF": "l'AMF", "DG Trésor": "la DG Trésor",
    "Journal officiel": "le Journal officiel", "AFA": "l'AFA", "AMLA": "l'AMLA", "EBA": "l'EBA",
    "ESMA": "l'ESMA", "BCE / MSU": "la BCE", "UE (Conseil / Commission)": "les institutions de l'UE",
    "GAFI / FATF": "le GAFI", "OFAC (US)": "l'OFAC", "FinCEN (US)": "FinCEN",
    "Comité de Bâle (BIS)": "le Comité de Bâle",
}


def _distinct(sents: list[str]) -> list[str]:
    """Écarte les phrases quasi identiques (même idée reformulée)."""
    out, seen = [], []
    for x in sents:
        w = set(re.findall(r"\w{4,}", x.lower()))
        if any(len(w & v) / max(1, min(len(w), len(v))) > .6 for v in seen):
            continue
        out.append(x)
        seen.append(w)
    return out


KIND_OBJET = {
    "Orientations / recommandations": "Le document précise les attentes de l'autorité et la manière dont elle "
                                      "appréciera la conformité des dispositifs sur ce sujet.",
    "Consultation": "Il s'agit d'un projet soumis à consultation : les établissements peuvent transmettre leurs "
                    "observations avant l'adoption de la version définitive.",
    "Texte législatif": "Le texte crée ou modifie des obligations juridiquement contraignantes pour les assujettis.",
    "Rapport / étude": "Le document présente des constats, des tendances et des typologies issus des travaux de "
                       "l'émetteur, à intégrer dans l'approche par les risques.",
    "Communiqué / actualité": "La publication informe le marché d'une évolution qui intéresse directement le "
                              "dispositif de conformité.",
}

TOPICS = [
    dict(nom="bénéficiaires effectifs et transparence",
         pat=r"bénéficiaires? effectifs?|beneficial owner|\bubo\b|transparen|actionnariat|registre",
         typo="Les risques portent sur l'opacité des structures : chaînes de détention complexes ou "
              "transfrontalières, trusts et constructions juridiques, prête-noms et contrôle exercé par "
              "d'autres moyens que la détention du capital.",
         signaux="Signaux faibles à surveiller : changements fréquents d'actionnariat, détentions juste sous le "
                 "seuil de 25 %, dirigeants sans lien apparent avec l'activité, divergences entre le registre "
                 "des bénéficiaires effectifs et les déclarations du client.",
         actions="revoir la méthode d'identification des UBO (détention et contrôle), signaler les divergences au "
                 "registre, prioriser la revue des structures complexes et documenter les diligences menées"),
    dict(nom="crypto-actifs",
         pat=r"crypto|\bmica\b|\bcasp\b|\bpsan\b|travel rule|virtual asset|stablecoin|blockchain",
         typo="Les risques identifiés concernent les flux transitant par des adresses auto-hébergées, des mixeurs "
              "ou des crypto-actifs renforçant l'anonymat, les conversions rapides entre blockchains et le "
              "recours à des prestataires non régulés de pays tiers.",
         signaux="Signaux faibles à surveiller : dépôts en monnaie fiat aussitôt convertis en crypto-actifs, fonds "
                 "reçus d'adresses exposées à des services à risque, volumes sans rapport avec le profil du client.",
         actions="déployer un outil d'analyse on-chain, contrôler la complétude des informations « travel rule », "
                 "documenter la propriété des adresses auto-hébergées et recalibrer les scénarios crypto"),
    dict(nom="sanctions et embargos",
         pat=r"sanction|gel des avoirs|asset freeze|restrictive measures|mesures restrictives|embargo|"
             r"double usage|dual-use|export control",
         typo="Les risques portent sur le contournement des sanctions : transbordement via des pays tiers, "
              "sociétés écrans récemment créées, cessions de parts sous le seuil de 50 %, et suppression ou "
              "altération d'informations dans les messages de paiement.",
         signaux="Signaux faibles à surveiller : nouveaux clients actifs avec des pays de transit, biens à double "
                 "usage, hausse soudaine des flux avec des juridictions limitrophes, changements d'actionnariat "
                 "intervenus après une désignation.",
         actions="mettre à jour les listes et les règles de filtrage, tester le calibrage des seuils de "
                 "correspondance, étendre le filtrage aux bénéficiaires effectifs et aux contreparties et "
                 "documenter le traitement des alertes"),
    dict(nom="fraude aux paiements",
         pat=r"fraud|virement instantané|instant payment|\biban\b|vérification du bénéficiaire|verification of "
             r"payee|scam|escroquer|usurpation|paiement",
         typo="Les risques concernent principalement la fraude au faux conseiller, au changement de RIB et au "
              "paiement autorisé par une victime manipulée, ainsi que l'utilisation de comptes de mules pour "
              "encaisser puis disperser les fonds.",
         signaux="Signaux faibles à surveiller : premier virement élevé vers un bénéficiaire inconnu, ajout de "
                 "bénéficiaire suivi d'un virement instantané, comptes récents alimentés par de multiples tiers.",
         actions="activer la vérification nom / IBAN, renforcer les scénarios en temps réel sur les virements "
                 "instantanés, détecter les comptes de mules et sensibiliser la clientèle"),
    dict(nom="financement du terrorisme",
         pat=r"terroris|\bobnl\b|non-profit|\bnpo\b|financement du terrorisme",
         typo="Les risques portent sur le financement par micro-montants, les cagnottes en ligne, le détournement "
              "d'organismes à but non lucratif et la liquidation rapide de l'épargne avant un départ.",
         signaux="Signaux faibles à surveiller : souscription de crédits suivie de retraits intégraux, virements "
                 "vers des zones de conflit ou des pays limitrophes, dons sans projet documenté.",
         actions="mettre à jour les scénarios de détection FT, filtrer en continu contre le registre national des "
                 "gels et traiter en priorité les alertes FT"),
    dict(nom="corruption et personnes politiquement exposées",
         pat=r"\bppe\b|\bpep\b|corruption|anticorruption|politiquement exposé|bribery",
         typo="Les risques concernent la corruption, le détournement de fonds publics, le recours à des "
              "intermédiaires et à des commissions occultes, et l'implication de PPE ou de leur entourage.",
         signaux="Signaux faibles à surveiller : paiements à des intermédiaires sans prestation identifiable, "
                 "patrimoine sans rapport avec les revenus d'une PPE, montages offshore.",
         actions="renforcer l'identification des PPE et de leur entourage, justifier l'origine des fonds et du "
                 "patrimoine et revoir la due diligence des intermédiaires"),
    dict(nom="déclarations de soupçon et renseignement financier",
         pat=r"déclaration de soupçon|tracfin|suspicious|\bstr\b|\bsar\b|cellule de renseignement|rapport annuel",
         typo="La publication met en lumière les typologies observées par la cellule de renseignement : "
              "sociétés éphémères, fraudes sociales et fiscales, escroqueries en ligne et usage de comptes de "
              "passage.",
         signaux="Signaux faibles à surveiller : opérations atypiques non analysées, déclarations tardives ou peu "
                 "étayées, flux répétitifs entre entités liées.",
         actions="intégrer les typologies publiées dans les scénarios de surveillance, améliorer la qualité et les "
                 "délais des déclarations de soupçon et former les équipes de niveau 1"),
    dict(nom="connaissance client et entrée en relation",
         pat=r"vigilance|\bkyc\b|\bkyb\b|due diligence|entrée en relation|onboarding|identification|"
             r"connaissance (?:du|de la) client",
         typo="Les risques portent sur les identités usurpées ou synthétiques, les faux justificatifs, l'entrée "
              "en relation à distance détournée et la sous-évaluation du risque lors de la mise à jour des dossiers.",
         signaux="Signaux faibles à surveiller : incohérences entre revenus déclarés et flux observés, coordonnées "
                 "partagées entre plusieurs clients, documents aux métadonnées suspectes, dossiers non actualisés.",
         actions="mettre à jour les procédures d'entrée en relation et de revue périodique, vérifier les "
                 "documents à la source et recalibrer la classification des risques clients"),
    dict(nom="résilience opérationnelle et numérique",
         pat=r"\bdora\b|\btic\b|\bict\b|cyber|incident|intelligence artificielle|artificial intelligence|\bai\b",
         typo="Les risques concernent les incidents informatiques, les cyberattaques et la défaillance de "
              "prestataires critiques, susceptibles d'interrompre les outils de surveillance et de filtrage.",
         signaux="Signaux faibles à surveiller : dépendance à un prestataire unique, incidents répétés sur les "
                 "outils de conformité, plans de continuité non testés.",
         actions="cartographier les outils de conformité et leurs prestataires, tester la continuité du filtrage "
                 "et formaliser la gestion et la notification des incidents"),
    dict(nom="durabilité et fiscalité",
         pat=r"durabilit|\besg\b|\bcsrd\b|\besrs\b|\bdac8\b|\bcrs\b|échange automatique|fiscal",
         typo="Les risques portent sur des données de durabilité ou fiscales incomplètes ou inexactes, "
              "l'écoblanchiment et les défauts de déclaration aux administrations.",
         signaux="Signaux faibles à surveiller : résidences fiscales incohérentes, refus de communiquer les "
                 "informations demandées, écarts entre données publiées et données de gestion.",
         actions="fiabiliser la collecte des données clients et de durabilité, formaliser les procédures de "
                 "déclaration et soumettre les publications à une revue du contrôle interne"),
    dict(nom="exigences prudentielles",
         pat=r"prudenti|fonds propres|capital|bâle|basel|\bcrr\b|\bcrd\b|liquidit|solvab",
         typo="Les risques portent sur la mauvaise calibration des exigences, la qualité insuffisante des données "
              "et les erreurs de reporting réglementaire.",
         signaux="Signaux faibles à surveiller : écarts récurrents entre reporting et données de gestion, "
                 "corrections tardives, dépendance excessive aux modèles internes.",
         actions="adapter les calculs, fiabiliser les données sources et renforcer les contrôles sur le "
                 "reporting réglementaire"),
]
DEFAULT_TOPIC = dict(
    nom="lutte contre le blanchiment",
    typo="Les risques visés relèvent du blanchiment de capitaux et du financement du terrorisme : fractionnement "
         "des opérations, comptes de passage, sociétés écrans et flux sans justification économique.",
    signaux="Signaux faibles à surveiller : opérations atypiques au regard du profil, entrées et sorties rapides "
            "de fonds, contreparties situées dans des juridictions à haut risque.",
    actions="réaliser une analyse d'écart entre la publication et le dispositif, mettre à jour les procédures et "
            "les scénarios et informer les équipes concernées")

NOUVEAU = re.compile(r"nouve(?:au|lle|aux)|désormais|introdu|typolog|tendance|hausse|augment|émerg|"
                     r"risque|fraude|contourn|signal|vulnérab|\bnew\b|emerging|trend|increase|risk|threat|menace",
                     re.I)


def topic(nom: str) -> dict:
    return next((t for t in TOPICS if t["nom"] == nom), DEFAULT_TOPIC)


def detect_topics(text: str, n: int = 2) -> list[dict]:
    scored = sorted(((len(re.findall(t["pat"], text, re.I)), t) for t in TOPICS), key=lambda x: -x[0])
    found = [t for k, t in scored if k > 0][:n]
    return found or [DEFAULT_TOPIC]


def action_phrase(nom: str, emetteur: str, date: str = "", scope: str | None = None) -> str:
    """« Le 25/10/2026, l'ACPR (…) a publié la mise à jour de… » à partir du titre de la publication."""
    who = ISSUER_NAME.get(emetteur, emetteur)
    head = (f"Le {date}, " if date else "") + who + (f" ({scope})" if scope else "")
    head = head[0].upper() + head[1:]
    m = re.match(r"^(?:l['’]\s*)?[\w&/\- ]{2,40}?\s+(publie|publient|met à jour|lance|adopte|"
                 r"publishes|publish|launches|issues|releases|adopts)\s+(.+)$", nom, re.I)
    if m and m.group(1).lower() in ("publie", "publient", "met à jour", "lance", "adopte"):
        verbe = {"met à jour": "a mis à jour", "lance": "a lancé", "adopte": "a adopté"}.get(
            m.group(1).lower(), "a publié")
        return f"{head} {verbe} {m.group(2).rstrip('.')}."
    if m:
        return f"{head} a publié « {m.group(2).rstrip('.')} »."
    return f"{head} a publié « {nom} »."


def essentiel_paragraphs(*, nom: str, emetteur: str, date: str, kind: str, cible: str, text: str,
                         sents: list[str], ranked: list[str], strong: list[str],
                         objet: str = "", nouveautes: str = "", topics: list[dict] | None = None,
                         intro: str = "", complement: str = "") -> list[str]:
    """Trois paragraphes : contexte & objet / nouveautés & typologies / impacts opérationnels."""
    topics = topics or detect_topics(f"{nom} {text}")
    scope = ISSUER_SCOPE.get(emetteur)
    # 1. Contexte & objet
    if not intro:
        intro = action_phrase(nom, emetteur, date, scope)
    if objet:
        body = objet
    elif len(sents) >= 3:
        top = set(_distinct(ranked)[:4])
        body = " ".join(short(x, 330) for x in sents if x in top)
    else:
        body = KIND_OBJET.get(kind, KIND_OBJET["Communiqué / actualité"])
    p1 = f"{intro} {body} Périmètre : {cible}." + (f" {complement}" if complement else "")
    # 2. Nouveautés & typologies
    if nouveautes:
        new = nouveautes
    else:
        used = set(ranked[:4])
        new = " ".join(short(x, 300) for x in _distinct([x for x in sents if x not in used and NOUVEAU.search(x)])[:3])
        new = " ".join(new.split(" ")[:120])
    t = topics[0]
    p2 = " ".join(x for x in [new, t["typo"], t["signaux"]] if x)
    # 3. Impacts opérationnels
    actions = "; ".join(dict.fromkeys(tp["actions"] for tp in topics))
    p3 = (f"Processus impactés en priorité : {', '.join(strong) if strong else 'dispositif LCB-FT dans son ensemble'}. "
          f"Actions recommandées : {actions}. Réaliser une analyse d'écart avec le dispositif existant, tracer les "
          f"décisions et le paramétrage des outils, et informer les équipes de niveau 1 et 2 ainsi que l'organe "
          f"de direction.")
    return [p1, p2, p3]

# --------------------------------------------------------------------------- #
# Fiche par extraction (sans IA)
# --------------------------------------------------------------------------- #
REF_PATTERNS = [
    r"(?:Règlement|Directive|Décision)(?: délégué| d'exécution)?\s*\((?:UE|CE)\)\s*(?:n°\s*)?\d{2,4}/\d+",
    r"(?:Regulation|Directive|Decision)(?: \(EU\)| \(EC\))\s*(?:No\s*)?\d{2,4}/\d+",
    r"(?:Décret|Arrêté|Ordonnance|Loi)\s+n°\s*[\d\-]+(?:\s+du\s+\d{1,2}(?:er)?\s+\w+\s+\d{4})?",
    r"(?:EBA|ESMA|EIOPA|AMLA)/(?:GL|RTS|ITS|CP|Op|REC|DC)/\d{4}/\d+",
    r"Instruction\s+(?:n°\s*)?\d{4}-I-\d+",
    r"Recommandation\s+(?:n°\s*)?\d{4}-R-\d+",
    r"DOC-\d{4}-\d+",
    r"Executive Order\s+\d+",
]

DATE_PHRASE = re.compile(
    r"(entr\w*\s+en\s+(?:vigueur|application)|applicable|s'appliquer\w*|apply\w*\s+from|enter\w*\s+into\s+force|"
    r"application date|à compter du|from)\s[^.]{0,80}?"
    r"(\d{1,2}(?:er)?\s+(?:" + "|".join(MONTHS_FR + MONTHS_EN) + r")\s+\d{4}|"
    r"(?:" + "|".join(MONTHS_FR + MONTHS_EN) + r")\s+\d{4})", re.I)


def _fmt_date_phrase(s: str) -> str:
    s = s.lower()
    for i, m in enumerate(MONTHS_EN):
        s = re.sub(rf"\b{m}\b", MONTHS_FR[i], s)
    m = re.search(r"(" + "|".join(MONTHS_FR) + r")\s+(\d{4})", s)
    return f"{m.group(1).capitalize()} {m.group(2)}" if m else s


def _pick(sents: list[str], pattern: re.Pattern, used: set) -> str:
    for s in sents:
        if s not in used and pattern.search(s):
            used.add(s)
            return short(s)
    return ""


def _rank(sents: list[str]) -> list[str]:
    words = re.findall(r"\w{5,}", " ".join(sents).lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return sorted(sents, key=lambda x: -sum(freq.get(w, 0) for w in re.findall(r"\w{5,}", x.lower()))
                  / (len(x) ** 0.5))


def extractive_flash(item: dict, page_text: str = "") -> dict:
    title, desc = item["title"], item.get("desc", "")
    corpus = " ".join(x for x in [desc, page_text] if x)
    blob = f"{title} {corpus}"
    sents = sentences(corpus)
    ranked = _rank(sents) if sents else []
    used: set = set()

    # Référence
    ref = ""
    for pat in REF_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            ref = m.group(0)
            break
    pub = datetime.fromtimestamp(item["ts"]).strftime("%d/%m/%Y") if item["ts"] else "date non précisée"
    reference = f"{ref} · {item['source']}, publié le {pub}" if ref else f"{item['source']} — publication du {pub}"

    # Calendrier
    m = DATE_PHRASE.search(corpus)
    application = _fmt_date_phrase(m.group(2)) if m else "À confirmer (voir le texte)"

    # Cible
    cibles = [lab for lab, pat in CIBLES if re.search(pat, blob, re.I)]
    cible = ", ".join(cibles[:5]) if cibles else item["cible_defaut"]

    # 3 points
    kind = item["kind"]
    p1 = _pick(ranked, PURPOSE, used) or (ranked[0] if ranked else "") or short(desc) or \
        action_phrase(title, item["source"])
    used.add(p1)
    p2 = _pick(ranked, OBLIGATION, used) or {
        "Consultation": "Projet soumis à consultation : les exigences finales peuvent encore évoluer ; "
                        "identifier dès maintenant les écarts avec le dispositif existant.",
        "Orientations / recommandations": "Comparer les attentes du superviseur au dispositif existant et "
                                          "documenter les écarts dans un plan d'action.",
    }.get(kind, "Analyser les exigences opérationnelles du texte et les traduire en procédures et contrôles.")
    p3 = _pick(ranked, CONSTRAINT, used) or {
        "Consultation": "Texte non définitif : suivre la date de clôture de la consultation et la publication "
                        "de la version finale.",
    }.get(kind, "Un défaut de mise en conformité expose à des sanctions du superviseur et à un risque "
                "réputationnel.")

    # Checklist
    checklist = []
    for dom, pat in DOMAINS.items():
        matches = [m.group(0).lower() for m in re.finditer(pat, blob, re.I)]
        hits, n = sorted(set(matches)), len(matches)
        impact = "Fort" if n >= 4 else ("Modéré" if n >= 1 else "Faible")
        found = [h for h in hits if len(h) > 2][:4]
        texte = (f"{DOMAIN_ACTIONS[dom]} (thèmes relevés : {', '.join(found)})." if found else
                 "Impact indirect : vérifier la cohérence de ce volet du dispositif avec la publication.")
        checklist.append(dict(domaine=dom, texte=texte, impact=impact, fait=False))

    # L'essentiel : 3 paragraphes (contexte & objet / nouveautés & typologies / impacts opérationnels)
    strong = [c["domaine"] for c in checklist if c["impact"] != "Faible"]
    essentiel = essentiel_paragraphs(nom=title, emetteur=item["source"], date=pub, kind=kind, cible=cible,
                                     text=corpus, sents=sents, ranked=ranked, strong=strong)

    return dict(
        titre=short(title, 140), reference=reference, pays_source=item["juridiction"],
        adoption=month_year(item["ts"]), application=application, cible=cible,
        points=[p1, p2, p3], checklist=checklist, essentiel=essentiel,
        contexte=essentiel[0], risque=essentiel[2],
        sources=" · ".join(dict.fromkeys(x for x in [item["source"], item.get("publisher", "")] if x)),
        type=kind, mode="Extraction automatique",
        lien=item["link"],
    )


# --------------------------------------------------------------------------- #
# Fiche par IA (optionnelle)
# --------------------------------------------------------------------------- #
LLM_PROMPT = """[RÔLE & EXPERTISE]
Tu es un expert senior en conformité LCB-FT (lutte contre le blanchiment de capitaux et le financement du
terrorisme), sanctions, embargos et gestion des risques bancaires. Ta mission est d'analyser la publication
ci-dessous et de produire une fiche de synthèse claire, directement exploitable par des compliance officers
et des analystes LCB-FT, en français.

[RÈGLES DE RÉDACTION — « L'ESSENTIEL »]
Exactement 3 paragraphes distincts, rédigés de manière fluide :
1. contexte_objet : nom exact du texte ou de la publication, émetteur et date, objet principal et périmètre
   d'application.
2. nouveautes_typologies : faits marquants et nouveautés réglementaires ou typologiques, risques spécifiques
   identifiés (fraude, blanchiment, abus de faiblesse, contournement de sanctions), signaux faibles à surveiller
   sur le marché ou la clientèle.
3. impacts_operationnels : impacts concrets sur les processus internes (KYC/KYB, filtrage des transactions,
   paramétrage des outils, reporting) et recommandations opérationnelles immédiates pour l'établissement assujetti.

[RÈGLES DE SÉCURITÉ]
- Ne mentionne jamais qu'un texte est incomplet, tronqué ou que son contenu n'a pas pu être récupéré.
- Si le texte source est court, extrapole logiquement à partir des informations disponibles et du périmètre
  habituel de l'émetteur, mais n'invente aucun chiffre, aucune date, aucun numéro d'article ni aucune
  obligation précise qui ne figure pas dans la source.
- Ton technique, précis, neutre et orienté gestion des risques ; terminologie exacte du secteur
  (KYC/KYB, UBO, filtrage, typologies, scénarios de surveillance).

[FORMAT DE SORTIE]
Un unique objet JSON, sans texte autour :
{{"titre": "nom exact et court du texte (max 90 caractères)",
 "reference": "référence complète du texte ou de la publication",
 "pays_source": "{juridiction}",
 "adoption": "Mois AAAA",
 "application": "Mois AAAA ou Non précisé",
 "cible": "assujettis visés (ex. Banques, PSAN, SGP, Assurances)",
 "points": ["objectif central (1 phrase)", "obligation technique clé (1 phrase)", "sanction ou contrainte majeure (1 phrase)"],
 "checklist": [
   {{"domaine": "KYC / KYB & UBO", "texte": "impact sur l'entrée en relation (1 phrase)", "impact": "Fort|Modéré|Faible"}},
   {{"domaine": "Filtrage & transactions", "texte": "impact sur le filtrage, les scénarios, les règles (1 phrase)", "impact": "Fort|Modéré|Faible"}},
   {{"domaine": "Gouvernance & reporting", "texte": "audits, déclarations TRACFIN / ACPR / AMF (1 phrase)", "impact": "Fort|Modéré|Faible"}}],
 "contexte_objet": "paragraphe 1",
 "nouveautes_typologies": "paragraphe 2",
 "impacts_operationnels": "paragraphe 3"}}

[DONNÉES D'ENTRÉE]
- Titre : {title}
- Source / Émetteur : {source} ({juridiction})
- Date : {date}
- Texte brut extrait :
{content}
"""


def llm_provider(secrets) -> str | None:
    try:
        if secrets.get("ANTHROPIC_API_KEY"):
            return "Claude"
        if secrets.get("MISTRAL_API_KEY"):
            return "Mistral"
        if secrets.get("OLLAMA_URL"):
            return "Ollama"
    except Exception:  # noqa: BLE001
        pass
    return None


def _json_from(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def llm_flash(item: dict, page_text: str, secrets) -> dict:
    """Fiche rédigée par IA ; lève une exception en cas d'échec (le code appelant bascule sur l'extraction)."""
    provider = llm_provider(secrets)
    pub = datetime.fromtimestamp(item["ts"]).strftime("%d/%m/%Y") if item["ts"] else "non précisée"
    content = clean(" ".join(x for x in [item.get("desc", ""), page_text] if x), 12_000) or item["title"]
    prompt = LLM_PROMPT.format(source=item["source"], juridiction=item["juridiction"], date=pub,
                               title=item["title"], content=content)
    if provider == "Claude":
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=90, headers={
            "x-api-key": secrets["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
            "content-type": "application/json"}, json={
            "model": secrets.get("CWP_LLM_MODEL", "claude-haiku-5-5"), "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        data = _json_from("".join(b.get("text", "") for b in r.json().get("content", [])))
    elif provider == "Mistral":
        r = requests.post("https://api.mistral.ai/v1/chat/completions", timeout=90, headers={
            "Authorization": f"Bearer {secrets['MISTRAL_API_KEY']}"}, json={
            "model": secrets.get("CWP_LLM_MODEL", "mistral-small-latest"),
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        data = _json_from(r.json()["choices"][0]["message"]["content"])
    elif provider == "Ollama":
        r = requests.post(secrets["OLLAMA_URL"].rstrip("/") + "/api/generate", timeout=180, json={
            "model": secrets.get("CWP_LLM_MODEL", "mistral"), "prompt": prompt, "format": "json",
            "stream": False})
        r.raise_for_status()
        data = _json_from(r.json().get("response", ""))
    else:
        raise RuntimeError("Aucun fournisseur IA configuré")

    base = extractive_flash(item, page_text)  # complète les champs manquants
    for k in ("titre", "reference", "pays_source", "adoption", "application", "cible"):
        if isinstance(data.get(k), str) and data[k].strip():
            base[k] = data[k].strip()
    ess = [data.get(k) for k in ("contexte_objet", "nouveautes_typologies", "impacts_operationnels")]
    if all(isinstance(x, str) and x.strip() for x in ess):
        base["essentiel"] = [x.strip() for x in ess]
        base["contexte"], base["risque"] = base["essentiel"][0], base["essentiel"][2]
    if isinstance(data.get("points"), list) and len(data["points"]) >= 3:
        base["points"] = [str(p) for p in data["points"][:3]]
    if isinstance(data.get("checklist"), list) and data["checklist"]:
        cl = []
        for i, c in enumerate(data["checklist"][:3]):
            imp = c.get("impact", "Modéré")
            cl.append(dict(domaine=c.get("domaine") or list(DOMAINS)[i], texte=c.get("texte", ""),
                           impact=imp if imp in ("Fort", "Modéré", "Faible") else "Modéré", fait=False))
        base["checklist"] = (cl + base["checklist"][len(cl):])[:3]
    base["mode"] = f"Synthèse IA ({provider})"
    return base


def build_flash(item: dict, secrets=None, use_ai: bool = True) -> dict:
    page_text = fetch_text(item["link"])
    if use_ai and secrets is not None and llm_provider(secrets):
        try:
            return llm_flash(item, page_text, secrets)
        except Exception as e:  # noqa: BLE001
            d = extractive_flash(item, page_text)
            d["mode"] = f"Extraction automatique (IA indisponible : {type(e).__name__})"
            return d
    return extractive_flash(item, page_text)
