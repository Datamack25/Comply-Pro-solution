"""
cwp.core.geo — détection des pays cités dans un titre d'actualité.

Corrige les erreurs de l'ancienne détection par sous-chaîne :
  • recherche par MOTS ENTIERS sur un texte sans accents (« machine » ne donne plus la Chine,
    « incubateur » ne donne plus Cuba, « Indiana » ne donne plus l'Inde…) ;
  • sigles (US, UE, EU, UK, UAE…) reconnus uniquement en MAJUSCULES (« us » pronom anglais ignoré) ;
  • gentilés FR / EN (iranien, Iranian, nord-coréen, North Korean…) ;
  • exclusions des faux amis (« New Mexico », « latino-américain », « US Virgin Islands »…) ;
  • distinction ÉMETTEUR (UE, États-Unis, Royaume-Uni… qui prononcent la mesure) et PAYS VISÉ.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

# Pays / zones qui prononcent habituellement les mesures (ils ne sont pas la « cible » par défaut)
ISSUERS = {"US", "EU", "GB", "FR", "CA", "CH", "AU", "JP", "UN"}

# (ISO2, nom affiché en français, motifs en minuscules sans accents, sigles en majuscules)
# Les motifs sont des expressions régulières appliquées entre limites de mots.
_C = [
    # --- Émetteurs ---
    ("US", "États-Unis", [r"etats[- ]unis", r"united states", r"washington", r"maison blanche", r"white house",
                          r"(?<!latino-)(?<!latin )(?<!sud-)(?<!sud )(?<!south )(?<!centr)(?<!nord-)americain(?:e|s|es)?",
                          r"(?<!latin )(?<!south )(?<!central )(?<!north )american(?!\s+express)"],
     ["US", "U.S.", "USA", "U.S.A."]),
    ("EU", "Union européenne", [r"union europeenne", r"european union", r"bruxelles", r"brussels",
                                r"conseil de l ?ue", r"commission europeenne", r"european commission",
                                r"eu council", r"council of the eu", r"parlement europeen", r"european parliament"],
     ["UE", "EU"]),
    ("GB", "Royaume-Uni", [r"royaume[- ]uni", r"united kingdom", r"grande[- ]bretagne", r"great britain", r"britain",
                           r"british(?! virgin)", r"britannique(?:s)?(?! (?:des )?iles vierges)", r"londres", r"london"],
     ["UK", "U.K."]),
    ("FR", "France", [r"france", r"francais(?:e|es)?", r"paris", r"bercy", r"french"], []),
    ("CA", "Canada", [r"canada", r"canadien(?:ne|s|nes)?", r"canadian", r"ottawa"], []),
    ("CH", "Suisse", [r"suisse(?:s)?", r"switzerland", r"swiss"], []),
    ("UN", "ONU", [r"nations unies", r"united nations", r"conseil de securite", r"security council"], ["ONU", "UN"]),
    # --- Régimes de sanctions majeurs ---
    ("RU", "Russie", [r"russie", r"russia", r"russian(?:s)?", r"russe(?:s)?", r"moscou", r"moscow", r"kremlin"], []),
    ("UA", "Ukraine", [r"ukraine", r"ukrainien(?:ne|s|nes)?", r"ukrainian(?:s)?", r"kiev", r"kyiv", r"crimee", r"crimea"], []),
    ("BY", "Biélorussie", [r"bielorussie", r"belarus", r"bielorusse(?:s)?", r"belarusian"], []),
    ("IR", "Iran", [r"iran", r"iranien(?:ne|s|nes)?", r"iranian(?:s)?", r"teheran", r"tehran", r"irgc", r"pasdaran"], []),
    ("KP", "Corée du Nord", [r"coree du nord", r"north korea(?:n|ns)?", r"nord[- ]coreen(?:ne|s|nes)?", r"pyongyang"],
     ["DPRK", "RPDC"]),
    ("KR", "Corée du Sud", [r"coree du sud", r"south korea(?:n|ns)?", r"sud[- ]coreen(?:ne|s|nes)?", r"seoul"], []),
    ("SY", "Syrie", [r"syrie", r"syria", r"syrien(?:ne|s|nes)?", r"syrian(?:s)?", r"damas", r"damascus"], []),
    ("CU", "Cuba", [r"cuba", r"cubain(?:e|s|es)?", r"cuban(?:s)?", r"la havane", r"havana"], []),
    ("VE", "Venezuela", [r"venezuela", r"venezuelien(?:ne|s|nes)?", r"venezuelan(?:s)?", r"caracas", r"pdvsa"], []),
    ("NI", "Nicaragua", [r"nicaragua", r"nicaraguayen(?:ne|s|nes)?", r"nicaraguan(?:s)?", r"managua"], []),
    ("MM", "Myanmar", [r"myanmar", r"birmanie", r"burma", r"birman(?:e|s|es)?", r"burmese"], []),
    ("AF", "Afghanistan", [r"afghanistan", r"afghan(?:e|s|es)?", r"taliban(?:s)?", r"kaboul", r"kabul"], []),
    ("IQ", "Irak", [r"irak", r"iraq", r"irakien(?:ne|s|nes)?", r"iraqi(?:s)?", r"bagdad", r"baghdad"], []),
    ("LY", "Libye", [r"libye", r"libya", r"libyen(?:ne|s|nes)?", r"libyan(?:s)?", r"tripoli"], []),
    ("SD", "Soudan", [r"(?<!sud )soudan", r"(?<!south )sudan", r"soudanais(?:e|es)?", r"sudanese", r"khartoum", r"darfour", r"darfur"], []),
    ("SS", "Soudan du Sud", [r"soudan du sud", r"south sudan", r"sud[- ]soudanais(?:e|es)?", r"juba"], []),
    ("SO", "Somalie", [r"somalie", r"somalia", r"somalien(?:ne|s|nes)?", r"somali(?:s)?", r"shebab", r"shabaab"], []),
    ("YE", "Yémen", [r"yemen", r"yemenite(?:s)?", r"yemeni(?:s)?", r"houthi(?:s)?", r"houthistes?"], []),
    ("LB", "Liban", [r"liban", r"lebanon", r"libanais(?:e|es)?", r"lebanese", r"beyrouth", r"beirut", r"hezbollah"], []),
    ("ML", "Mali", [r"mali", r"malien(?:ne|s|nes)?", r"malian(?:s)?", r"bamako"], []),
    ("NE", "Niger", [r"niger", r"nigerien(?:ne|s|nes)?", r"niamey"], []),
    ("CF", "Centrafrique", [r"centrafrique", r"republique centrafricaine", r"central african republic", r"centrafricain(?:e|s|es)?"], ["RCA"]),
    ("CD", "RD Congo", [r"rd ?congo", r"republique democratique du congo", r"democratic republic of (?:the )?congo",
                        r"kinshasa", r"congolais(?:e|es)?"], ["RDC", "DRC"]),
    ("ZW", "Zimbabwe", [r"zimbabwe", r"zimbabween(?:ne|s|nes)?", r"zimbabwean(?:s)?", r"harare"], []),
    ("GN", "Guinée", [r"(?<!nouvelle-)(?<!new )(?<!papua new )(?<!equatoriale )guinee(?! equatoriale)(?!-bissau)",
                      r"(?<!new )(?<!equatorial )guinea(?!-bissau)", r"conakry"], []),
    ("BI", "Burundi", [r"burundi", r"burundais(?:e|es)?"], []),
    ("MD", "Moldavie", [r"moldavie", r"moldova", r"moldave(?:s)?", r"chisinau"], []),
    ("GE", "Géorgie", [r"georgie(?! du sud)", r"tbilissi", r"tbilisi"], []),
    ("AM", "Arménie", [r"armenie", r"armenia", r"armenien(?:ne|s|nes)?", r"armenian(?:s)?"], []),
    ("AZ", "Azerbaïdjan", [r"azerbaidjan", r"azerbaijan"], []),
    ("KZ", "Kazakhstan", [r"kazakhstan"], []),
    ("KG", "Kirghizistan", [r"kirghizistan", r"kyrgyzstan", r"kyrgyz"], []),
    ("UZ", "Ouzbékistan", [r"ouzbekistan", r"uzbekistan"], []),
    # --- Asie / Moyen-Orient ---
    ("CN", "Chine", [r"chine", r"china", r"chinese", r"chinois(?:e|es)?", r"pekin", r"beijing"], []),
    ("HK", "Hong Kong", [r"hong[- ]kong"], []),
    ("TW", "Taïwan", [r"taiwan", r"taiwanais(?:e|es)?", r"taiwanese"], []),
    ("IN", "Inde", [r"inde", r"india", r"indien(?:ne|s|nes)?", r"indian(?! ocean)", r"new delhi"], []),
    ("PK", "Pakistan", [r"pakistan", r"pakistanais(?:e|es)?", r"pakistani(?:s)?"], []),
    ("AE", "Émirats arabes unis", [r"emirats(?: arabes unis)?", r"emirates", r"emirati(?:s)?", r"dubai", r"abou dhabi", r"abu dhabi"], ["UAE", "EAU"]),
    ("SA", "Arabie saoudite", [r"arabie saoudite", r"saudi(?: arabia)?", r"saoudien(?:ne|s|nes)?", r"riyad", r"riyadh"], []),
    ("QA", "Qatar", [r"qatar", r"qatari(?:e|s|es)?", r"doha"], []),
    ("TR", "Turquie", [r"turquie", r"turkey", r"turkiye", r"turc(?:s)?", r"turque(?:s)?", r"turkish", r"ankara", r"istanbul"], []),
    ("IL", "Israël", [r"israel", r"israelien(?:ne|s|nes)?", r"israeli(?:s)?", r"tel[- ]aviv"], []),
    ("PS", "Palestine", [r"palestine", r"palestinien(?:ne|s|nes)?", r"palestinian(?:s)?", r"gaza", r"cisjordanie", r"west bank", r"hamas"], []),
    ("VN", "Vietnam", [r"vietnam", r"viet nam", r"vietnamien(?:ne|s|nes)?", r"vietnamese", r"hanoi"], []),
    ("LA", "Laos", [r"laos", r"laotien(?:ne|s|nes)?", r"lao pdr"], []),
    ("KH", "Cambodge", [r"cambodge", r"cambodia", r"cambodgien(?:ne|s|nes)?", r"cambodian"], []),
    ("PH", "Philippines", [r"philippines", r"philippin(?:e|s|es)?", r"filipino(?:s)?"], []),
    ("NP", "Népal", [r"nepal"], []),
    ("SG", "Singapour", [r"singapour", r"singapore"], []),
    ("JP", "Japon", [r"japon", r"japan", r"japonais(?:e|es)?", r"japanese", r"tokyo"], []),
    # --- Afrique ---
    ("NG", "Nigeria", [r"nigeria", r"nigerian(?:e|s|es)?", r"abuja", r"lagos"], []),
    ("ZA", "Afrique du Sud", [r"afrique du sud", r"south africa(?:n|ns)?", r"sud[- ]africain(?:e|s|es)?"], []),
    ("KE", "Kenya", [r"kenya", r"kenyan(?:e|s|es)?", r"nairobi"], []),
    ("CM", "Cameroun", [r"cameroun", r"cameroon", r"camerounais(?:e|es)?"], []),
    ("AO", "Angola", [r"angola", r"angolais(?:e|es)?", r"angolan(?:s)?"], []),
    ("SN", "Sénégal", [r"senegal", r"senegalais(?:e|es)?"], []),
    ("CI", "Côte d'Ivoire", [r"cote d ?ivoire", r"ivory coast", r"ivoirien(?:ne|s|nes)?", r"abidjan"], []),
    ("MA", "Maroc", [r"maroc", r"morocco", r"marocain(?:e|s|es)?", r"moroccan"], []),
    ("DZ", "Algérie", [r"algerie", r"algeria", r"algerien(?:ne|s|nes)?", r"algerian"], []),
    ("TN", "Tunisie", [r"tunisie", r"tunisia", r"tunisien(?:ne|s|nes)?", r"tunisian"], []),
    ("EG", "Égypte", [r"egypte", r"egypt", r"egyptien(?:ne|s|nes)?", r"egyptian"], []),
    ("ET", "Éthiopie", [r"ethiopie", r"ethiopia", r"ethiopien(?:ne|s|nes)?", r"ethiopian"], []),
    # --- Europe ---
    ("DE", "Allemagne", [r"allemagne", r"germany", r"allemand(?:e|s|es)?", r"german(?!ium)", r"berlin", r"bafin"], []),
    ("IT", "Italie", [r"italie", r"italy", r"italien(?:ne|s|nes)?", r"italian"], []),
    ("ES", "Espagne", [r"espagne", r"spain", r"espagnol(?:e|s|es)?", r"spanish", r"madrid"], []),
    ("NL", "Pays-Bas", [r"pays[- ]bas", r"netherlands", r"neerlandais(?:e|es)?", r"dutch", r"amsterdam"], []),
    ("BE", "Belgique", [r"belgique", r"belgium", r"belge(?:s)?", r"belgian"], []),
    ("LU", "Luxembourg", [r"luxembourg"], []),
    ("MC", "Monaco", [r"monaco", r"monegasque(?:s)?"], []),
    ("MT", "Malte", [r"malte", r"malta", r"maltais(?:e|es)?", r"maltese"], []),
    ("CY", "Chypre", [r"chypre", r"cyprus", r"chypriote(?:s)?", r"cypriot"], []),
    ("BG", "Bulgarie", [r"bulgarie", r"bulgaria"], []),
    ("RS", "Serbie", [r"serbie", r"serbia", r"serbe(?:s)?", r"serbian"], []),
    ("BA", "Bosnie-Herzégovine", [r"bosnie", r"bosnia"], []),
    ("PL", "Pologne", [r"pologne", r"poland", r"polonais(?:e|es)?", r"polish"], []),
    ("HU", "Hongrie", [r"hongrie", r"hungary", r"hongrois(?:e|es)?", r"hungarian"], []),
    ("EE", "Estonie", [r"estonie", r"estonia"], []),
    ("LV", "Lettonie", [r"lettonie", r"latvia"], []),
    ("LT", "Lituanie", [r"lituanie", r"lithuania"], []),
    ("FI", "Finlande", [r"finlande", r"finland"], []),
    ("NO", "Norvège", [r"norvege", r"norway"], []),
    ("SE", "Suède", [r"suede", r"sweden", r"swedish"], []),
    ("DK", "Danemark", [r"danemark", r"denmark", r"danish"], []),
    ("IE", "Irlande", [r"irlande", r"ireland", r"irish"], []),
    ("PT", "Portugal", [r"portugal", r"portugais(?:e|es)?", r"portuguese"], []),
    ("GR", "Grèce", [r"grece", r"greece", r"grec(?:s)?", r"grecque(?:s)?", r"greek"], []),
    # --- Amériques & Caraïbes ---
    ("HT", "Haïti", [r"haiti", r"haitien(?:ne|s|nes)?", r"haitian(?:s)?", r"port-au-prince", r"port au prince",
                     r"viv ansanm", r"gran grif"], []),
    ("DO", "République dominicaine", [r"republique dominicaine", r"dominican republic", r"saint-domingue", r"santo domingo"], []),
    ("JM", "Jamaïque", [r"jamaique", r"jamaica(?! plain)", r"jamaicain(?:e|s|es)?", r"jamaican"], []),
    ("TT", "Trinité-et-Tobago", [r"trinite[- ]et[- ]tobago", r"trinidad(?: and tobago)?"], []),
    ("BS", "Bahamas", [r"bahamas"], []),
    ("BB", "Barbade", [r"barbade", r"barbados"], []),
    ("KY", "Îles Caïmans", [r"iles? caimans?", r"cayman islands?"], []),
    ("VG", "Îles Vierges britanniques", [r"iles vierges britanniques", r"british virgin islands", r"bvi"], ["BVI"]),
    ("VI", "Îles Vierges américaines", [r"iles vierges (?:des etats-unis|americaines)", r"u\.?s\.? virgin islands"], ["USVI"]),
    ("PA", "Panama", [r"panama(?! papers)", r"panameen(?:ne|s|nes)?", r"panamanian"], []),
    ("MX", "Mexique", [r"mexique", r"(?<!new )mexico(?! city)", r"mexicain(?:e|s|es)?", r"mexican(?:s)?", r"sinaloa", r"jalisco"], []),
    ("GT", "Guatemala", [r"guatemala", r"guatemalteque(?:s)?", r"guatemalan(?:s)?"], []),
    ("HN", "Honduras", [r"honduras", r"hondurien(?:ne|s|nes)?", r"honduran(?:s)?", r"tegucigalpa"], []),
    ("SV", "Salvador", [r"el salvador", r"(?<=au )salvador", r"(?<=du )salvador", r"(?<=le )salvador",
                        r"salvadorien(?:ne|s|nes)?", r"salvadoran(?:s)?"], []),
    ("CO", "Colombie", [r"colombie", r"colombia(?!n university)", r"colombien(?:ne|s|nes)?", r"colombian(?:s)?", r"bogota"], []),
    ("BO", "Bolivie", [r"bolivie", r"bolivia", r"bolivien(?:ne|s|nes)?", r"bolivian(?:s)?", r"la paz"], []),
    ("PE", "Pérou", [r"perou", r"peru", r"peruvien(?:ne|s|nes)?", r"peruvian"], []),
    ("EC", "Équateur", [r"equateur", r"ecuador"], []),
    ("BR", "Brésil", [r"bresil", r"brazil", r"bresilien(?:ne|s|nes)?", r"brazilian"], []),
    ("AR", "Argentine", [r"argentine", r"argentina", r"argentin(?:e|s|es)?"], []),
    ("GY", "Guyana", [r"guyana"], []),
    ("SR", "Suriname", [r"suriname"], []),
]

COUNTRIES = [(c, n) for c, n, _, _ in _C]
NAME = {c: n for c, n, _, _ in _C}


def norm(s: str) -> str:
    """Minuscules, sans accents, apostrophes et ponctuation normalisées (les traits d'union sont gardés)."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^a-z0-9'\-.]+", " ", s)
    s = re.sub(r"(?<![a-z])'|'(?![a-z])", " ", s)
    s = s.replace("'", " ")
    s = re.sub(r"(?<![a-z])\.|\.(?![a-z])", " ", s)  # points de fin de phrase, garde « u.s. »
    return " " + re.sub(r"\s+", " ", s).strip() + " "


@lru_cache(maxsize=1)
def _compiled():
    out = []
    for code, _name, pats, acr in _C:
        rx = re.compile(r"(?<![a-z0-9-])(?:" + "|".join(pats) + r")(?![a-z0-9])") if pats else None
        rx_a = re.compile(r"(?<![A-Za-z0-9.])(?:" + "|".join(re.escape(a) for a in acr) + r")(?![A-Za-z0-9])") if acr else None
        out.append((code, rx, rx_a))
    return out


def mentions(text: str) -> list[tuple[int, str]]:
    """Toutes les mentions de pays : [(position relative 0–1, code ISO2)], triées par ordre d'apparition.
    La position est relative pour pouvoir comparer texte normalisé et texte original."""
    raw = str(text or "")
    n = norm(raw)
    found: dict[str, float] = {}
    for code, rx, rx_a in _compiled():
        best = None
        if rx:
            m = rx.search(n)
            if m:
                best = m.start() / max(len(n), 1)
        if rx_a:
            m = rx_a.search(raw)
            if m:
                p = m.start() / max(len(raw), 1)
                best = p if best is None else min(best, p)
        if best is not None:
            found[code] = best
    # « Soudan du Sud » contient « Soudan » : on ne garde que le plus précis
    if "SS" in found:
        found.pop("SD", None)
    if "VI" in found:
        found.pop("US", None)
    return sorted(((p, c) for c, p in found.items()), key=lambda x: x[0])


_TARGET_RX = re.compile(
    r"(?:contre|visant|vise|cible|ciblant|a l encontre d(?:e|u|es)|against|on|targeting|targets|target|sanctionne(?:nt)?|"
    r"sanctions?|frappe(?:nt)?|hits?|blacklists?|designates?|designe(?:nt)?)\s+"
    r"(?:[\w-]+\s+){0,4}$")


def target_country(headline: str) -> str:
    """Pays VISÉ (« sanctions contre la Russie », « sanctions on Iran's… », « sanctionne des Iraniens »).
    En cas de plusieurs candidats, le premier dans le titre l'emporte."""
    n = norm(headline)
    subject = _subject(headline)
    hits = []
    raw = str(headline or "")
    for code, rx, rx_a in _compiled():
        if code == "UN" or code == subject:
            continue
        for m in (rx.finditer(n) if rx else []):
            if _TARGET_RX.search(n[max(0, m.start() - 60):m.start()]):
                hits.append((code in ISSUERS, m.start() / max(len(n), 1), code))   # un pays tiers prime sur un émetteur
                break
        for m in (rx_a.finditer(raw) if rx_a else []):           # sigles : US, UE, UK…
            if _TARGET_RX.search(norm(raw[max(0, m.start() - 60):m.start()]).rstrip() + " "):
                hits.append((code in ISSUERS, m.start() / max(len(raw), 1), code))
                break
    return min(hits)[2] if hits else ""


_SUBJECT_VERB = re.compile(r"^\s*(?:la |le |les |l )?(?P<c>[a-z\- ]{2,30}?)\s+(?:imposes?|impose|sanctions|sanctionne(?:nt)?|"
                           r"adopts?|adopte(?:nt)?|bans?|interdit|blacklists?|designates?|designe(?:nt)?|freezes?|gele(?:nt)?|"
                           r"announces?|annonce(?:nt)?|retaliates?|riposte)\b")


def _subject(headline: str) -> str:
    """Pays SUJET du verbe en tête de titre (« Russia imposes sanctions on… ») : c'est l'émetteur, pas la cible."""
    m = _SUBJECT_VERB.match(norm(headline))
    if not m:
        return ""
    c = country_by_name(m.group("c").strip())
    return c[0] if c else ""


def country_of(headline: str, desc: str = "", measure_kind: str = "", authorities: str = "") -> tuple[str, str]:
    """(ISO2, nom FR) du pays à afficher pour une actualité.

    • mesure restrictive (sanction, gel, embargo, liste GAFI) → le pays VISÉ :
      préposition explicite, sinon premier pays non émetteur du titre, puis du résumé ; à défaut « — »
      (l'émetteur figure déjà dans la colonne Autorité : l'afficher comme pays induirait en erreur) ;
    • autre actualité (amende, enquête, réglementation) → la juridiction : premier pays du titre,
      sinon celui de l'autorité citée (ACPR → France, OFAC → États-Unis…), sinon du résumé.
    """
    restrictive = measure_kind in ("gel", "liste", "sanction", "embargo")
    if restrictive:
        t = target_country(headline)
        if t:
            return t, NAME[t]
    subject = _subject(headline) if restrictive else ""
    head = [c for _, c in mentions(headline) if c not in ("UN", subject)]
    body = [c for _, c in mentions(desc) if c not in ("UN", subject)]
    if restrictive:
        for pool in (head, body):
            third = [c for c in pool if c not in ISSUERS]
            if third:
                pick = next((c for c in third if c != "UA"), third[0]) if len(third) > 1 else third[0]
                return pick, NAME[pick]
        return "", "—"
    if head:
        return head[0], NAME[head[0]]
    a = authority_country(authorities)
    if a:
        return a, NAME[a]
    if body:
        return body[0], NAME[body[0]]
    return "", "—"


AUTHORITY_COUNTRY = {
    "OFAC": "US", "Trésor US": "US", "FinCEN": "US", "SEC": "US", "DOJ": "US", "BIS": "US",
    "OFSI": "GB", "FCA": "GB", "ACPR": "FR", "AMF": "FR", "Tracfin": "FR", "AFA": "FR", "PNF": "FR",
    "FINMA": "CH", "BaFin": "DE", "Conseil de l'UE": "EU", "AMLA": "EU", "EBA": "EU", "ESMA": "EU", "BCE": "EU",
}


def authority_country(authorities: str) -> str:
    for a in [x.strip() for x in str(authorities or "").split(",") if x.strip()]:
        if a in AUTHORITY_COUNTRY:
            return AUTHORITY_COUNTRY[a]
    return ""


def country_by_name(word: str) -> tuple[str, str] | None:
    """Si `word` désigne exactement un pays (« Russia », « Iranian », « UK »), renvoie (ISO2, nom FR).
    « Bank of Russia » ou « Russian Railways » ne sont PAS des pays : renvoie None."""
    w = str(word or "").strip()
    if not w:
        return None
    n = norm(w).strip()
    for code, rx, rx_a in _compiled():
        if (rx and rx.fullmatch(n)) or (rx_a and rx_a.fullmatch(w)):
            return code, NAME[code]
    return None


def all_country_tokens() -> set[str]:
    """Mots désignant des pays (pour les exclure de l'extraction d'entité)."""
    toks = set()
    for _c, name, pats, acr in _C:
        toks |= set(norm(name).split())
        for p in pats:
            toks |= {w for w in re.findall(r"[a-z]{3,}", p)}
        toks |= {a.lower().strip(".") for a in acr}
    return toks
