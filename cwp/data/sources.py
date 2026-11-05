"""
cwp.data.sources — connecteurs vers les bases de données publiques ouvertes.

Chaque fonction `enrichir_*` télécharge la source, la normalise et la fusionne dans
le CSV correspondant (data/*.csv) via store.upsert : un clic = un enrichissement.

Listes de sanctions (fichier complet → les entrées disparues passent au statut « retiré ») :
  OFAC SDN · liste consolidée UE (FSF) · liste consolidée ONU · UK Sanctions List · gels DG Trésor
Référentiels :  Banque mondiale (WGI, PIB/hab.) · listes GAFI
À la demande (par entité / pays / ville) :
  GLEIF (LEI) · Recherche d'entreprises (SIRENE/RNE) · Wikidata (PPE) · GDELT (presse négative)
  OpenStreetMap : Nominatim (géocodage) · Overpass (points d'intérêt à risque)
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import requests

from . import store
from .countries import GAFI_DATE, GAFI_GRISE, GAFI_NOIRE, REGIMES_SANCTIONS, nom, ref, to_iso2

UA = "CWP-Compliance-Watch-Platform/2.0 (veille conformite LCB-FT; usage professionnel)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})


class SourceError(RuntimeError):
    pass


def _get(urls, timeout=90, **kw) -> requests.Response:
    """GET avec plusieurs URL de repli."""
    urls = [urls] if isinstance(urls, str) else urls
    last = None
    for u in urls:
        try:
            r = S.get(u, timeout=timeout, **kw)
            if r.ok and r.content:
                return r
            last = f"HTTP {r.status_code} sur {u}"
        except Exception as e:  # réseau, TLS, délai…
            last = f"{type(e).__name__} sur {u} : {e}"
    raise SourceError(last or "source injoignable")


def _uid(*parts) -> str:
    return hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def _j(values) -> str:
    """Joint des valeurs uniques non vides avec « | »."""
    out, seen = [], set()
    for v in values:
        v = re.sub(r"\s+", " ", str(v or "")).strip(" ,;")
        if v and v.lower() not in ("-0-", "nan", "none") and v.lower() not in seen:
            seen.add(v.lower()); out.append(v)
    return " | ".join(out)


def _countries(values) -> str:
    return _j(to_iso2(v) or "" for v in values)


# pays        = pays PROPRES à la personne / entité (nationalité, adresse, pavillon) — sert au filtrage nominatif
# pays_regime = pays VISÉ par le régime de sanctions (programme OFAC, régime UE / UK / ONU) — sert aux statistiques
SANCTION_COLS = ["uid", "liste", "ref", "nom", "type", "programme", "pays", "pays_regime", "alias", "adresse",
                 "date_naissance", "date_inscription", "remarques"]


def _run(name: str, fn, source: str, snapshot=True) -> dict:
    try:
        df = fn()
    except Exception as e:
        store.log(name, "échec", {}, source, erreur=str(e)[:300])
        raise
    return store.upsert(name, df, snapshot=snapshot, source=source)


# =========================================================================== #
# 1. OFAC — SDN (CSV officiels : SDN, ADD adresses, ALT alias)
# =========================================================================== #
OFAC_BASE = ["https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/{}",
             "https://www.treasury.gov/ofac/downloads/{}"]


def parse_ofac(sdn: bytes, add: bytes | None = None, alt: bytes | None = None) -> pd.DataFrame:
    rd = lambda b, n: pd.read_csv(io.BytesIO(b), header=None, dtype=str, keep_default_na=False,
                                  encoding="latin-1", on_bad_lines="skip", names=range(n))
    sd = rd(sdn, 12)
    sd = sd[sd[0].str.strip().str.isdigit()]
    sd.columns = ["ent", "nom", "type", "programme", "titre", "call", "vtype", "tonnage", "grt", "vflag",
                  "vowner", "remarques"]
    addr = {}
    if add:
        a = rd(add, 6); a.columns = ["ent", "n", "adresse", "ville", "pays", "rem"]
        for ent, g in a.groupby("ent"):
            addr[ent.strip()] = (_j(", ".join(x for x in (r.adresse, r.ville, r.pays) if x and x != "-0-")
                                    for r in g.itertuples()), [r.pays for r in g.itertuples()])
    alias = {}
    if alt:
        l = rd(alt, 5); l.columns = ["ent", "n", "atype", "nom", "rem"]
        alias = l.groupby(l.ent.str.strip()).nom.apply(_j).to_dict()
    tmap = {"individual": "Personne", "vessel": "Navire", "aircraft": "Aéronef", "-0-": "Entité", "": "Entité"}
    rows = []
    for r in sd.itertuples():
        ent = r.ent.strip()
        rem = r.remarques if r.remarques != "-0-" else ""
        nat = re.findall(r"(?:nationality|citizen|Nationality)\s+([A-Z][\w ,'-]+?)(?:;|\.|$)", rem)
        dob = re.search(r"DOB ([\w ]+?\d{4})", rem)
        adr, pays_adr = addr.get(ent, ("", []))
        rows.append(dict(
            uid=f"OFAC-{ent}", liste="OFAC SDN", ref=ent, nom=r.nom.strip(),
            type=tmap.get(r.type.strip().lower(), "Entité"), programme=_j(re.split(r"[\[\]]", r.programme)),
            pays=_countries(list(pays_adr) + nat + ([r.vflag] if r.vflag != "-0-" else [])),
            pays_regime=_j(_prog_countries(r.programme)),
            alias=alias.get(ent, ""), adresse=adr, date_naissance=dob.group(1) if dob else "",
            date_inscription="", remarques=rem[:500]))
    return pd.DataFrame(rows, columns=SANCTION_COLS)


# Programme OFAC -> pays visé. Les programmes « UKRAINE-EO13661/13662 » visent la RUSSIE (responsables et secteurs
# russes) : les rattacher à l'Ukraine faisait apparaître l'Ukraine comme pays massivement sanctionné.
PROG_COUNTRY = {"CUBA": "CU", "IRAN": "IR", "IRGC": "IR", "IFSR": "IR", "IFCA": "IR", "ISA": "IR", "RUSSIA": "RU",
                "SYRIA": "SY", "VENEZUELA": "VE", "DPRK": "KP", "DPRK2": "KP", "DPRK3": "KP", "DPRK4": "KP",
                "NKSPEA": "KP", "HAITI": "HT", "BELARUS": "BY", "BURMA": "MM", "NICARAGUA": "NI", "IRAQ": "IQ",
                "IRAQ2": "IQ", "IRAQ3": "IQ", "LIBYA": "LY", "LIBYA2": "LY", "LIBYA3": "LY", "SUDAN": "SD",
                "DARFUR": "SD", "SOUTH SUDAN": "SS", "SOMALIA": "SO", "YEMEN": "YE", "ZIMBABWE": "ZW", "MALI": "ML",
                "CAR": "CF", "DRCONGO": "CD", "LEBANON": "LB", "ETHIOPIA": "ET", "HK": "HK", "BURUNDI": "BI",
                "AFGHANISTAN": "AF", "WEST BANK": "PS"}
PROG_EXACT = {"UKRAINE-EO13661": "RU", "UKRAINE-EO13662": "RU", "UKRAINE-EO13685": "UA",   # EO 13685 : Crimée
              "UKRAINE-EO13660": "", "CAATSA - RUSSIA": "RU", "CAATSA - IRAN": "IR", "HRIT-IR": "IR", "HRIT-SY": "SY",
              "SYRIA-EO13894": "", "BALKANS": "", "BALKANS-EO14033": ""}      # multi-pays : pas de pays unique


def _prog_countries(prog: str) -> list[str]:
    out = []
    for t in re.split(r"[\[\]]+", prog or ""):
        t = t.strip().upper()
        if not t:
            continue
        out.append(PROG_EXACT[t] if t in PROG_EXACT else PROG_COUNTRY.get(t.split("-")[0].strip(), ""))
    return out


# Codes de régime UE / libellés UK-ONU-FR qui ne désignent pas le pays visé
REGIME_OVERRIDE = {"UKR": "RU",   # régime UE « intégrité territoriale de l'Ukraine » : vise surtout des Russes
                   "UKRAINE": "RU", "CRIMEA": "UA"}


def _regime_countries(programme: str) -> str:
    """Pays visé(s) par un régime à partir de son code (UE : ISO3) ou de son libellé (UK, ONU, DG Trésor)."""
    from cwp.core import geo
    txt = str(programme or "")
    out = []
    for code in re.findall(r"\b[A-Z]{3}\b", txt):
        if code in REGIME_OVERRIDE:
            out.append(REGIME_OVERRIDE[code])
            continue
        try:
            m = ref()[lambda d: d.iso3 == code]
            if len(m):
                out.append(m.iso2.iloc[0])
        except Exception:
            pass
    low = txt.lower()
    if "ukrain" in low and ("russ" in low or "territorial" in low or "intégrité" in low):
        out.append("RU")
    out += [c for _, c in geo.mentions(txt) if c not in ("UN", "EU", "UA") or (c == "UA" and "crim" in low)]
    return _j(out)


def fetch_ofac() -> pd.DataFrame:
    get = lambda f: _get([b.format(f) for b in OFAC_BASE]).content
    sdn = get("SDN.CSV")
    try: add = get("ADD.CSV")
    except SourceError: add = None
    try: alt = get("ALT.CSV")
    except SourceError: alt = None
    return parse_ofac(sdn, add, alt)


def enrichir_ofac():
    return _run("sanctions_ofac", fetch_ofac, "OFAC – Trésor américain")


# =========================================================================== #
# 2. UE — liste consolidée des sanctions financières (FSF)
# =========================================================================== #
EU_URLS = ["https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
           "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList/content?token=dG9rZW4tMjAxNw"]


def _col(df, *cands):
    low = {c.lower(): c for c in df.columns}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    for c in cands:  # recherche partielle
        for lc, orig in low.items():
            if c.lower() in lc:
                return orig
    return None


def parse_ue(raw: bytes) -> pd.DataFrame:
    txt = raw.decode("utf-8-sig", errors="replace")
    sep = ";" if txt[:2000].count(";") > txt[:2000].count(",") else ","
    df = pd.read_csv(io.StringIO(txt), sep=sep, dtype=str, keep_default_na=False, on_bad_lines="skip")
    c_id = _col(df, "Entity_LogicalId", "Entity_logical_id")
    c_nm = _col(df, "NameAlias_WholeName", "Naal_wholename")
    c_tp = _col(df, "Entity_SubjectType_ClassificationCode", "Entity_SubjectType", "Subject_type")
    c_pg = _col(df, "Entity_Regulation_Programme", "Programme")
    c_dt = _col(df, "Entity_Regulation_PublicationDate", "Leba_publication_date", "Entity_DesignationDate")
    c_ref = _col(df, "Entity_EU_ReferenceNumber", "Entity_reference")
    c_ci = _col(df, "Citizenship_CountryIso2Code", "Citizenship_CountryDescription", "Citi_country")
    c_ac = _col(df, "Address_CountryIso2Code", "Address_CountryDescription", "Addr_country")
    c_ad = [c for c in (_col(df, "Address_Street"), _col(df, "Address_City")) if c]
    c_bd = _col(df, "BirthDate_BirthDate", "Birt_date")
    c_rm = _col(df, "Entity_Remark", "Entity_DesignationDetails")
    if not c_id or not c_nm:
        raise SourceError("format UE inattendu : colonnes Entity_LogicalId / NameAlias_WholeName introuvables")
    tmap = {"person": "Personne", "p": "Personne", "enterprise": "Entité", "e": "Entité"}
    rows = []
    for ent, g in df.groupby(c_id):
        names = [n for n in g[c_nm] if n]
        if not names:
            continue
        dates = sorted(d for d in (g[c_dt] if c_dt else []) if d)
        tp = (g[c_tp].iloc[0] if c_tp else "").strip().lower()
        rows.append(dict(
            uid=f"UE-{ent}", liste="UE consolidée", ref=(g[c_ref].iloc[0] if c_ref else ent) or ent,
            nom=names[0], type=tmap.get(tp, "Entité" if "enterprise" in tp else "Personne" if "person" in tp else "Entité"),
            programme=_j(g[c_pg]) if c_pg else "",
            pays=_countries(list(g[c_ci] if c_ci else []) + list(g[c_ac] if c_ac else [])),
            pays_regime=_regime_countries(_j(g[c_pg]) if c_pg else ""),
            alias=_j(names[1:])[:1500], adresse=_j(", ".join(x for x in row if x) for row in g[c_ad].values)[:500] if c_ad else "",
            date_naissance=_j(g[c_bd]) if c_bd else "", date_inscription=dates[0][:10] if dates else "",
            remarques=(g[c_rm].iloc[0] if c_rm else "")[:500]))
    return pd.DataFrame(rows, columns=SANCTION_COLS)


def enrichir_ue():
    return _run("sanctions_ue", lambda: parse_ue(_get(EU_URLS).content), "Commission européenne (FSF)")


# =========================================================================== #
# 3. ONU — liste consolidée du Conseil de sécurité (XML)
# =========================================================================== #
UN_URLS = ["https://scsanctions.un.org/resources/xml/en/consolidated.xml",
           "https://scsanctions.un.org/resources/xml/fr/consolidated.xml"]


def parse_onu(raw: bytes) -> pd.DataFrame:
    root = ET.fromstring(raw)
    t = lambda e, tag: (e.findtext(tag) or "").strip()
    rows = []
    for kind, tag, atag, adtag in (("Personne", "INDIVIDUAL", "INDIVIDUAL_ALIAS", "INDIVIDUAL_ADDRESS"),
                                   ("Entité", "ENTITY", "ENTITY_ALIAS", "ENTITY_ADDRESS")):
        for e in root.iter(tag):
            name = " ".join(x for x in (t(e, "FIRST_NAME"), t(e, "SECOND_NAME"), t(e, "THIRD_NAME"),
                                        t(e, "FOURTH_NAME")) if x)
            if not name:
                continue
            nats = [v.text for n in e.findall("NATIONALITY") for v in n.findall("VALUE") if v.text]
            adr = e.findall(adtag)
            ctry = [a.findtext("COUNTRY") for a in adr]
            dob = [d.findtext("DATE") or d.findtext("YEAR") for d in e.findall("INDIVIDUAL_DATE_OF_BIRTH")]
            rows.append(dict(
                uid=f"ONU-{t(e, 'DATAID') or _uid(name)}", liste="ONU consolidée", ref=t(e, "REFERENCE_NUMBER"),
                nom=name, type=kind, programme=t(e, "UN_LIST_TYPE"), pays=_countries(nats + ctry),
                pays_regime=_regime_countries(t(e, "UN_LIST_TYPE")),
                alias=_j(a.findtext("ALIAS_NAME") for a in e.findall(atag)),
                adresse=_j(", ".join(x for x in (a.findtext("STREET"), a.findtext("CITY"), a.findtext("COUNTRY")) if x)
                           for a in adr)[:500],
                date_naissance=_j(dob), date_inscription=t(e, "LISTED_ON")[:10], remarques=t(e, "COMMENTS1")[:500]))
    return pd.DataFrame(rows, columns=SANCTION_COLS)


def enrichir_onu():
    return _run("sanctions_onu", lambda: parse_onu(_get(UN_URLS).content), "Conseil de sécurité des Nations unies")


# =========================================================================== #
# 4. Royaume-Uni — UK Sanctions List (FCDO, liste unique depuis le 28/01/2026)
# =========================================================================== #
UK_URLS = ["https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv"]


def parse_uk(raw: bytes) -> pd.DataFrame:
    txt = raw.decode("utf-8-sig", errors="replace")
    lines = txt.splitlines()
    hdr = next((i for i, l in enumerate(lines[:30]) if re.search(r"unique id|name 6|group id", l, re.I)), 0)
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), dtype=str, keep_default_na=False, on_bad_lines="skip")
    c_id = _col(df, "Unique ID", "Group ID", "OFSI Group ID")
    if not c_id:
        raise SourceError("format UK inattendu : colonne Unique ID introuvable")
    name_cols = [c for c in (_col(df, f"Name {i}") for i in (1, 2, 3, 4, 5, 6)) if c]
    c_full = _col(df, "Primary name", "Name")
    c_nt = _col(df, "Name type", "Alias type")
    c_rg = _col(df, "Regime Name", "Regime")
    c_tp = _col(df, "Designation Type", "Entity Type", "Group Type")
    c_dd = _col(df, "Date Designated", "Listed On", "Designated")
    c_nat = _col(df, "Nationality", "Nationality(/ies)")
    c_ac = _col(df, "Address Country", "Country")
    c_dob = _col(df, "D.O.B", "Date of birth", "DOB")
    c_oi = _col(df, "Other Information", "UK Statement of Reasons")

    def fullname(r):
        if name_cols:
            n6 = r.get(_col(df, "Name 6") or "", "")
            first = " ".join(r[c] for c in name_cols if c != _col(df, "Name 6") and r[c])
            return " ".join(x for x in (first, n6) if x).strip()
        return r.get(c_full, "")

    rows = []
    for gid, g in df.groupby(c_id):
        recs = g.to_dict("records")
        names = [fullname(r) for r in recs]
        prim = [n for r, n in zip(recs, names) if c_nt and "primary" in str(r.get(c_nt, "")).lower()] or names
        if not prim or not prim[0]:
            continue
        tp = str(recs[0].get(c_tp, "") if c_tp else "").lower()
        rows.append(dict(
            uid=f"UK-{gid}", liste="UK Sanctions List", ref=gid, nom=prim[0],
            type="Personne" if "individual" in tp else "Navire" if "ship" in tp else "Entité",
            programme=_j(g[c_rg]) if c_rg else "",
            pays=_countries(list(g[c_nat] if c_nat else []) + list(g[c_ac] if c_ac else [])),
            pays_regime=_regime_countries(_j(g[c_rg]) if c_rg else ""),
            alias=_j(n for n in names if n != prim[0])[:1500], adresse="",
            date_naissance=_j(g[c_dob]) if c_dob else "",
            date_inscription=_to_iso(recs[0].get(c_dd, "")) if c_dd else "",
            remarques=str(recs[0].get(c_oi, "") if c_oi else "")[:500]))
    return pd.DataFrame(rows, columns=SANCTION_COLS)


def _to_iso(d: str) -> str:
    d = str(d or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %B %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(d[:10] if fmt.startswith("%Y-") else d, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return d[:10]


def enrichir_uk():
    return _run("sanctions_uk", lambda: parse_uk(_get(UK_URLS).content), "FCDO – Royaume-Uni")


# =========================================================================== #
# 5. France — Registre national des gels (DG Trésor)
# =========================================================================== #
FR_URLS = ["https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-fichier-json"]


def parse_gels(raw: bytes) -> pd.DataFrame:
    data = json.loads(raw.decode("utf-8-sig"))
    pub = data.get("Publications", data)
    details = pub.get("PublicationDetail") or pub.get("publicationDetail") or []
    rows = []
    for d in details:
        champs = {}
        for c in d.get("RegistreDetail", []) or []:
            champs.setdefault(c.get("TypeChamp", ""), []).extend(c.get("Valeur", []) or [])

        def vals(champ, *keys):
            out = []
            for v in champs.get(champ, []):
                if isinstance(v, dict):
                    out.append(" ".join(str(v.get(k, "")) for k in keys if v.get(k)) or
                               " ".join(str(x) for x in v.values() if isinstance(x, (str, int))))
                else:
                    out.append(str(v))
            return out
        prenom = " ".join(vals("PRENOM", "Prenom"))
        name = " ".join(x for x in (prenom, d.get("Nom", "")) if x).strip()
        nature = str(d.get("Nature", "")).lower()
        dob = vals("DATE_DE_NAISSANCE", "Jour", "Mois", "Annee")
        rows.append(dict(
            uid=f"FR-{d.get('IdRegistre', _uid(name))}", liste="Gels DG Trésor", ref=str(d.get("IdRegistre", "")),
            nom=name, type="Personne" if "physique" in nature else "Navire" if "navire" in nature else "Entité",
            programme=_j(vals("REGIME", "Valeur") + vals("FONDEMENT_JURIDIQUE", "FondementJuridiqueLabel"))[:400],
            pays_regime=_regime_countries(_j(vals("REGIME", "Valeur") + vals("FONDEMENT_JURIDIQUE", "FondementJuridiqueLabel"))),
            pays=_countries(vals("NATIONALITE", "Pays") + vals("ADRESSE_PM", "Pays") + vals("ADRESSE_PP", "Pays")),
            alias=_j(vals("ALIAS", "Alias")), adresse=_j(vals("ADRESSE_PM", "Adresse", "Pays") + vals("ADRESSE_PP", "Adresse", "Pays"))[:500],
            date_naissance=_j(dob), date_inscription=_to_iso(_j(vals("DATE_DE_DESIGNATION", "Date"))[:10]),
            remarques=_j(vals("MOTIFS", "Motifs") + vals("AUTRE_INFORMATION", "AutreInformation"))[:500]))
    return pd.DataFrame(rows, columns=SANCTION_COLS)


def enrichir_gels_fr():
    return _run("gels_avoirs_fr", lambda: parse_gels(_get(FR_URLS).content), "DG Trésor")


SANCTION_SOURCES = {
    "sanctions_ofac": ("OFAC SDN", enrichir_ofac),
    "sanctions_ue": ("UE consolidée", enrichir_ue),
    "sanctions_onu": ("ONU consolidée", enrichir_onu),
    "sanctions_uk": ("UK Sanctions List", enrichir_uk),
    "gels_avoirs_fr": ("Gels DG Trésor", enrichir_gels_fr),
}


def sanctions_consolidees(actives_only=True) -> pd.DataFrame:
    """Vue unique des 5 listes (pour le screening, les cartes et le ML)."""
    frames = [store.load(n) for n in SANCTION_SOURCES]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(columns=SANCTION_COLS + store.META_COLS)
    df = pd.concat(frames, ignore_index=True)
    if actives_only and "statut" in df.columns:
        df = df[df.statut != "retiré"]
    return df


# =========================================================================== #
# 6. Risque pays — Banque mondiale (WGI, PIB/hab.) + GAFI + sanctions
# =========================================================================== #
WB_IND = {"CC.EST": ("wgi_corruption", 3), "GE.EST": ("wgi_efficacite_gouv", 3), "PV.EST": ("wgi_stabilite", 3),
          "RQ.EST": ("wgi_qualite_regl", 3), "RL.EST": ("wgi_etat_droit", 3), "VA.EST": ("wgi_voix_resp", 3),
          "NY.GDP.PCAP.CD": ("pib_hab_usd", 2)}


def fetch_worldbank() -> pd.DataFrame:
    vals, years = {}, {}
    for ind, (col, src) in WB_IND.items():
        url = (f"https://api.worldbank.org/v2/country/all/indicator/{ind}?source={src}&format=json"
               f"&per_page=20000&mrnev=1")
        try:
            js = _get(url, timeout=60).json()
        except Exception:
            continue
        for x in (js[1] if isinstance(js, list) and len(js) > 1 and js[1] else []):
            i3 = x.get("countryiso3code")
            if i3 and x.get("value") is not None:
                vals.setdefault(i3, {})[col] = round(float(x["value"]), 3)
                years[i3] = max(years.get(i3, ""), str(x.get("date", "")))
    if not vals:
        raise SourceError("API Banque mondiale injoignable")
    return pd.DataFrame([dict(iso3=k, annee_wgi=years.get(k, ""), **v) for k, v in vals.items()])


def build_pays_risque(wb: pd.DataFrame | None = None) -> pd.DataFrame:
    r = ref()[["iso2", "iso3", "nom", "region", "sous_region"]].copy()
    old = store.load("pays_risque")
    if wb is None or wb.empty:  # on garde les WGI déjà stockés
        keep = [c for c in old.columns if c.startswith(("wgi_", "pib_", "annee_wgi", "cpi", "basel"))] if not old.empty else []
        wb = old[["iso3"] + keep] if keep else pd.DataFrame(columns=["iso3"])
    else:  # on conserve les indices importés à la main (CPI, Basel)
        extra = [c for c in old.columns if c.startswith(("cpi", "basel"))] if not old.empty else []
        if extra:
            wb = wb.merge(old[["iso3"] + extra], on="iso3", how="left")
    df = r.merge(wb, on="iso3", how="left")
    df["gafi"] = df.iso2.map(lambda c: "Liste noire" if c in GAFI_NOIRE else "Liste grise" if c in GAFI_GRISE else "Aucune")
    df["gafi_maj"] = GAFI_DATE
    df["regime_sanctions"] = df.iso2.isin(REGIMES_SANCTIONS).map({True: "oui", False: "non"})
    sc = sanctions_consolidees()

    def _count(col):
        cnt = {}
        for p in sc.get(col, pd.Series(dtype=str)):
            for c in set(str(p).split(" | ")):
                if c:
                    cnt[c] = cnt.get(c, 0) + 1
        return cnt
    own, reg = _count("pays"), _count("pays_regime")
    df["nb_entites_sanctionnees"] = df.iso2.map(lambda c: own.get(c, 0))     # entités de ce pays
    df["nb_designations_regime"] = df.iso2.map(lambda c: reg.get(c, 0))      # inscriptions au titre d'un régime visant ce pays
    df = score_pays(df)
    df["uid"] = df.iso2
    return df


def score_pays(df: pd.DataFrame) -> pd.DataFrame:
    """Score composite 0–100 (100 = risque maximal), transparent et explicable."""
    import numpy as np
    w = [c for c in df.columns if c.startswith("wgi_")]
    wgi = df[w].apply(pd.to_numeric, errors="coerce").mean(axis=1) if w else pd.Series(np.nan, index=df.index)
    s_gouv = ((2.5 - wgi.clip(-2.5, 2.5)) / 5 * 40).fillna(20)
    s_gafi = df.gafi.map({"Liste noire": 35, "Liste grise": 18}).fillna(0)
    s_reg = (df.regime_sanctions == "oui") * 12
    n = pd.to_numeric(df.nb_entites_sanctionnees, errors="coerce").fillna(0)
    s_sanc = (np.log1p(n) / np.log1p(max(n.max(), 1)) * 13) if n.max() > 0 else 0
    cpi = pd.to_numeric(df.get("cpi", pd.Series(np.nan, index=df.index)), errors="coerce")
    adj = ((50 - cpi.clip(0, 100)) / 50 * 5).fillna(0)  # bonus/malus si l'IPC a été importé
    df["score_gouvernance"] = s_gouv.round(1)
    df["score_gafi"] = s_gafi
    df["score_regime"] = s_reg.astype(float)
    df["score_sanctions"] = pd.Series(s_sanc, index=df.index).round(1) if not np.isscalar(s_sanc) else 0.0
    df["score_risque"] = (s_gouv + s_gafi + s_reg + df["score_sanctions"] + adj).clip(0, 100).round(1)
    df["niveau"] = pd.cut(df.score_risque, [-1, 35, 55, 101], labels=["Faible", "Modéré", "Élevé"]).astype(str)
    return df


def enrichir_pays(avec_banque_mondiale=True):
    def fn():
        wb = None
        if avec_banque_mondiale:
            try:
                wb = fetch_worldbank()
            except SourceError:
                wb = None
        return build_pays_risque(wb)
    return _run("pays_risque", fn, "Banque mondiale · GAFI · listes de sanctions", snapshot=False)


def importer_indice_pays(df_in: pd.DataFrame, colonne: str) -> int:
    """Importe un indice externe (ex. IPC Transparency International, Basel AML Index).
    df_in doit contenir une colonne pays (ISO2/ISO3/nom) et une colonne valeur."""
    cp = next(c for c in df_in.columns if c.lower() in ("iso3", "iso2", "iso", "code", "pays", "country"))
    cv = next(c for c in df_in.columns if c != cp)
    m = {to_iso2(v): x for v, x in zip(df_in[cp], df_in[cv]) if to_iso2(v)}
    cur = store.load("pays_risque")
    if cur.empty:
        cur = build_pays_risque()
    cur[colonne] = cur.iso2.map(m).fillna(cur.get(colonne, ""))
    cur = score_pays(cur.drop(columns=[c for c in cur.columns if c.startswith("score_")] + ["niveau"], errors="ignore"))
    store.upsert("pays_risque", cur, source=f"import manuel : {colonne}")
    return len(m)


# =========================================================================== #
# 7. À la demande — GLEIF, Recherche d'entreprises, Wikidata, GDELT, OSM
# =========================================================================== #
def gleif_search(q: str, n=8) -> pd.DataFrame:
    url = f"https://api.gleif.org/api/v1/lei-records?filter[fulltext]={quote(q)}&page[size]={n}"
    js = _get(url, timeout=30, headers={"Accept": "application/vnd.api+json"}).json()
    rows = []
    for d in js.get("data", []):
        a = d.get("attributes", {}); e = a.get("entity", {}); la = e.get("legalAddress", {}) or {}
        rows.append(dict(uid=a.get("lei", d.get("id")), lei=a.get("lei", d.get("id")),
                         nom=(e.get("legalName") or {}).get("name", ""), pays=la.get("country", ""),
                         ville=la.get("city", ""), adresse=", ".join(la.get("addressLines", []) or []),
                         code_postal=la.get("postalCode", ""), juridiction=e.get("jurisdiction", ""),
                         forme=(e.get("legalForm") or {}).get("id", ""), statut_entite=e.get("status", ""),
                         statut_lei=(a.get("registration") or {}).get("status", ""),
                         date_lei=((a.get("registration") or {}).get("initialRegistrationDate", "") or "")[:10],
                         categorie=e.get("category", ""), parent_direct="", parent_ultime=""))
    df = pd.DataFrame(rows)
    for i, r in df.iterrows():
        for rel, col in (("direct-parent", "parent_direct"), ("ultimate-parent", "parent_ultime")):
            try:
                p = S.get(f"https://api.gleif.org/api/v1/lei-records/{r.lei}/{rel}", timeout=15)
                if p.ok:
                    pd_ = p.json().get("data", {}).get("attributes", {})
                    df.at[i, col] = f"{pd_.get('entity', {}).get('legalName', {}).get('name', '')} ({pd_.get('lei', '')})"
            except Exception:
                pass
    if not df.empty:
        store.append_rows("lei_gleif", df, source="GLEIF")
    return df


def gleif_children(lei: str) -> pd.DataFrame:
    try:
        js = _get(f"https://api.gleif.org/api/v1/lei-records/{lei}/direct-children?page[size]=50", timeout=20).json()
    except SourceError:
        return pd.DataFrame()
    return pd.DataFrame([dict(lei=d["attributes"]["lei"], nom=d["attributes"]["entity"]["legalName"]["name"],
                              pays=d["attributes"]["entity"]["legalAddress"].get("country", ""))
                         for d in js.get("data", [])])


def entreprises_fr(q: str, n=8) -> pd.DataFrame:
    js = _get(f"https://recherche-entreprises.api.gouv.fr/search?q={quote(q)}&per_page={n}", timeout=30).json()
    rows = []
    for e in js.get("results", []):
        s_ = e.get("siege", {}) or {}
        dirs = e.get("dirigeants", []) or []
        fin = e.get("finances") or {}
        last = sorted(fin)[-1] if fin else ""
        rows.append(dict(
            uid=e.get("siren"), siren=e.get("siren"), nom=e.get("nom_complet", ""),
            nature_juridique=e.get("nature_juridique", ""), naf=e.get("activite_principale", ""),
            date_creation=e.get("date_creation", ""), etat=e.get("etat_administratif", ""),
            categorie=e.get("categorie_entreprise", ""), effectif=e.get("tranche_effectif_salarie", ""),
            adresse=s_.get("adresse", ""), commune=s_.get("libelle_commune", ""),
            lat=s_.get("latitude", ""), lon=s_.get("longitude", ""),
            nb_etablissements=e.get("nombre_etablissements", ""),
            dirigeants=_j(f"{d.get('prenoms', '')} {d.get('nom', '')} ({d.get('qualite', '')})".strip()
                          if d.get("type_dirigeant") == "personne physique"
                          else f"{d.get('denomination', '')} ({d.get('qualite', '')})" for d in dirs),
            ca=(fin.get(last) or {}).get("ca", "") if last else "",
            resultat_net=(fin.get(last) or {}).get("resultat_net", "") if last else "", exercice=last))
    df = pd.DataFrame(rows)
    if not df.empty:
        store.append_rows("entreprises_fr", df, source="API Recherche d'entreprises")
    return df


WD_SPARQL = "https://query.wikidata.org/sparql"


def _sparql(q: str) -> list[dict]:
    r = _get(f"{WD_SPARQL}?format=json&query={quote(q)}", timeout=60,
             headers={"Accept": "application/sparql-results+json"})
    return [{k: v.get("value", "") for k, v in b.items()} for b in r.json()["results"]["bindings"]]


def ppe_pays(iso2: str, limit=400) -> pd.DataFrame:
    """PPE d'un pays depuis Wikidata : chefs d'État/gouvernement, ministres, parlementaires, juges suprêmes,
    dirigeants de banque centrale, ambassadeurs, officiers généraux (fonctions FATF R.12)."""
    q = f"""
SELECT DISTINCT ?p ?pLabel ?posLabel ?debut ?fin ?naissance WHERE {{
  ?pays wdt:P297 "{iso2}".
  VALUES ?cls {{ wd:Q48352 wd:Q2285706 wd:Q83307 wd:Q486839 wd:Q16533 wd:Q121998 wd:Q1553195 wd:Q189290 }}
  ?pos wdt:P279* ?cls; wdt:P1001|wdt:P17 ?pays.
  ?p p:P39 ?st. ?st ps:P39 ?pos.
  OPTIONAL {{ ?st pq:P580 ?debut. }} OPTIONAL {{ ?st pq:P582 ?fin. }} OPTIONAL {{ ?p wdt:P569 ?naissance. }}
  FILTER(!BOUND(?fin) || ?fin > "2000-01-01"^^xsd:dateTime)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}} LIMIT {limit}"""
    rows = [dict(uid=f"{b['p'].rsplit('/', 1)[-1]}-{_uid(b.get('posLabel'))}", qid=b["p"].rsplit("/", 1)[-1],
                 nom=b.get("pLabel", ""), fonction=b.get("posLabel", ""), pays=iso2,
                 debut=b.get("debut", "")[:10], fin=b.get("fin", "")[:10], naissance=b.get("naissance", "")[:10],
                 en_fonction="oui" if not b.get("fin") else "non") for b in _sparql(q)]
    df = pd.DataFrame(rows)
    if not df.empty:
        store.append_rows("ppe_wikidata", df, source="Wikidata")
    return df


def ppe_nom(name: str) -> pd.DataFrame:
    """Vérifie si un nom correspond à une PPE connue de Wikidata (fonctions publiques exercées)."""
    js = _get(f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote(name)}"
              f"&language=fr&uselang=fr&type=item&limit=5&format=json", timeout=20).json()
    ids = [x["id"] for x in js.get("search", [])]
    if not ids:
        return pd.DataFrame()
    q = f"""
SELECT ?p ?pLabel ?posLabel ?paysLabel ?pays2 ?debut ?fin ?naissance WHERE {{
  VALUES ?p {{ {' '.join('wd:' + i for i in ids)} }}
  ?p wdt:P31 wd:Q5; p:P39 ?st. ?st ps:P39 ?pos.
  OPTIONAL {{ ?pos wdt:P1001|wdt:P17 ?pays. ?pays wdt:P297 ?pays2. }}
  OPTIONAL {{ ?st pq:P580 ?debut. }} OPTIONAL {{ ?st pq:P582 ?fin. }} OPTIONAL {{ ?p wdt:P569 ?naissance. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}} LIMIT 60"""
    rows = [dict(uid=f"{b['p'].rsplit('/', 1)[-1]}-{_uid(b.get('posLabel'))}", qid=b["p"].rsplit("/", 1)[-1],
                 nom=b.get("pLabel", ""), fonction=b.get("posLabel", ""), pays=b.get("pays2", ""),
                 debut=b.get("debut", "")[:10], fin=b.get("fin", "")[:10], naissance=b.get("naissance", "")[:10],
                 en_fonction="oui" if not b.get("fin") else "non") for b in _sparql(q)]
    df = pd.DataFrame(rows)
    if not df.empty:
        store.append_rows("ppe_wikidata", df, source="Wikidata")
    return df


NEG_TERMS_EN = '(sanction OR sanctions OR fraud OR corruption OR bribery OR "money laundering" OR indicted OR fined OR arrested OR embezzlement)'
NEG_TERMS_FR = '(blanchiment OR corruption OR fraude OR condamné OR amende OR "mis en examen" OR escroquerie)'


def presse_negative(name: str, mois=24, n=75) -> pd.DataFrame:
    """Presse négative via GDELT DOC 2.0 (articles du monde entier, 65 langues)."""
    out = []
    for terms in (NEG_TERMS_EN, NEG_TERMS_FR):
        q = f'"{name}" {terms}'
        url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={quote(q)}&mode=artlist&format=json"
               f"&maxrecords={n}&sort=datedesc&timespan={mois}months")
        try:
            r = _get(url, timeout=40)
            js = json.loads(r.text) if r.text.strip().startswith("{") else {}
        except Exception:
            js = {}
        for a in js.get("articles", []):
            sd = a.get("seendate", "")
            out.append(dict(uid=_uid(name, a.get("url")), entite=name, titre=a.get("title", ""),
                            media=a.get("domain", ""), langue=a.get("language", ""),
                            pays_media=a.get("sourcecountry", ""),
                            date=f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}" if len(sd) >= 8 else "", lien=a.get("url", ""),
                            categorie=classer_presse(a.get("title", ""))))
        time.sleep(5)  # GDELT : une requête toutes les 5 s
    df = pd.DataFrame(out).drop_duplicates("uid") if out else pd.DataFrame()
    if not df.empty:
        store.append_rows("presse_negative", df, source="GDELT Project")
    return df


PRESSE_CATS = [("Sanctions", r"sanction|ofac|gel des avoirs|asset freeze|designat|blacklist"),
               ("Blanchiment", r"laundering|blanchi|aml\b"),
               ("Corruption", r"corrupt|brib|pots?-de-vin|kickback|embezzl|détourn"),
               ("Fraude", r"fraud|escroq|scam|ponzi|fraude"),
               ("Justice", r"indict|charged|arrest|convict|condamn|mis en examen|procès|trial|court|tribunal"),
               ("Amende", r"\bfine[ds]?\b|amende|penalt|settle")]


def classer_presse(title: str) -> str:
    t = (title or "").lower()
    return next((c for c, rx in PRESSE_CATS if re.search(rx, t)), "Autre")


_LAST_NOMINATIM = [0.0]


def geocode(q: str) -> dict | None:
    """Géocodage OpenStreetMap (Nominatim), mis en cache dans data/geocodage.csv (1 requête / s)."""
    q = (q or "").strip()
    if not q:
        return None
    key = _uid(q.lower())
    cache = store.load("geocodage")
    if not cache.empty and key in set(cache.uid):
        r = cache[cache.uid == key].iloc[0]
        return None if not r.lat else dict(lat=float(r.lat), lon=float(r.lon), label=r.label, pays=r.pays,
                                            bbox=r.get("bbox", ""))
    wait = 1.1 - (time.time() - _LAST_NOMINATIM[0])
    if wait > 0:
        time.sleep(wait)
    _LAST_NOMINATIM[0] = time.time()
    try:
        js = _get(f"https://nominatim.openstreetmap.org/search?q={quote(q)}&format=jsonv2&limit=1&addressdetails=1",
                  timeout=20).json()
    except SourceError:
        return None
    res = None
    row = dict(uid=key, requete=q, lat="", lon="", label="", pays="", bbox="")
    if js:
        x = js[0]
        res = dict(lat=float(x["lat"]), lon=float(x["lon"]), label=x.get("display_name", ""),
                   pays=(x.get("address", {}).get("country_code", "") or "").upper(),
                   bbox=",".join(x.get("boundingbox", [])))
        row.update({k: str(v) for k, v in res.items()})
    store.append_rows("geocodage", [row], source="OpenStreetMap (Nominatim)")
    return res


OSM_CATEGORIES = {
    "Banques": '["amenity"="bank"]',
    "Bureaux de change": '["amenity"="bureau_de_change"]',
    "Transfert d'argent": '["amenity"="money_transfer"]',
    "Distributeurs (ATM)": '["amenity"="atm"]',
    "Casinos & jeux": '["amenity"~"casino|gambling"]',
    "Prêteurs sur gages": '["shop"~"pawnbroker|money_lender"]',
    "Bijouteries / or": '["shop"~"jewelry|gold_buyer"]',
    "Concessionnaires auto": '["shop"="car"]',
    "Agences immobilières": '["office"="estate_agent"]',
    "Ambassades": '["office"="diplomatic"]',
    "Ports & marinas": '["harbour"="yes"]',
}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def osm_poi(lieu: str, categories: list[str], max_km=25) -> pd.DataFrame:
    """Points d'intérêt sensibles LCB-FT autour d'une ville (OpenStreetMap / Overpass)."""
    g = geocode(lieu)
    if not g:
        raise SourceError(f"lieu introuvable : {lieu}")
    lat, lon = g["lat"], g["lon"]
    d = max_km / 111.0
    try:
        s, n, w, e = map(float, g["bbox"].split(","))
        s, n, w, e = max(s, lat - d), min(n, lat + d), max(w, lon - d * 1.5), min(e, lon + d * 1.5)
    except Exception:
        s, n, w, e = lat - d, lat + d, lon - d, lon + d
    parts = "".join(f"nwr{OSM_CATEGORIES[c]}({s},{w},{n},{e});" for c in categories if c in OSM_CATEGORIES)
    q = f"[out:json][timeout:90];({parts});out center 3000;"
    last = None
    for u in OVERPASS:
        try:
            r = S.post(u, data={"data": q}, timeout=120)
            if r.ok:
                js = r.json(); break
            last = f"HTTP {r.status_code}"
        except Exception as ex:
            last = str(ex)
    else:
        raise SourceError(f"Overpass injoignable ({last})")
    rows = []
    for el in js.get("elements", []):
        t = el.get("tags", {})
        la, lo = el.get("lat") or el.get("center", {}).get("lat"), el.get("lon") or el.get("center", {}).get("lon")
        if la is None:
            continue
        cat = next((c for c in categories if _osm_match(OSM_CATEGORIES[c], t)), "Autre")
        rows.append(dict(uid=f"{el['type']}{el['id']}", osm_id=f"{el['type']}/{el['id']}", categorie=cat,
                         nom=t.get("name", "") or t.get("brand", "") or t.get("operator", ""),
                         operateur=t.get("operator", "") or t.get("brand", ""), lat=la, lon=lo, lieu=lieu,
                         adresse=" ".join(x for x in (t.get("addr:housenumber", ""), t.get("addr:street", ""),
                                                      t.get("addr:city", "")) if x),
                         pays=g.get("pays", "")))
    df = pd.DataFrame(rows)
    if not df.empty:
        store.append_rows("osm_poi", df, source="OpenStreetMap (Overpass)")
    return df


def _osm_match(flt: str, tags: dict) -> bool:
    k, op, v = re.match(r'\["(.+?)"(=|~)"(.+?)"\]', flt).groups()
    val = tags.get(k, "")
    return bool(re.fullmatch(v, val)) if op == "~" else val == v


# =========================================================================== #
# 8. Actualités (issues de la veille CWP) → historique CSV
# =========================================================================== #
def persist_actualites(rows: list[dict]) -> dict:
    out = []
    for r in rows:
        if not r.get("link"):
            continue
        out.append(dict(uid=_uid(r["link"]),
                        date=datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d %H:%M") if r.get("ts") else "",
                        theme=r.get("theme", ""), titre=r.get("headline") or r.get("title", ""),
                        resume=r.get("desc", ""), entite=r.get("entity", ""), pays_iso2=r.get("cc", ""),
                        pays=r.get("country", ""), mesure_cle=r.get("mkey", ""), mesure=r.get("measure", ""),
                        autorite=r.get("auth", ""), montant=r.get("amount", ""), montant_v=r.get("amount_v", 0),
                        media=r.get("source", ""), langue=r.get("lang", ""), groupe=r.get("groupe", ""),
                        lien=r["link"]))
    return store.append_rows("actualites", out, source="Presse (Google News) · CWP")
