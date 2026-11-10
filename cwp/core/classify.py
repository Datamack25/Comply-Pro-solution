"""
cwp.core.classify — classification automatique des actualités (heuristique, sans IA).

À partir du titre et du résumé d'un article : entité visée, pays, type de mesure, autorité,
montant, langue. Aucune dépendance à Streamlit : testable unitairement (tests/test_classify.py).
"""
from __future__ import annotations

import html
import re

from . import geo

# --------------------------------------------------------------------------- #
# Nettoyage
# --------------------------------------------------------------------------- #

def clean(t, n=280):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


def headline_of(it: dict) -> str:
    """Titre sans le nom du média (« … - Reuters »)."""
    t, src = it.get("title", ""), it.get("source") or ""
    if src and t.endswith(" - " + src):
        return t[: -(len(src) + 3)].strip()
    return re.sub(r"\s+-\s+[^-]{2,60}$", "", t).strip()


_FR_WORDS = set("le la les des du de un une et est sont pour par avec dans sur contre selon après au aux "
                "qui que ses leur nouvelles nouveau sanctionne gel avoirs amende liste grise".split())
_EN_WORDS = set("the of and to in on for with by at from is are be new over against after its their "
                "imposes sanctioned fined freeze assets grey list".split())


def detect_lang(text: str, default: str = "") -> str:
    """Langue probable (fr / en) d'un titre, par comptage de mots outils."""
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", str(text or "").lower())
    fr = sum(w in _FR_WORDS for w in words) + sum(1 for w in words if re.search(r"[àâçéèêëîïôûùüÿœ]", w))
    en = sum(w in _EN_WORDS for w in words)
    if fr == en:
        return default
    return "fr" if fr > en else "en"


# --------------------------------------------------------------------------- #
# Mesures, autorités, montants
# --------------------------------------------------------------------------- #
# (clé, libellé, couleur écran, couleur export, motifs) — l'ordre fixe la priorité
MEASURES = [
    ("gel", "Gel des avoirs", "#ff4d6d", "#c62839", ["gel des avoirs", "gel d'avoirs", "asset freeze", "assets frozen",
                                                     "frozen assets", "freezes assets", "gèle les avoirs"]),
    ("liste", "Liste GAFI", "#ffb020", "#b7791f", ["liste grise", "grey list", "gray list", "greylist", "liste noire",
                                                   "black list", "high-risk jurisdiction", "juridictions à haut risque"]),
    ("amende", "Amende", "#ff7a45", "#c2541b", ["amende", "fined", " fine ", " fines ", "pénalité", "penalty", "penalties",
                                                "settlement", "commission des sanctions"]),
    ("sanction", "Sanction", "#ff4d6d", "#c62839", ["sanction", "designat", "désign", "sdn list", "blacklist", "paquet de"]),
    ("embargo", "Embargo / export", "#a855f7", "#7e3fbf", ["embargo", "export control", "contrôle des exportations",
                                                           "contrôles à l'exportation", "double usage", "dual-use", "dual use"]),
    ("enquete", "Enquête / poursuite", "#00d4ff", "#1a6fa0", ["enquête", "investigation", "probe", "charged", "inculp",
                                                              "mis en examen", "poursuit", "indict", "arrest", "interpell",
                                                              "condamn", "convicted", "perquisition", "raid"]),
    ("regle", "Réglementation", "#00ff88", "#1d8a55", ["règlement", "directive", "guidelines", "lignes directrices",
                                                       "consultation", "amlr", "mica", "dora", "entre en vigueur", "circulaire", "circular",
                                                       "applicable", "rule", "framework", "standard"]),
]
NEWS_MEASURE = ("news", "Actualité", "#52708a", "#6b7c8c")
SANCTION_KINDS = {"gel", "liste", "amende", "sanction", "embargo"}
SCREEN_COLOR = {m[0]: m[2] for m in MEASURES} | {"news": NEWS_MEASURE[2]}
EXPORT_COLOR = {m[0]: m[3] for m in MEASURES} | {"news": NEWS_MEASURE[3]}

AUTHORITIES = [
    ("OFAC", ["ofac"]), ("Trésor US", ["treasury", "trésor américain"]), ("OFSI", ["ofsi"]),
    ("Conseil de l'UE", ["conseil de l'ue", "council of the eu", "eu council", "commission européenne", "european commission"]),
    ("ONU", [" onu ", "united nations", "nations unies", "conseil de sécurité", "security council"]),
    ("GAFI", ["gafi", "fatf"]), ("AMLA", ["amla"]), ("ACPR", ["acpr"]), ("AMF", [" amf ", "autorité des marchés"]),
    ("Tracfin", ["tracfin"]), ("EBA", [" eba ", "autorité bancaire européenne", "european banking authority"]),
    ("ESMA", ["esma"]), ("BCE", [" bce ", " ecb ", "banque centrale européenne"]), ("FCA", [" fca "]),
    ("FinCEN", ["fincen"]), ("SEC", [" sec "]), ("DOJ", [" doj ", "department of justice", "justice department"]),
    ("BIS", [" bis ", "bureau of industry"]), ("AFA", [" afa ", "agence française anticorruption"]),
    ("PNF", [" pnf ", "parquet national financier"]), ("FINMA", ["finma"]), ("BaFin", ["bafin"]),
]


def norm_text(s):
    return " " + re.sub(r"[,;:!?()\[\]«»\"“”‘’|/]", " ", (s or "").lower()) + " "


def detect_measure(text):
    for key, label, _, _, pats in MEASURES:
        if any(p in text for p in pats):
            return key, label
    return NEWS_MEASURE[0], NEWS_MEASURE[1]


def detect_authorities(text):
    return ", ".join([n for n, pats in AUTHORITIES if any(p in text for p in pats)][:2])


_CUR = r"(?P<cur>€|\$|£|eur(?:os?)?|euros?|usd|dollars?|gbp|livres?(?: sterling)?|chf|francs? suisses?)"
_NUM = r"(?P<num>\d{1,3}(?:[   .,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
_MULT = r"(?P<mult>milliards?|billions?|bn|mds?|md|millions?|mn|mio|m|mille|k)?"
_AMOUNT_RES = [
    re.compile(_CUR + r"\s?" + _NUM + r"\s?" + _MULT + r"\b", re.I),            # $5 million, €1,2 md
    re.compile(_NUM + r"\s?" + _MULT + r"\s?(?:d['’]\s?|de\s)?" + _CUR, re.I),  # 5 M€, 1,2 milliard d'euros
]
_CUR_SYM = {"€": "€", "eur": "€", "euro": "€", "euros": "€", "$": "$", "usd": "$", "dollar": "$", "dollars": "$",
            "£": "£", "gbp": "£", "livre": "£", "livres": "£", "chf": "CHF"}


def _to_float(num):
    n = re.sub(r"[   ]", "", num)
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", n):          # 1.500.000 / 1,500,000
        return float(re.sub(r"[.,]", "", n))
    return float(n.replace(",", "."))


def detect_amount(text):
    """Renvoie (montant lisible, valeur numérique) ou ("—", 0)."""
    best = None
    for rx in _AMOUNT_RES:
        for m in rx.finditer(text):
            try:
                v = _to_float(m.group("num"))
            except ValueError:
                continue
            mult = (m.group("mult") or "").lower()
            if mult.startswith(("milliard", "billion", "bn", "md")):
                v *= 1e9
            elif mult.startswith(("million", "mn", "mio")) or mult == "m":
                v *= 1e6
            elif mult in ("mille", "k"):
                v *= 1e3
            cur = m.group("cur").lower()
            sym = next((v2 for k, v2 in _CUR_SYM.items() if cur.startswith(k)), cur.upper())
            if v < 1000 and not mult:   # « 22e paquet », années, etc. : ignorés
                continue
            if best is None or v > best[1]:
                best = (sym, v)
    if not best:
        return "—", 0
    sym, v = best
    if v >= 1e9:
        s_ = f"{v/1e9:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " Md"
    elif v >= 1e6:
        s_ = f"{v/1e6:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " M"
    else:
        s_ = f"{v:,.0f}".replace(",", " ")
    return f"{s_} {sym}", v


# --------------------------------------------------------------------------- #
# Entité visée
# --------------------------------------------------------------------------- #
_STOP = set("""le la les l un une des du de d au aux et en à a sur pour par avec dans selon après avant contre face vers
ce cette ces il elle ils elles on nous voici est sont sera plus moins fin premier première nouveau nouvelle nouveaux nouvelles
comment pourquoi quand quel quelle quels quelles qui que quoi
the a an of and to in on for with by at from as is are be will can could should would it its his her their new first top more
how why what who when where this that these those over under amid after before into about
exclusive exclusif breaking update live analyse analysis opinion tribune interview vidéo video podcast édito
sources source devant derrière regarder documentaire reportage enquête décryptage infographie carte vidéos photos
capitole parlement parliament gouvernement government ministère ministry ministre minister président president
présidente patron patronne chef chief ceo directeur director premier ministre manifestants protesters
congrès congress sénat senate assemblée maison blanche white house élysée matignon
selon alors face voici voilà pourquoi comment ici là
nord sud est ouest north south east west
must pay pays paid fined fines hits hit adopt adopts adopted impose imposes imposed nearly officially record largest
biggest ever agrees agree settles settle faces face says hails welcomes slaps sanctioning sees amid
foreign ministers ministres affaires étrangères diplomates diplomats leaders dirigeants
listings listing targeting individuals entities individus entités military defense industry complex
sanction sanctions sanctionne sanctionné sanctionnée sanctionnés sanctionnées sanctioned sanctioning sanctionnent
gel avoirs embargo amende amendes liste grise noire grey gray list
treasury trésor targets target designates designated imposes impose adds announces says said council conseil commission
blanchiment fraude corruption conformité terrorisme financement crypto cryptos cryptomonnaie cryptomonnaies
money laundering aml lcb-ft régulateur regulator rapport report guide export exports
ue eu us uk usa u.s onu un fatf ofac treasury
lundi mardi mercredi jeudi vendredi samedi dimanche janvier février mars avril mai juin juillet août septembre octobre novembre décembre
monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september october november december""".split())
_STOP |= {w.lower() for a, _ in AUTHORITIES for w in a.split()}
_STOP |= geo.all_country_tokens()
_CONN = {"de", "du", "des", "of", "and", "&", "la", "le", "el", "al", "bin", "van", "von", "y"}


def extract_entity(h):
    """Premier groupe de mots à majuscule qui n'est ni un pays, ni une autorité, ni un mot courant."""
    groups, cur = [], []
    for w in re.findall(r"[\w'’&.\-]+", h):
        base = re.sub(r"^(?:[LlDdJj]|Qu|qu)['’]", "", w)
        base = re.sub(r"['’]s?$", "", base).strip(".'’-")   # Russia's -> Russia
        if not base:
            continue
        if base[:1].isupper():
            cur.append(base)
        elif cur and base.lower() in _CONN:
            cur.append(base)
        else:
            if cur:
                groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    for g in groups:
        cut = next((i for i, x in enumerate(g) if i > 0 and _is_stop(x) and x.lower() not in _CONN), None)
        if cut:
            g = g[:cut]
        while g and (_is_stop(g[0]) or g[0].lower() in _CONN):
            g = g[1:]
        while g and (_is_stop(g[-1]) or g[-1].lower() in _CONN):
            g = g[:-1]
        if g and len(" ".join(g)) > 2:
            return " ".join(g[:5])
    return ""


def _is_stop(w: str) -> bool:
    lw = w.lower()
    return lw in _STOP or geo.norm(w).strip() in _STOP


def detect_entity(h, country):
    ent = extract_entity(h)
    if not ent:
        return country if country != "—" else "—"
    c = geo.country_by_name(ent)
    if c:                       # l'entité est un pays : on l'écrit en français (Russia -> Russie)
        return c[1]
    return ent


# --------------------------------------------------------------------------- #
# Décision prononcée ou simple actualité ?
# --------------------------------------------------------------------------- #
_NOT_ACTION = ["documentaire", "documentary", "regarder", "à voir", "vidéo", "video", "podcast", "replay", "reportage",
               "opinion", "tribune", "édito", "editorial", "chronique", "analyse", "analysis", "décryptage", "explainer",
               "explained", "interview", "entretien", "témoignage", "les dessous", "inside", "comment ", "pourquoi", "how ",
               "why ", "what ", "faut-il", "should ", "?", "manifestant", "protest", "réclam", "appelle à", "appel à",
               "calls for", "call for", "urge", "demande un", "demandent un", "accuse", "dénonce", "critique", "menace",
               "threaten", "pourrait", "envisage", "could ", "may ", "might ", "considers", "weighs", "mulls", "plans to",
               "prévoit de", "projet de", "proposal", "proposition", "promouvoir", "promote", "contourn", "evade", "evasion",
               "se dit prêt", "disposée", "disposé", "levée des sanctions", "lift sanctions", "lifts sanctions",
               "allègement", "eases sanctions"]
_ACTION = ["adopte", "adopté", "adopts", "adopted", "impose", "imposes", "imposed", "inflige", "infligé", "sanctionne",
           "sanctionné", "sanctions ", "sanctioned", "designat", "désigne", "inscrit", "ajoute", "adds", "added", "listed",
           "gèle", "gelé", "gel des avoirs", "freezes", "frozen", "froze", "prononce", "prononcé", "condamn", "fined",
           "fines ", "amende de", "amende record", "pénalité de", "penalty of", "settle", "règle", "agrees to pay",
           "accepte de payer", "to pay", "pays ", "paiera", "prolonge", "prolongé", "extends", "extended", "renouvelle",
           "renews", "élargit", "expands", "interdit", "bans", "banned", "blacklist", "entity list", "nouveau paquet",
           "new package", "e paquet", "th package", "retire", "removes", "removed", "exits grey", "sort de la liste",
           "placé sur", "placed on", "maintient", "keeps", "embargo sur", "arms embargo", "export ban"]


def is_action(r: dict) -> bool:
    if r["mkey"] not in SANCTION_KINDS:
        return False
    t = " " + r["headline"].lower() + " "
    if any(x in t for x in _NOT_ACTION):
        return False
    return any(x in t for x in _ACTION)


# --------------------------------------------------------------------------- #
# Enrichissement d'un article
# --------------------------------------------------------------------------- #

def enrich(it: dict) -> dict:
    """Ajoute headline, entity, cc, country, mkey, measure, auth, amount, amount_v, lang à un article."""
    h = headline_of(it)
    desc = it.get("desc", "")
    if it.get("source"):
        desc = desc.replace(it["source"], " ")      # le nom du média n'indique pas le pays de l'affaire
    desc = desc.replace(h, " ")
    text = norm_text(h + " " + desc)
    mkey, measure = detect_measure(text)
    auth = detect_authorities(text)
    cc, country = geo.country_of(h, desc, mkey, auth)
    entity = detect_entity(h, country)
    if entity in ("—", "", "Union européenne", "États-Unis", "Royaume-Uni", "ONU") and cc:
        entity = country if mkey in SANCTION_KINDS else entity
    amount, amount_v = detect_amount(" " + h + " " + desc + " ")
    lang = it.get("lang") or detect_lang(h, "fr")
    return {**it, "headline": h, "entity": entity, "cc": cc, "country": country, "mkey": mkey, "measure": measure,
            "auth": auth, "amount": amount, "amount_v": amount_v, "lang": lang}


# --------------------------------------------------------------------------- #
# Crédibilité des médias
# --------------------------------------------------------------------------- #
# Rang de crédibilité (plus petit = plus crédible). Sources officielles d'abord, puis agences et grands titres.
SOURCE_RANK = [
    ["ofac", "treasury", "u.s. department", "council of the eu", "conseil de l'ue", "consilium", "european commission",
     "commission européenne", "acpr", "banque de france", "amf", "tracfin", "fca", "ofsi", "fincen", "sec.gov", "justice.gov",
     "fatf", "gafi", "united nations", "nations unies", "eba", "esma", "ecb", "bce", "amla"],
    ["reuters", "bloomberg", "agence france-presse", "afp", "associated press", "ap news", "financial times"],
    ["wall street journal", "the economist", "new york times", "washington post", "les echos", "le monde",
     "bbc", "the guardian", "politico", "cnbc", "le figaro", "franceinfo", "france 24", "l'agefi", "agefi",
     "la tribune", "challenges", "euronews", "dw", "rfi", "nikkei", "handelsblatt", "les échos"],
    ["al jazeera", "cnn", "abc news", "nbc news", "cbs news", "fox business", "forbes", "yahoo", "marketwatch",
     "barron's", "the times", "the telegraph", "le parisien", "20 minutes", "ouest-france", "bfm", "lci",
     "boursorama", "zonebourse", "investing.com", "the hill", "axios", "pbs", "npr", "time", "newsweek",
     "anadolu", "trt", "interfax", "kyiv independent", "eubusiness"],
]


def source_rank(r: dict) -> int:
    s_ = (r.get("source") or r.get("media") or "").lower()
    for i, tier in enumerate(SOURCE_RANK):
        if any(k in s_ for k in tier):
            return i
    return len(SOURCE_RANK)
