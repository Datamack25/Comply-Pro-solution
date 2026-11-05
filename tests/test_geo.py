"""Détection du pays : mots entiers, sigles en majuscules, pays VISÉ plutôt qu'émetteur."""
import pytest

from cwp.core import geo


@pytest.mark.parametrize("headline, kind, expected", [
    ("L'UE adopte son 20e paquet de sanctions contre la Russie", "sanction", "RU"),
    ("US imposes sanctions on Chinese refinery for buying Iranian oil", "sanction", "CN"),
    ("Treasury sanctions Haitian gang leaders Viv Ansanm", "sanction", "HT"),
    ("Les États-Unis sanctionnent des responsables nicaraguayens", "sanction", "NI"),
    ("UK sanctions Russian oligarchs over Ukraine war", "sanction", "RU"),
    ("Sanctions : Washington vise le secteur aurifère du Nicaragua", "sanction", "NI"),
    ("Russia imposes sanctions on US officials", "sanction", "US"),
    ("La Chine sanctionne des entreprises américaines", "sanction", "US"),
    ("FATF adds Bulgaria to grey list", "liste", "BG"),
    ("South Sudan arms embargo renewed by UN Security Council", "sanction", "SS"),
    ("US Virgin Islands bank charged", "enquete", "VI"),
])
def test_country_of(headline, kind, expected):
    assert geo.country_of(headline, "", kind)[0] == expected


@pytest.mark.parametrize("headline, kind", [
    ("Machine learning et LCB-FT : nouvelles lignes directrices", "regle"),   # « machine » ≠ Chine
    ("Un incubateur fintech lève 10 M€", "news"),                            # « incubateur » ≠ Cuba
    ("OFAC sanctions network helping us evade", "sanction"),                  # « us » pronom ≠ États-Unis
    ("New Mexico man indicted for laundering", "enquete"),                    # New Mexico ≠ Mexique
    ("Latin American banks face new rules", "regle"),                         # ≠ États-Unis
    ("EU adopts new sanctions package", "sanction"),                          # émetteur seul : pas de pays visé
])
def test_no_false_country(headline, kind):
    assert geo.country_of(headline, "", kind)[0] == ""


def test_issuer_never_shown_as_target_when_unknown():
    cc, name = geo.country_of("Le Conseil de l'UE adopte de nouvelles sanctions", "", "sanction")
    assert cc == "" and name == "—"


def test_fine_uses_authority_jurisdiction():
    assert geo.country_of("BNP Paribas condamnée à une amende", "", "amende", "ACPR")[0] == "FR"


def test_country_by_name_exact_only():
    assert geo.country_by_name("Russia") == ("RU", "Russie")
    assert geo.country_by_name("Bank of Russia") is None
