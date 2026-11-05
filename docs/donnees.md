# CWP — Données ouvertes, Machine Learning, Cartographie et Rapports

## Nouveaux onglets

| Onglet | Rôle |
|---|---|
| 🗄️ **Centre de données** | Boutons d'enrichissement (un clic = le CSV s'enrichit), explorateur, journal, nouveautés et radiations, sauvegarde ZIP / Excel, restauration |
| 🧭 **Profil d'entité** | Filtrage sanctions + PPE (correspondance approchante), presse négative, LEI, registre français, carte OSM, graphe de relations, score explicable, rapports PDF / HTML / Excel ; filtrage en lot d'un fichier clients |
| 🗺️ **Cartographie** | Carte mondiale du risque pays, sanctions par pays et programme, activités à risque d'une ville (OpenStreetMap), entités analysées, actualités par pays |
| 🤖 **Machine Learning** | Classifieur d'actualités (apprend de vos corrections), segmentation des pays (K-means + ACP), anomalies (Isolation Forest), typologies de sanctions, tendance des inscriptions |
| 📑 **Rapports** | Veille sanctions (nouveautés depuis une date), risque pays, profil d'entité, inventaire — en PDF, HTML interactif et Excel |

Le bouton « 🔄 Rafraîchir la veille » de la barre latérale archive aussi les actualités dans `data/actualites.csv`.

## Fichiers CSV (`data/`)

| Fichier | Source | Enrichissement |
|---|---|---|
| `sanctions_ofac.csv` | OFAC – SDN (SDN, ADD, ALT) | liste complète → entrées disparues = « retiré » |
| `sanctions_ue.csv` | Commission européenne – FSF | idem |
| `sanctions_onu.csv` | Conseil de sécurité ONU | idem |
| `sanctions_uk.csv` | FCDO – UK Sanctions List | idem |
| `gels_avoirs_fr.csv` | DG Trésor – registre des gels | idem |
| `pays_risque.csv` | Banque mondiale (WGI, PIB/hab.) + GAFI + sanctions | recalcul |
| `actualites.csv` | veille CWP | ajout |
| `ppe_wikidata.csv` | Wikidata | ajout (par pays ou par nom) |
| `presse_negative.csv` | GDELT | ajout (par entité) |
| `lei_gleif.csv` | GLEIF | ajout (par entité) |
| `entreprises_fr.csv` | API Recherche d'entreprises (SIRENE / RNE) | ajout |
| `osm_poi.csv`, `geocodage.csv` | OpenStreetMap (Overpass, Nominatim) | ajout / cache |
| `entites_profils.csv` | profils calculés par CWP | ajout |
| `ml_labels.csv` | vos validations d'étiquettes | ajout |
| `journal_maj.csv` | trace de chaque opération | ajout |
| `reference/ref_pays.csv` | référentiel ISO (250 pays, noms FR / EN, régions ONU) — `scripts/build_ref_pays.py` | fixe, versionné |

Colonnes ajoutées automatiquement : `premiere_vue`, `derniere_vue`, `statut` (actif / retiré), `retire_le`.
La première fois qu'une liste est enrichie, elle sert de base de référence ; les « nouvelles inscriptions »
apparaissent à partir du deuxième enrichissement.

## Persistance sur Streamlit Community Cloud

Le disque de Streamlit Cloud est remis à zéro à chaque redémarrage. Deux solutions :
1. **Centre de données → Sauvegarde** : télécharger le ZIP et le restaurer après un redémarrage.
2. **GitHub Actions** (facultatif) : `.github/workflows/enrichissement.yml` lance chaque jour
   `scripts/enrichir.py` et committe les CSV mis à jour dans le dépôt. Supprimez ce fichier si vous
   ne voulez pas de commits automatiques.

## À vérifier

- **Listes GAFI** (`cwp/data/countries.py`) : saisies d'après la plénière du 30/10/2026 (source secondaire).
  Les confirmer sur le site du GAFI et les mettre à jour après chaque plénière (février, juin, octobre).
- **Régimes de sanctions** (`REGIMES_SANCTIONS`) : liste indicative à revoir.
- **Licences** : OpenSanctions et ACLED ne sont pas utilisés (licence commerciale). Wikidata (CC0), GLEIF (CC0),
  OpenStreetMap (ODbL, attribution affichée), GDELT (libre avec citation), listes officielles (domaine public).
- **IPC / Basel AML Index** : pas d'API libre ; importez le fichier dans Centre de données → « Importer un indice ».

## Méthodes

- **Correspondance de noms** : normalisation (accents, ponctuation, mots vides juridiques), puis
  0,45 × token_sort + 0,35 × token_set (pondéré par la couverture) + 0,20 × Jaro-Winkler, avec ajustements
  pays (+4 / −3), année de naissance (+5 / −6) et type (−8). Forte ≥ 95, Probable 88–95, Possible < 88.
- **Score d'entité** (0–100) : sanctions (60 / 38 / 15), PPE (22 / 10), presse négative (≤ 20),
  risque pays (25 % du score pays), juridiction offshore (6), LEI absent ou expiré (4), société radiée (5).
- **Score pays** (0–100) : gouvernance WGI (40), GAFI (noire 35 / grise 18), régime de sanctions (12),
  entités inscrites (13, échelle log), IPC importé (± 5).

Les résultats sont indicatifs : une correspondance de nom n'est pas une identification.

## 🎓 Espace pédagogique (`cwp/ui/pages/espace_pedagogique.py`, dossier `cwp/pedago/`)

| Rubrique | Contenu | Où le modifier |
|---|---|---|
| Glossaire | 563 termes rédigés (finance de marché, analyse financière, crédit, banque & paiements, LCB-FT, KYC, sanctions, embargos & export, fraude, fiscalité, crypto-actifs, corruption, régulation, gouvernance, outils) + 41 concepts + 50 fraudes existants ; **bouton d'enrichissement Wikipédia** par catégories (plusieurs milliers de termes, licence CC BY-SA citée) ; import de vos propres termes | `cwp/pedago/glossaire_data.py` (une ligne = `terme | catégorie | définition`) |
| Méthodologies | 16 méthodologies pas à pas : KYC personne physique, KYC personne morale / bénéficiaires effectifs, analyse N1, analyse N2 et DS, levée d'homonymie, contournement de sanctions, embargo / double usage, blanchiment (dont TBML), fraude fiscale, usurpation d'identité, fraude au paiement, PPE, analyse financière / crédit, crypto-actifs, financement du terrorisme, corruption | `cwp/pedago/methodes.py` |
| Cas d'étude | 15 cas pédagogiques fictifs avec corrigé + 6 affaires publiques résumées | `cwp/pedago/cas.py` |
| Trames | Une trame par méthodologie, en **PDF** (mode d'emploi + formulaire + cotation + décision) et en **Excel** (cellules à remplir, listes déroulantes, cotation et niveau de risque calculés, onglet décision) ; pack ZIP complet | générées depuis `methodes.py` |
| Quiz | QCM tirés du glossaire, par catégorie | — |

## 🧭 Profil d'entité 360°

En plus des sources en ligne (listes, PPE, presse, GLEIF, registre FR, OpenStreetMap), le profil interroge
**Wikidata / Wikipédia** (fiche d'identité : nature, pays, création, secteur, siège, dirigeants, société mère,
filiales, cotation, fonctions) et **SEC EDGAR** (comptes des sociétés cotées américaines), puis croise toutes
les données de la plateforme (actualités archivées, analyses antérieures, presse stockée, registres déjà
consultés, risque pays, Focus Caraïbes, programmes de sanctions du pays). Il produit :
- une **synthèse d'analyste** rédigée, des points d'attention et les prochaines étapes ;
- les **trames recommandées** pour le dossier, téléchargeables directement ;
- un rapport PDF / HTML / Excel qui reprend l'ensemble.

SEC EDGAR demande un User-Agent identifiant l'utilisateur : ajoutez `SEC_USER_AGENT = "Votre nom votre@email"`
dans les secrets Streamlit.

## 📰 Notoriété négative (`cwp/ui/pages/notoriete.py`, `cwp/data/notoriete.py`)

- Formulaire de **7 personnes ou entités** ; chaque nom (expression exacte) est combiné à **71 mots-clés négatifs** modifiables
  (français, anglais, espagnol, créole), par groupes OR (mode rapide) ou **un mot-clé par requête** (mode approfondi).
- Moteurs : **Google Actualités** (flux RSS publics), **GDELT** (presse mondiale) et, si une clé est configurée, une **recherche web
  par API officielle** de 4 pages par requête : `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` (Google Programmable Search) ou `BRAVE_API_KEY`.
  Le scraping direct des pages de résultats Google n'est pas utilisé (interdit par les conditions d'utilisation et bloqué).
- Lecture du texte des articles les plus pertinents, **score de 0 à 100 par article** (gravité et position des mots-clés, nom complet,
  nom et mot-clé dans la même phrase, crédibilité du média, fraîcheur, contextes atténuants : victime, acquittement, homonymie,
  fonction de lutte contre la fraude) et **5 niveaux de criticité colorés**. Si aucun moteur ne répond, la plateforme affiche
  « Recherche impossible » au lieu de conclure à l'absence d'information négative.
- Résumés extractifs, ou rédigés par IA si une clé `ANTHROPIC_API_KEY` / `MISTRAL_API_KEY` / `OLLAMA_URL` est configurée.
- **Un PDF par entité** (score, conclusion, échelle, articles pertinents avec lien et résumé, résultats écartés, méthode), ZIP du lot,
  Excel de tous les articles. Historique dans `notoriete_recherches.csv` / `notoriete_articles.csv`, repris par le profil 360°
  (+6 / +12 / +20 points au score pour les niveaux 3 / 4 / 5).

## 🇭🇹 Haïti & Caraïbes (`cwp/ui/pages/haiti.py`, `cwp/pedago/haiti.py`)

- Fiches BRH, UCREF, ULCC, BAFE, GAFIC ; seuils et délais (circulaire BRH 99-2 de 2018 : 600 000 HTG espèces, 60 000 HTG virements,
  5 ans de conservation, sanctions de 500 000 HTG par violation) avec un **statut de vérification** par élément.
  Le seuil de 1 300 000 HTG est marqué « à vérifier » (aucun texte trouvé).
- Contexte : économie informelle, transferts de la diaspora, instabilité, faiblesses du dispositif, panorama Caraïbes ;
  **rapport PDF** téléchargeable.
- Veille Caraïbes (UCREF, BRH, ULCC, sanctions, GAFIC, médias haïtiens) enrichissant `veille_caraibes.csv`.
- **Renseignements internes** : formulaire + import en masse d'informations non publiques (rapports ULCC, communiqués UCREF,
  décisions locales, terrain) avec fiabilité A–F et crédibilité 1–6 ; intégrés au filtrage des noms (liste « Renseignement interne »)
  et au profil 360°. Accès et durée de conservation à cadrer avec le DPO.
