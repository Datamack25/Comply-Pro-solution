# CWP — Onglets « Regulatory Flash » et « Glossaire des fraudes »

## Page Veille → sous-onglet « 📜 Veille réglementaire »

- **Registre & calendrier** (`cwp/content/registre_reglementaire.py`) : textes adoptés depuis 2021, en vigueur,
  à venir ou en cours d'adoption (LCB-FT, sanctions, crypto-actifs, paiements, résilience, prudentiel, ESG).
  Filtres statut / thème / juridiction / année, prochaines échéances (J-xx), frise chronologique,
  fiche Regulatory Flash par texte (PDF / PNG), export Excel et recueil PDF.
  Pour ajouter un texte : copier un bloc dans `REGISTRE` et adapter les dates.
- **Publications récentes** : même moteur que la page Regulatory Flash (ci-dessous).

## Page Veille → sous-onglet « 🖨️ Générateur de veille (PDF / image) »

Aussi disponible dans 🌎 Focus Caraïbes → « 🖨️ Générer un document » (pré-réglé sur Caraïbes / Haïti).

- **Région** : Monde entier, Caraïbes, Amérique latine, Amérique du Nord, Europe, Afrique, Moyen-Orient, Asie, Océanie
  (référentiel `data/reference/ref_pays.csv`, colonnes `region` / `sous_region`).
- **Pays** : un ou plusieurs, ou « Tous les pays de la région ».
- **Type d'information** : sanctions & gels d'avoirs, embargos & contrôle des exportations, amendes des régulateurs,
  listes GAFI & pays à risque, réglementation & circulaires, enquêtes / poursuites / corruption, ou toutes les actualités.
- **Période** (7 jours → 12 mois) et option « uniquement les mesures prononcées ».
- Tableau au format Weekly Watch (Entité / cible, Catégorie, Description + « Même information », Pays, Mesure, Montant,
  Date, Autorité) ; exports PNG, PDF (avec synthèse de l'analyste et statut GAFI des pays choisis) et Excel.
- Collecte : `cwp/services/veille_ciblee.py` (Google Actualités FR + EN par pays et par type, flux de la plateforme,
  historique `data/actualites.csv`). Une information n'est retenue que si elle cite un pays du périmètre :
  une sanction OFAC visant Haïti apparaît donc bien dans la veille Haïti.

## Regulatory Flash = veille réglementaire automatique

`cwp/services/regwatch.py` interroge les régulateurs (ACPR, TRACFIN, AMF, DG Trésor, Journal officiel, AFA,
AMLA, EBA, ESMA, BCE, Conseil/Commission UE, GAFI, OFAC, FinCEN, Comité de Bâle) via leurs flux
officiels et Google News filtré sur leur site. Chaque publication est classée
(texte législatif, orientations, consultation, sanction, rapport…) et transformée en fiche
Regulatory Flash, exportable en PDF / PNG, ou regroupée dans un bulletin PDF.

- Ajouter ou retirer une source : dictionnaire `SOURCES` en haut de `cwp/services/regwatch.py`.
- Fiches rédigées par IA : ajouter une clé dans les secrets Streamlit (voir `.streamlit/secrets.toml.example`).
  Sans clé, la fiche est construite par extraction automatique du texte de la publication.
- Le panneau « État des sources » indique quels flux répondent.
