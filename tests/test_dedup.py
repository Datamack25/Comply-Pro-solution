"""Fusion des doublons français / anglais."""
import time

from cwp.core import classify as K
from cwp.core import dedup as D

NOW = time.time()


def _rows(pairs):
    return [K.enrich(dict(title=f"{t} - {s}", source=s, lang=l, desc="", link=f"http://x/{i}", ts=NOW - h * 3600,
                          theme="Sanctions"))
            for i, (t, s, l, h) in enumerate(pairs)]


def test_fr_en_same_fact_merged_and_french_kept():
    rows = _rows([("L'UE adopte un 20e paquet de sanctions contre la Russie visant la flotte fantôme", "Le Monde", "fr", 1),
                  ("EU adopts 20th sanctions package against Russia targeting shadow fleet", "Reuters", "en", 2)])
    out = D.merge(rows, "fr")
    assert len(out) == 1
    assert out[0]["lang"] == "fr"
    assert [v["lang"] for v in out[0]["versions"]] == ["en"]


def test_english_preference():
    rows = _rows([("BNP Paribas condamnée à une amende de 5 millions d'euros par l'ACPR", "Les Echos", "fr", 1),
                  ("BNP Paribas fined €5 million by French regulator ACPR", "Bloomberg", "en", 2)])
    out = D.merge(rows, "en")
    assert len(out) == 1 and out[0]["lang"] == "en"


def test_distinct_facts_same_country_not_merged():
    rows = _rows([("L'UE adopte un 20e paquet de sanctions contre la Russie", "Le Monde", "fr", 1),
                  ("Royaume-Uni : nouvelles sanctions contre des oligarques russes", "BFM", "fr", 2),
                  ("Russia sanctions: US targets Russian banks", "CNBC", "en", 3)])
    assert len(D.merge(rows, "fr")) == 3


def test_outside_time_window_not_merged():
    rows = _rows([("Le GAFI retire la Bulgarie de la liste grise", "Les Echos", "fr", 1),
                  ("FATF removes Bulgaria from grey list", "Reuters", "en", 24 * 30)])
    assert len(D.merge(rows, "fr")) == 2


def test_language_filter():
    rows = _rows([("Le GAFI retire la Bulgarie de la liste grise", "Les Echos", "fr", 1),
                  ("FATF removes Bulgaria from grey list", "Reuters", "en", 2)])
    kept, prefer = D.filter_lang(rows, "en_only")
    assert prefer == "en" and all(r["lang"] == "en" for r in kept)


def test_negative_news_counted_once():
    from cwp.data.notoriete import merge_languages
    arts = [dict(titre="Rosneft visée par de nouvelles sanctions de l'UE", lien="a", media="Le Monde", date="2026-11-01", langue="fr"),
            dict(titre="EU slaps new sanctions on Rosneft", lien="b", media="Reuters", date="2026-11-01", langue="en"),
            dict(titre="Rosneft profits rise in Q3", lien="c", media="FT", date="2026-10-01", langue="en")]
    out = merge_languages(arts)
    assert len(out) == 2 and out[0]["nb_versions"] == 2
