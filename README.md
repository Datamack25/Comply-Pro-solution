# CWP – Compliance Watch Platform

Plateforme Streamlit de veille conformité : sanctions, embargos, LCB-FT / AMLA, GAFI, régulateurs,
anticorruption, crypto. Elle comprend aussi le filtrage d'entités, la notoriété négative, la cartographie
des risques pays, un focus Haïti / Caraïbes / Amérique latine et un espace pédagogique.

© 2026 Mackenson Cineus — Compliance Watch Platform

---

## Démarrage

```bash
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Les clés facultatives (OpenSanctions, IA pour les fiches Regulatory Flash, moteur web pour la notoriété
négative) se mettent dans `.streamlit/secrets.toml`. Partez du modèle `.streamlit/secrets.toml.example`.

## Organisation du dépôt

```
Comply-Pro-solution/
├── app.py                     Point d'entrée Streamlit : navigation uniquement
├── cwp/                       Code de l'application (package Python)
│   ├── config.py              Chemins, identité (©, avertissement), réglages de langue
│   ├── core/                  Logique métier pure, testée, sans Streamlit
│   │   ├── geo.py             Détection du pays (mots entiers, pays visé ≠ émetteur)
│   │   ├── classify.py        Entité, mesure, autorité, montant, langue d'un article
│   │   └── dedup.py           Fusion des doublons, y compris français / anglais
│   ├── services/              Accès à l'extérieur
│   │   ├── news.py            Flux Google Actualités FR / EN, résumé, archivage
│   │   ├── regwatch.py        Veille des régulateurs (Regulatory Flash)
│   │   └── opensanctions.py   API OpenSanctions
│   ├── data/                  Données ouvertes : listes de sanctions, risque pays, filtrage, ML, rapports
│   ├── pedago/                Espace pédagogique : glossaire, méthodes, cas, trames
│   ├── content/               Contenus éditoriaux : concepts, textes de loi, registre, fraudes, liens
│   ├── exports/               Exports PDF / PNG / Excel signés (© + avertissement)
│   └── ui/
│       ├── theme.py           Charte graphique
│       ├── components.py      Composants partagés (pied de page légal, cartes, tableau, langue)
│       ├── state.py           Mots-clés d'alerte, articles déjà vus
│       └── pages/             Une page par module (dashboard, veille, profil_entite, …)
├── data/
│   ├── reference/             Référentiels versionnés et éditables (pays ISO, fiches Caraïbes, concepts)
│   └── *.csv                  Données enrichies à l'exécution (listes, actualités, journal)
├── assets/                    Polices (accents dans les PDF) et images
├── scripts/                   enrichir.py (tâche planifiée), build_ref_pays.py
├── tests/                     Tests automatiques (pytest)
├── docs/                      Documentation détaillée des onglets et des données
└── .streamlit/                config.toml (thème), secrets.toml.example
```

Les règles de dépendance sont simples. `core` ne dépend de rien. `services`, `data` et `exports`
s'appuient sur `core`. `ui` s'appuie sur tout le reste. `app.py` ne fait qu'appeler les pages.

## Ajouter une page

1. Créez `cwp/ui/pages/ma_page.py` avec une fonction `render_ma_page()`.
2. Ajoutez une ligne dans la liste `PAGES` de `app.py` : `("🧩 Ma page", "ma_page", "render_ma_page")`.

Le pied de page légal s'ajoute automatiquement en bas de chaque page.

## Mentions légales

Le copyright et l'avertissement sont définis à un seul endroit, `cwp/config.py`
(`COPYRIGHT`, `DISCLAIMER`). Ils apparaissent :

- en petits caractères au bas de chaque page et dans la barre latérale ;
- en pied de page de chaque PDF, sur chaque page ;
- au bas des images PNG ;
- dans un onglet « Mentions » des fichiers Excel ;
- dans les rapports HTML et les exports JSON.

## Fiabilité des informations

- **Pays affiché.** Pour une sanction, un gel, un embargo ou une liste GAFI, c'est le pays *visé* qui
  est affiché, pas celui qui prononce la mesure (« l'UE sanctionne la Russie » → Russie). Si le titre ne
  le précise pas, la colonne affiche « — » plutôt qu'un pays erroné. L'émetteur reste visible dans la
  colonne Autorité.
- **Doublons.** Une information parue en français et en anglais n'est affichée qu'une fois. Par
  défaut, c'est la version française qui est affichée. Les autres versions restent accessibles sous
  l'article. La langue se règle dans la barre latérale.
- **Listes de sanctions.** Chaque inscription a deux rattachements : le pays de la personne ou de
  l'entité (`pays`) et le pays visé par le régime (`pays_regime`). Une société chinoise inscrite au
  titre du programme Iran est donc rattachée à la Chine et au régime Iran.
- **Statuts GAFI.** La liste de référence est dans `cwp/data/countries.py` (plénière du 30/10/2026).
  Un contrôle automatique signale toute fiche pays qui la contredit (voir `tests/test_reference_data.py`).

Outil d'aide à la veille fourni à titre informatif. Il ne constitue pas un conseil juridique ou
réglementaire. Vérifiez toute information auprès des sources officielles (OFAC, UE, ONU, DG Trésor,
GAFI…) avant toute décision. Un nom cité dans la presse n'est pas une désignation officielle.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Données

Voir `docs/donnees.md` (listes, risque pays, ML, persistance sur Streamlit Cloud) et `docs/onglets.md`
(Regulatory Flash, glossaire des fraudes).
