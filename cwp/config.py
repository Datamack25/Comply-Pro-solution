"""
cwp.config — configuration centrale de la plateforme.

Un seul endroit pour :
  • les chemins (racine du projet, données de référence, données d'exécution, ressources) ;
  • l'identité de la plateforme (nom, copyright, avertissement), réutilisée par l'interface
    et par tous les exports (PDF, PNG, Excel, HTML, JSON).
"""
from __future__ import annotations

import os
from datetime import datetime

# --------------------------------------------------------------------------- #
# Chemins
# --------------------------------------------------------------------------- #
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # racine du dépôt
DATA_DIR = os.path.join(ROOT, "data")                                # données d'exécution (CSV enrichis)
REF_DIR = os.path.join(DATA_DIR, "reference")                        # référentiels versionnés (CSV éditables)
MODEL_DIR = os.path.join(DATA_DIR, "models")                         # modèles ML entraînés
ASSETS_DIR = os.path.join(ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")

for _d in (DATA_DIR, MODEL_DIR):
    os.makedirs(_d, exist_ok=True)


def ref_path(name: str) -> str:
    """Chemin d'un référentiel de data/reference/."""
    return os.path.join(REF_DIR, name)


# --------------------------------------------------------------------------- #
# Identité de la plateforme
# --------------------------------------------------------------------------- #
APP_NAME = "Compliance Watch Platform"
APP_SHORT = "CWP"
PLATFORM = f"{APP_SHORT} – {APP_NAME}"
OWNER = "Mackenson Cineus"
YEAR = datetime.now().year

COPYRIGHT = f"© {YEAR} {OWNER} — {APP_NAME}"
DISCLAIMER = ("Outil d'aide à la veille fourni à titre informatif. Il ne constitue pas un conseil juridique "
              "ou réglementaire. Vérifiez toute information auprès des sources officielles avant toute décision.")
# Version courte pour les pieds de page étroits (exports PNG, en-têtes de colonnes…)
DISCLAIMER_SHORT = "Information indicative, non constitutive d'un conseil : vérifiez auprès des sources officielles."
LEGAL_FOOTER = f"{COPYRIGHT} · {DISCLAIMER}"

# --------------------------------------------------------------------------- #
# Langue des actualités
# --------------------------------------------------------------------------- #
DEFAULT_LANG = "fr"
LANG_MODES = {
    "fr_first": "Français en priorité",
    "en_first": "Anglais en priorité",
    "fr_only": "Français uniquement",
    "en_only": "Anglais uniquement",
}
