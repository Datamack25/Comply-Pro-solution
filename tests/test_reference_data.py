"""Cohérence des référentiels pays avec les listes GAFI et les programmes de sanctions."""
import pandas as pd

from cwp.config import ref_path
from cwp.data import countries
from cwp.data.sources import _prog_countries


def test_ref_pays_present_and_complete():
    df = countries.ref()
    assert len(df) >= 249
    assert {"iso2", "iso3", "nom", "nom_en", "region", "sous_region"} <= set(df.columns)
    assert df.iso2.is_unique


def test_focus_fiches_match_fatf_lists():
    from cwp.ui.pages.focus_caraibes import gafi_mismatch
    df = pd.read_csv(ref_path("focus_caraibes_pays.csv"), dtype=str, keep_default_na=False)
    bad = {r.code: gafi_mismatch(r.code, r.gafi) for r in df.itertuples() if gafi_mismatch(r.code, r.gafi)}
    assert not bad, bad


def test_caraibes_base_matches_fatf_lists():
    df = pd.read_csv(ref_path("caraibes_pays.csv"), dtype=str, keep_default_na=False)
    for r in df.itertuples():
        listed = "grise" in r.statut_gafi.lower() or "noire" in r.statut_gafi.lower()
        assert listed == (r.code in countries.GAFI_GRISE | countries.GAFI_NOIRE), r.code


def test_ofac_ukraine_programs_target_russia():
    assert _prog_countries("[UKRAINE-EO13662] [RUSSIA-EO14024]") == ["RU", "RU"]
    assert _prog_countries("[UKRAINE-EO13685]") == ["UA"]          # Crimée
    assert _prog_countries("[SDGT]") == [""]


def test_country_normalisation_is_strict():
    assert countries.to_iso2("Virgin Islands, U.S.") == "VI"
    assert countries.to_iso2("Dominica") == "DM"
    assert countries.to_iso2("Niger") == "NE"
