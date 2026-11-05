"""Chaque page s'affiche sans erreur et porte la mention © + l'avertissement."""
import os

import pytest
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    return at


def test_every_page_renders_with_legal_footer(app):
    for page in app.sidebar.radio[0].options:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, [e.value for e in app.exception])
        md = " ".join(m.value for m in app.markdown)
        assert "Mackenson Cineus" in md and "titre informatif" in md, page
