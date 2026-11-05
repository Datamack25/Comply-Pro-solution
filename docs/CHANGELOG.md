# Journal des modifications

## 2.0.0 — 05/11/2026

### Corrections
- **Doublons français / anglais.** Une même information (« L'UE sanctionne… » / « EU sanctions… ») ne
  s'affiche plus qu'une fois. La correction s'applique au Dashboard, à la Veille, au Focus Caraïbes, à la
  notoriété négative (le score d'une entité ne compte plus deux fois le même article) et aux statistiques
  « Actualités par pays ». Un réglage de langue est disponible dans la barre latérale.
- **Pays incohérents avec la sanction ou l'embargo.**
  - Le pays affiché est désormais le pays visé, et non l'émetteur (UE, États-Unis…).
  - Les pays sont reconnus par mots entiers : « machine » ne donne plus la Chine, « incubateur » ne
    donne plus Cuba, « us » (pronom anglais) ne donne plus les États-Unis, « New Mexico » ne donne plus
    le Mexique.
  - Les gentilés sont reconnus en français et en anglais (iranien / Iranian, nord-coréen…), et environ
    110 pays et zones sont couverts.
  - OFAC : les programmes `UKRAINE-EO13661/13662` sont rattachés à la Russie. Auparavant, l'Ukraine
    apparaissait comme un pays massivement sanctionné.
  - Listes de sanctions : le pays de l'entité et le pays visé par le régime sont désormais distincts
    (colonne `pays_regime`). La Cartographie permet de choisir le rattachement.
  - La normalisation des noms de pays est plus stricte (« Dominica » ≠ « Dominican Republic », Îles
    Vierges américaines ≠ britanniques).
  - Focus Caraïbes : un article qui ne cite pas le pays recherché est écarté, ce qui élimine les
    homonymes comme « Salvador de Bahia ».
  - Les fiches pays incomplètes (statut GAFI) ont été complétées. Une alerte s'affiche si une fiche
    contredit la liste GAFI de référence.
- **Référentiel pays manquant** (`ref_pays.csv`) : il est désormais fourni dans `data/reference/`
  (250 pays, noms FR / EN, régions ONU). Sans lui, plusieurs onglets échouaient.
- **Glossaire** : les variantes d'un même terme sont fusionnées (Sapin II / Loi Sapin II, APP fraud…).

### Nouveautés
- Mention « © 2026 Mackenson Cineus — Compliance Watch Platform » et avertissement de
  non-responsabilité, en petits caractères, sur chaque page et dans chaque export.

### Organisation
- Code restructuré en package `cwp/` (core, services, data, exports, ui/pages). `app.py` passe de
  1 050 à 85 lignes. Les fichiers en double (`regwatch (1).py`, etc.) ont été remplacés par
  leur version la plus récente. Tests automatiques ajoutés (32 tests).
