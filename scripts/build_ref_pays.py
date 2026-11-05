"""Génère data/reference/ref_pays.csv (référentiel ISO 3166-1 : 249 pays, noms FR / EN, régions ONU en français).

    pip install pycountry country_converter
    python scripts/build_ref_pays.py

À relancer uniquement si la norme ISO évolue ; le fichier produit est versionné dans le dépôt.
"""
import csv
import gettext
import os
import sys

import country_converter as coco
import pycountry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cwp.config import ref_path  # noqa: E402

SOUS_REGION = {
    "Antarctica": "Antarctique", "Australia and New Zealand": "Australie et Nouvelle-Zélande", "Caribbean": "Caraïbes",
    "Central America": "Amérique centrale", "Central Asia": "Asie centrale", "Eastern Africa": "Afrique de l'Est",
    "Eastern Asia": "Asie de l'Est", "Eastern Europe": "Europe de l'Est", "Melanesia": "Mélanésie",
    "Micronesia": "Micronésie", "Middle Africa": "Afrique centrale", "Northern Africa": "Afrique du Nord",
    "Northern America": "Amérique du Nord", "Northern Europe": "Europe du Nord", "Polynesia": "Polynésie",
    "South America": "Amérique du Sud", "South-eastern Asia": "Asie du Sud-Est", "Southern Africa": "Afrique australe",
    "Southern Asia": "Asie du Sud", "Southern Europe": "Europe du Sud", "Western Africa": "Afrique de l'Ouest",
    "Western Asia": "Asie de l'Ouest", "Western Europe": "Europe de l'Ouest",
}
REGION = {"Africa": "Afrique", "America": "Amériques", "Asia": "Asie", "Europe": "Europe", "Oceania": "Océanie",
          "Antarctica": "Antarctique"}
# Noms courts usuels en français (la norme ISO donne parfois des formes longues)
NOM_COURT = {"US": "États-Unis", "GB": "Royaume-Uni", "RU": "Russie", "IR": "Iran", "KP": "Corée du Nord",
             "KR": "Corée du Sud", "SY": "Syrie", "VE": "Venezuela", "BO": "Bolivie", "LA": "Laos", "VN": "Vietnam",
             "TZ": "Tanzanie", "MD": "Moldavie", "CD": "RD Congo", "CG": "Congo", "MK": "Macédoine du Nord",
             "PS": "Palestine", "TW": "Taïwan", "VG": "Îles Vierges britanniques", "VI": "Îles Vierges américaines",
             "FM": "Micronésie", "CZ": "Tchéquie", "VA": "Vatican", "BN": "Brunei", "CV": "Cap-Vert", "SZ": "Eswatini",
             "HK": "Hong Kong", "MO": "Macao", "MM": "Myanmar", "BS": "Bahamas", "GM": "Gambie", "NL": "Pays-Bas",
             "TR": "Turquie", "CI": "Côte d'Ivoire", "LY": "Libye", "AE": "Émirats arabes unis", "DO": "République dominicaine"}


def main():
    fr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
    data = coco.CountryConverter().data.set_index("ISO2")
    rows = []
    for c in pycountry.countries:
        en = getattr(c, "common_name", None) or c.name
        nom = NOM_COURT.get(c.alpha_2) or fr.gettext(c.name)
        reg = data.loc[c.alpha_2] if c.alpha_2 in data.index else None
        cont = reg["continent"] if reg is not None else ""
        sous = reg["UNregion"] if reg is not None else ""
        rows.append(dict(iso2=c.alpha_2, iso3=c.alpha_3, nom=nom, nom_en=en, region=REGION.get(cont, cont),
                         sous_region=SOUS_REGION.get(sous, sous)))
    rows.append(dict(iso2="XK", iso3="XKX", nom="Kosovo", nom_en="Kosovo", region="Europe", sous_region="Europe du Sud"))
    rows.sort(key=lambda r: r["iso2"])
    with open(ref_path("ref_pays.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} pays écrits dans {ref_path('ref_pays.csv')}")


if __name__ == "__main__":
    main()
