"""
cwp.content.glossaire_fraudes — 50 typologies de fraude, blanchiment et contournement les plus courantes.

Chaque fiche : nom, alias, catégorie, description (≈3 lignes),
identifier (signaux dans une transaction, ≈2 lignes), combattre (parades, ≈2 lignes).
Sources d'inspiration : typologies GAFI, TRACFIN, Europol, ACPR, Banque de France (OSMP).
"""

CATEGORIES = [
    "Blanchiment",
    "Financement du terrorisme",
    "Contournement de sanctions",
    "Fraude aux paiements",
    "Fraude identitaire & crédit",
    "Escroqueries",
    "Fraude fiscale",
    "Corruption & fraude interne",
    "Abus de marché",
    "Traite & exploitation",
]

FRAUDES = [
    # ------------------------------------------------------------------ Blanchiment
    {"nom": "Schtroumpfage", "alias": "Smurfing", "categorie": "Blanchiment",
     "description": "Fractionnement d'une grosse somme d'origine illicite en multiples petits dépôts effectués "
                    "par plusieurs personnes (les « schtroumpfs »), sur un ou plusieurs comptes, pour rester "
                    "sous les seuils de déclaration et de vigilance.",
     "identifier": "Nombreux dépôts espèces de montants proches et juste sous les seuils, réalisés par des tiers "
                   "différents, dans des agences variées, sur une période courte.",
     "combattre": "Agréger les dépôts par bénéficiaire et par période, scénario « multi-déposants », "
                  "vérifier l'identité des déposants et déclarer à TRACFIN."},
    {"nom": "Structuration", "alias": "Fractionnement", "categorie": "Blanchiment",
     "description": "Le client lui-même découpe ses opérations (dépôts, retraits, virements) en tranches "
                   "inférieures aux seuils réglementaires ou internes afin d'éviter les contrôles, "
                   "les justificatifs ou les déclarations automatiques.",
     "identifier": "Série d'opérations répétées à 9 000-9 900 €, rythme régulier, cumul important "
                   "sans justification économique, retraits fractionnés sur plusieurs DAB.",
     "combattre": "Règles de cumul glissant (jour/semaine/mois), alertes « juste sous le seuil », "
                  "demande de justificatifs et revue du profil de risque."},
    {"nom": "Cuckoo smurfing", "alias": "Blanchiment « coucou »", "categorie": "Blanchiment",
     "description": "Des fonds illicites sont déposés sur le compte d'une personne innocente qui attend "
                    "un transfert légitime de l'étranger ; un faux remettant (souvent un hawaladar) "
                    "« paie » ainsi le bénéficiaire et récupère les fonds propres à l'étranger.",
     "identifier": "Crédits espèces fractionnés par des tiers inconnus du client, au lieu du virement "
                   "international attendu, souvent dans plusieurs villes.",
     "combattre": "Interroger le client sur l'origine des dépôts, contrôler les sociétés de transfert "
                  "utilisées et surveiller les dépôts de tiers sur comptes de particuliers."},
    {"nom": "Blanchiment par le commerce", "alias": "TBML, sur/sous-facturation", "categorie": "Blanchiment",
     "description": "Les flux illicites sont justifiés par des échanges commerciaux fictifs ou maquillés : "
                    "sur- ou sous-facturation, facturation multiple, fausse description des marchandises, "
                    "afin de transférer de la valeur entre pays.",
     "identifier": "Prix unitaires incohérents avec le marché, marchandises sans lien avec l'activité, "
                   "paiements par des tiers, routes commerciales illogiques ou pays à risque.",
     "combattre": "Contrôle documentaire (factures, connaissements), comparaison aux prix de marché, "
                  "vigilance renforcée sur le trade finance et les paiements de tiers."},
    {"nom": "Sociétés écrans", "alias": "Shell companies", "categorie": "Blanchiment",
     "description": "Entités sans activité économique réelle, souvent immatriculées dans des juridictions "
                    "opaques, utilisées pour faire transiter des fonds et masquer l'identité du "
                    "bénéficiaire effectif.",
     "identifier": "Société récente, adresse de domiciliation, pas de salariés, flux entrants/sortants "
                   "équivalents et rapides, contreparties offshore, objet social vague.",
     "combattre": "KYB approfondi (registres, BE, substance), recoupement avec les comptes publiés, "
                  "refus ou sortie de relation si la substance n'est pas démontrée."},
    {"nom": "Prête-nom", "alias": "Homme de paille", "categorie": "Blanchiment",
     "description": "Une personne accepte, contre rémunération ou sous pression, d'apparaître comme "
                    "titulaire d'un compte, d'une société ou d'un bien pour le compte du véritable "
                    "propriétaire qui souhaite rester caché.",
     "identifier": "Profil (âge, revenus, profession) incompatible avec les montants, procurations "
                   "ou connexions par un tiers, décisions manifestement prises par quelqu'un d'autre.",
     "combattre": "Questionner l'origine et la destination des fonds, analyser procurations et données "
                  "de connexion (IP, appareil), identifier le BE réel."},
    {"nom": "Mules financières", "alias": "Money mules", "categorie": "Blanchiment",
     "description": "Personnes, souvent jeunes ou précaires, recrutées (réseaux sociaux, fausses offres "
                    "d'emploi) pour recevoir des fonds frauduleux sur leur compte et les retransférer "
                    "rapidement, en échange d'une commission.",
     "identifier": "Crédits soudains de tiers inconnus suivis de virements sortants ou retraits quasi "
                   "immédiats, compte jusque-là peu actif, achats de crypto ou de cartes prépayées.",
     "combattre": "Scénarios « entrée-sortie rapide », blocage et rappel des fonds, sensibilisation "
                  "des jeunes clients et coopération inter-banques sur les comptes signalés."},
    {"nom": "Comptes de passage", "alias": "Pass-through / comptes rebond", "categorie": "Blanchiment",
     "description": "Comptes utilisés uniquement comme point de transit : les fonds y entrent et en "
                    "ressortent presque aussitôt, pour multiplier les couches (layering) et "
                    "brouiller la traçabilité.",
     "identifier": "Solde moyen proche de zéro malgré des volumes élevés, entrées et sorties de "
                   "montants quasi identiques, multiples contreparties sans logique commerciale.",
     "combattre": "Indicateur de rotation des fonds (vélocité), analyse de réseau des contreparties, "
                  "vigilance renforcée et sortie de relation si nécessaire."},
    {"nom": "Hawala", "alias": "Systèmes de compensation informels", "categorie": "Blanchiment",
     "description": "Réseau de transfert de valeur fondé sur la confiance entre intermédiaires : l'argent "
                    "ne circule pas physiquement, les positions sont compensées plus tard (commerce, "
                    "espèces). Légal dans certains pays, souvent non agréé en Europe.",
     "identifier": "Commerce (épicerie, téléphonie, voyage) recevant des espèces de nombreux particuliers "
                   "puis émettant des virements vers des pays à risque sans lien avec son activité.",
     "combattre": "Vérifier l'agrément de prestataire de paiement, comparer les flux au chiffre d'affaires "
                  "déclaré, déclaration de soupçon pour exercice illégal."},
    {"nom": "Blanchiment immobilier", "alias": "", "categorie": "Blanchiment",
     "description": "Acquisition de biens immobiliers avec des fonds illicites, parfois via des SCI ou "
                    "des sociétés étrangères, avec sous-évaluation, apport en espèces ou revente rapide "
                    "pour « justifier » une plus-value.",
     "identifier": "Apport personnel élevé sans origine documentée, paiement par des tiers, achat via "
                   "structure opaque, revente rapide avec écart de prix important.",
     "combattre": "Justificatifs d'origine des fonds et du patrimoine, identification des BE de la SCI, "
                  "coordination avec notaires et déclarations TRACFIN."},
    {"nom": "Blanchiment par le jeu", "alias": "Casinos, paris en ligne", "categorie": "Blanchiment",
     "description": "Conversion d'espèces illicites en gains apparents : achat de jetons ou dépôt sur un "
                    "compte de jeu, mise minimale, puis demande de remboursement par chèque ou virement "
                    "présenté comme un gain.",
     "identifier": "Crédits « gains de jeu » répétés, dépôts suivis de retraits sans activité réelle de "
                   "jeu, rachat de tickets gagnants, comptes de jeu multiples.",
     "combattre": "Exiger les relevés de l'opérateur de jeu, croiser avec les dépôts espèces, scénario "
                  "dédié aux crédits issus d'opérateurs de jeux."},
    {"nom": "Loan-back", "alias": "Prêt adossé", "categorie": "Blanchiment",
     "description": "Le blanchisseur se « prête » à lui-même ses propres fonds illicites, placés à "
                    "l'étranger, via une société ou une banque complaisante ; le remboursement du prêt "
                    "fictif légitime ensuite les flux et peut même être déductible.",
     "identifier": "Prêt accordé par une entité offshore liée à l'emprunteur, conditions hors marché, "
                   "garantie en espèces, remboursements irréguliers ou absents.",
     "combattre": "Analyser le prêteur (BE, liens), exiger le contrat et l'origine des fonds, "
                  "vigilance renforcée sur les prêts intragroupe offshore."},
    {"nom": "Mixeurs & chain-hopping", "alias": "Crypto-blanchiment", "categorie": "Blanchiment",
     "description": "Utilisation de mixeurs/tumblers, de privacy coins et de conversions successives entre "
                    "blockchains (bridges, swaps) pour casser la traçabilité des crypto-actifs avant "
                    "leur conversion en monnaie fiat.",
     "identifier": "Fonds provenant d'adresses exposées à des mixeurs ou services à risque, multiples "
                   "conversions rapides, retraits fiat juste après réception.",
     "combattre": "Outil d'analyse on-chain (scoring d'adresses), application de la travel rule (TFR), "
                  "gel et déclaration en cas d'exposition à risque élevé."},
    {"nom": "Biens de luxe & œuvres d'art", "alias": "", "categorie": "Blanchiment",
     "description": "Achat de biens à forte valeur et faciles à transporter (art, montres, bijoux, voitures) "
                    "avec des fonds illicites, puis revente ou mise en garantie ; le marché de l'art "
                    "offre opacité et prix subjectifs.",
     "identifier": "Paiements élevés à des galeries, ventes aux enchères ou concessionnaires, paiements "
                   "par des tiers ou en espèces, revente rapide à l'étranger.",
     "combattre": "Vigilance sur les marchands d'art et de luxe (assujettis LCB-FT), justification de "
                  "l'origine des fonds, contrôle des paiements de tiers."},
    {"nom": "Mélange de fonds", "alias": "Commingling", "categorie": "Blanchiment",
     "description": "Les fonds illicites sont injectés dans la caisse d'un commerce manipulant beaucoup "
                    "d'espèces (restaurant, laverie, car wash) et déclarés comme recettes légitimes, "
                    "se mêlant au chiffre d'affaires réel.",
     "identifier": "Dépôts espèces disproportionnés par rapport à la taille ou au secteur, recettes "
                   "stables quels que soient la saison ou les jours de fermeture.",
     "combattre": "Comparer les dépôts aux ratios sectoriels et aux liasses fiscales, visite sur site, "
                  "suivi des évolutions brutales du chiffre d'affaires espèces."},
    # -------------------------------------------------------- Financement du terrorisme
    {"nom": "Détournement d'OBNL", "alias": "Associations, ONG", "categorie": "Financement du terrorisme",
     "description": "Utilisation abusive d'organismes à but non lucratif (associations caritatives, "
                    "culturelles, religieuses) pour collecter des dons ou transférer des fonds vers des "
                    "groupes terroristes ou zones de conflit.",
     "identifier": "Virements vers zones de conflit ou pays voisins sans projet documenté, retraits espèces "
                   "importants, dons en espèces non tracés, dirigeants liés à des personnes listées.",
     "combattre": "Analyse des statuts, projets et partenaires terrain, filtrage des dirigeants et "
                  "bénéficiaires, approche par les risques (recommandation 8 du GAFI)."},
    {"nom": "Micro-financement du terrorisme", "alias": "Autofinancement, cagnottes",
     "categorie": "Financement du terrorisme",
     "description": "Financement par petits montants difficiles à repérer : crédits à la consommation, "
                    "cagnottes en ligne, cartes prépayées, ventes de biens, pour financer un départ "
                    "ou une action individuelle.",
     "identifier": "Souscription de plusieurs crédits puis retrait total, liquidation soudaine de l'épargne, "
                   "achats de billets vers zones à risque, cagnottes aux finalités floues.",
     "combattre": "Scénarios comportementaux (rupture de profil), filtrage gel des avoirs (DG Trésor), "
                  "remontée rapide à TRACFIN et coopération avec les autorités."},
    # ------------------------------------------------------- Contournement de sanctions
    {"nom": "Contournement via pays tiers", "alias": "Transbordement, réexportation",
     "categorie": "Contournement de sanctions",
     "description": "Des biens ou paiements destinés à un pays sanctionné transitent par un pays tiers "
                    "(hubs commerciaux régionaux) via des intermédiaires, pour masquer la destination "
                    "finale ou l'utilisateur final.",
     "identifier": "Exportations de biens à double usage vers des pays de transit connus, pic soudain "
                   "d'activité d'un nouveau client, adresses de livraison différentes du payeur.",
     "combattre": "Clause « no re-export », vérification de l'utilisateur final, filtrage des biens "
                  "(codes douaniers à haut risque) et des contreparties."},
    {"nom": "Wire stripping", "alias": "Suppression d'informations", "categorie": "Contournement de sanctions",
     "description": "Retrait ou modification volontaire des informations d'un message de paiement "
                    "(nom, adresse, pays, banque) pour éviter le déclenchement du filtrage sanctions "
                    "chez les banques intermédiaires.",
     "identifier": "Champs donneur d'ordre ou bénéficiaire incomplets ou génériques, références "
                   "modifiées entre deux messages, demandes du client de « ne pas mentionner » un pays.",
     "combattre": "Contrôle de complétude (TFR), rejet des messages incomplets, audit des "
                  "réparations manuelles de messages et formation des opérateurs."},
    {"nom": "Contournement par la détention", "alias": "Règle des 50 % / contrôle",
     "categorie": "Contournement de sanctions",
     "description": "Des personnes sanctionnées transfèrent leurs parts sous les seuils de détention ou "
                    "à des proches, ou conservent le contrôle de fait d'une société, pour que celle-ci "
                    "échappe au gel des avoirs.",
     "identifier": "Cession récente de parts à des proches ou trusts, actionnariat juste sous 50 %, "
                   "dirigeant lié à une personne listée, changement de nom de la société.",
     "combattre": "Cartographie de l'actionnariat et du contrôle, recherche des liens familiaux, "
                  "suivi des modifications post-sanction et filtrage étendu aux BE."},
    # ------------------------------------------------------------ Fraude aux paiements
    {"nom": "Fraude au président", "alias": "FOVI", "categorie": "Fraude aux paiements",
     "description": "L'escroc se fait passer pour un dirigeant (mail, téléphone, parfois deepfake) et "
                    "ordonne à un collaborateur un virement urgent et confidentiel vers un compte "
                    "étranger, en invoquant une opération secrète.",
     "identifier": "Virement inhabituel, urgent, vers un nouveau bénéficiaire étranger, demande de "
                   "contournement des procédures, émis hors des circuits habituels.",
     "combattre": "Double validation et contre-appel sur un numéro connu, délai sur nouveaux "
                  "bénéficiaires, sensibilisation des équipes comptables."},
    {"nom": "Fraude au changement de RIB", "alias": "BEC, faux fournisseur", "categorie": "Fraude aux paiements",
     "description": "Usurpation de l'identité d'un fournisseur ou d'un bailleur (souvent via une boîte "
                    "mail piratée) pour demander la modification des coordonnées bancaires et détourner "
                    "les paiements suivants.",
     "identifier": "Changement de RIB récent suivi d'un paiement important, IBAN dans un autre pays "
                   "que le fournisseur, nom du titulaire différent de la raison sociale.",
     "combattre": "Vérification de la concordance IBAN/nom (VoP), confirmation par un canal "
                  "indépendant, gel temporaire des nouveaux RIB."},
    {"nom": "Hameçonnage", "alias": "Phishing", "categorie": "Fraude aux paiements",
     "description": "Messages frauduleux (mail, SMS « smishing ») imitant une banque, un service public "
                    "ou un livreur pour dérober identifiants, données de carte ou codes, ensuite "
                    "utilisés pour payer ou vider le compte.",
     "identifier": "Connexion depuis un nouvel appareil ou pays, ajout de bénéficiaire puis virement "
                   "rapide, paiements CNP successifs juste après une connexion inhabituelle.",
     "combattre": "Authentification forte (DSP2), scoring de session, notifications en temps réel "
                  "et campagnes de sensibilisation des clients."},
    {"nom": "Faux conseiller bancaire", "alias": "Vishing, spoofing", "categorie": "Fraude aux paiements",
     "description": "Le fraudeur appelle la victime en usurpant le numéro de la banque, prétend bloquer "
                    "une fraude et l'amène à valider elle-même des opérations ou à remettre sa carte "
                    "à un faux coursier.",
     "identifier": "Validations d'authentification forte pendant un appel, virements vers comptes "
                   "« sécurisés », ajout de carte à un wallet mobile depuis un nouvel appareil.",
     "combattre": "Message clair : la banque ne demande jamais de valider, contrôle du contexte "
                  "d'authentification, délai et rappel client sur opérations atypiques."},
    {"nom": "Fraude à la carte à distance", "alias": "CNP", "categorie": "Fraude aux paiements",
     "description": "Utilisation de données de carte volées (fuites, phishing, dark web) pour des achats "
                    "en ligne sans présence physique de la carte, souvent revendus ou convertis en "
                    "biens facilement liquidables.",
     "identifier": "Multiples petites transactions test, achats chez des marchands à risque, adresse "
                   "de livraison différente, échecs 3-D Secure répétés.",
     "combattre": "3-D Secure systématique, scoring des transactions, limitation de vélocité et "
                  "remplacement rapide des cartes compromises."},
    {"nom": "Skimming", "alias": "Copie de carte", "categorie": "Fraude aux paiements",
     "description": "Installation d'un dispositif sur un DAB ou un terminal de paiement pour copier la "
                    "piste magnétique et capter le code ; les données servent à fabriquer des cartes "
                    "clonées utilisées à l'étranger.",
     "identifier": "Retraits dans un pays sans puce EMV peu après un usage local, point de compromission "
                   "commun à plusieurs clients, retraits la nuit en série.",
     "combattre": "Détection des points de compromission, blocage géographique, cartes EMV sans "
                  "piste active et inspection des automates."},
    {"nom": "Prise de contrôle de compte", "alias": "ATO", "categorie": "Fraude aux paiements",
     "description": "Le fraudeur accède au compte de la victime (identifiants volés, malware, "
                    "ingénierie sociale), change les coordonnées de contact puis vide le compte ou "
                    "souscrit des produits à son nom.",
     "identifier": "Modification de mail, téléphone ou mot de passe suivie d'opérations sortantes, "
                   "nouvel appareil, empreinte de navigateur inhabituelle.",
     "combattre": "Délai de sécurité après modification des données sensibles, biométrie "
                  "comportementale, alerte au client sur l'ancien canal."},
    {"nom": "SIM swapping", "alias": "Échange de carte SIM", "categorie": "Fraude aux paiements",
     "description": "Le fraudeur obtient de l'opérateur le transfert du numéro de la victime sur une "
                    "nouvelle SIM, puis reçoit les codes SMS d'authentification pour valider des "
                    "virements ou réinitialiser des accès.",
     "identifier": "Perte soudaine de réseau du client, changement récent de SIM signalé par "
                   "l'opérateur, authentification SMS depuis un nouvel appareil puis virement.",
     "combattre": "Interroger les API opérateurs (date de changement de SIM), privilégier "
                  "l'authentification via application, bloquer les opérations sensibles post-swap."},
    {"nom": "Fraude au paiement autorisé", "alias": "APP fraud", "categorie": "Fraude aux paiements",
     "description": "La victime, manipulée (faux investissement, achat fictif, urgence), émet elle-même "
                    "le virement vers le compte du fraudeur ; le paiement étant authentifié, il est "
                    "difficile à contester.",
     "identifier": "Premier virement vers un bénéficiaire inconnu, montant élevé par rapport à "
                   "l'historique, virement instantané, libellé évoquant un placement ou un dépôt.",
     "combattre": "Vérification du bénéficiaire, avertissements dynamiques, délai de réflexion "
                  "sur les montants atypiques et rappel rapide des fonds."},
    {"nom": "Chargeback frauduleux", "alias": "Friendly fraud", "categorie": "Fraude aux paiements",
     "description": "Un client effectue un achat légitime puis conteste la transaction auprès de sa "
                    "banque (non-réception, non-reconnaissance) afin d'obtenir le remboursement tout "
                    "en conservant le bien ou le service.",
     "identifier": "Taux de contestation élevé pour un même porteur, contestations après livraison "
                   "confirmée, répétition chez plusieurs marchands.",
     "combattre": "Preuves de livraison et d'authentification, listes de contestataires récurrents, "
                  "gestion structurée des litiges avec les réseaux de cartes."},
    {"nom": "Fraude au chèque", "alias": "Falsification, contrefaçon", "categorie": "Fraude aux paiements",
     "description": "Chèques volés, falsifiés (montant ou bénéficiaire modifié) ou contrefaits, déposés "
                    "puis rapidement exploités avant le rejet ; la France reste particulièrement "
                    "exposée à ce moyen de paiement.",
     "identifier": "Remise de chèque élevée sur compte récent, retrait ou virement immédiat après "
                   "encaissement, incohérence entre émetteur et activité du client.",
     "combattre": "Délai d'indisponibilité des fonds, contrôle image des chèques (outils d'analyse), "
                  "vérification auprès de la banque tirée pour les gros montants."},
    {"nom": "Cavalerie", "alias": "Kiting", "categorie": "Fraude aux paiements",
     "description": "Jeu d'écritures croisées entre plusieurs comptes ou banques (chèques, effets, "
                    "virements) pour créer artificiellement de la trésorerie en exploitant les délais "
                    "d'encaissement et masquer une insolvabilité.",
     "identifier": "Remises croisées de montants similaires entre comptes liés, soldes artificiellement "
                   "gonflés, rejets fréquents, absence de flux commerciaux réels.",
     "combattre": "Analyse des flux entre comptes liés, limitation des avances sur encaissement, "
                  "surveillance des rejets et des remises circulaires."},
    # ------------------------------------------------------ Fraude identitaire & crédit
    {"nom": "Usurpation d'identité", "alias": "", "categorie": "Fraude identitaire & crédit",
     "description": "Utilisation des données personnelles d'une personne réelle (pièce d'identité volée, "
                    "fuites de données) pour ouvrir des comptes, souscrire des crédits ou commettre "
                    "des fraudes en son nom.",
     "identifier": "Ouverture à distance avec coordonnées récentes, mail ou téléphone partagés avec "
                   "d'autres dossiers, demandes de crédit multiples rapprochées.",
     "combattre": "Vérification d'identité à distance certifiée (PVID), contrôle des documents perdus/"
                  "volés, détection des données partagées entre dossiers."},
    {"nom": "Identité synthétique", "alias": "Synthetic ID", "categorie": "Fraude identitaire & crédit",
     "description": "Création d'une identité fictive combinant des éléments réels et inventés, entretenue "
                    "patiemment pour bâtir un historique de crédit avant de souscrire un maximum de "
                    "financements et disparaître.",
     "identifier": "Identité sans historique ni empreinte numérique, données incohérentes entre "
                   "sources, augmentation progressive des plafonds puis tirage maximal.",
     "combattre": "Recoupement multi-sources (données administratives, opérateurs), analyse de liens "
                  "entre dossiers et revue manuelle des profils « trop parfaits »."},
    {"nom": "Fraude documentaire", "alias": "Faux justificatifs", "categorie": "Fraude identitaire & crédit",
     "description": "Production de documents falsifiés ou fabriqués (pièce d'identité, bulletin de "
                    "salaire, avis d'imposition, Kbis, relevés) pour ouvrir un compte, obtenir un "
                    "crédit ou justifier l'origine de fonds.",
     "identifier": "Métadonnées PDF suspectes, polices ou calculs incohérents, revenus déclarés sans "
                   "rapport avec les flux observés sur le compte.",
     "combattre": "Outils de détection de falsification, vérification à la source (2D-Doc, API impôts), "
                  "rapprochement revenus déclarés / flux réels."},
    {"nom": "Bust-out", "alias": "Fraude au crédit organisée", "categorie": "Fraude identitaire & crédit",
     "description": "Le fraudeur se comporte en bon payeur pour gagner la confiance de plusieurs "
                    "établissements, augmente ses plafonds, puis utilise d'un coup toutes ses lignes "
                    "de crédit et cesse tout remboursement.",
     "identifier": "Hausse soudaine et simultanée de l'utilisation des crédits, avances d'espèces, "
                   "achats de biens revendables, paiements par chèques sans provision.",
     "combattre": "Surveillance de l'utilisation des lignes, consultation des fichiers d'incidents, "
                  "réduction préventive des plafonds en cas de rupture de comportement."},
    # ------------------------------------------------------------------ Escroqueries
    {"nom": "Arnaque sentimentale", "alias": "Romance scam", "categorie": "Escroqueries",
     "description": "Un escroc noue une relation amoureuse en ligne avec la victime, souvent isolée, "
                    "puis invente des urgences (frais médicaux, douane, billet d'avion) pour obtenir "
                    "des virements répétés.",
     "identifier": "Virements récurrents vers l'étranger ou mandats cash au profit d'un même tiers, "
                   "client âgé ou vulnérable, montants croissants, libellés « prêt » ou « aide ».",
     "combattre": "Dialogue avec le client par un conseiller formé, alerte sur les bénéficiaires "
                  "signalés, refus des opérations manifestement frauduleuses."},
    {"nom": "Faux placements", "alias": "Fraude à l'investissement", "categorie": "Escroqueries",
     "description": "Offres d'investissement fictives (forex, crypto, livrets, or, vin) aux rendements "
                    "attractifs, proposées par des sites non autorisés usurpant parfois des acteurs "
                    "connus, qui encaissent les fonds puis disparaissent.",
     "identifier": "Virements vers des plateformes absentes des registres AMF/ACPR, bénéficiaires "
                   "dans des pays sans lien avec l'offre, achats de crypto sur demande d'un « conseiller ».",
     "combattre": "Contrôle des listes noires AMF/ACPR, avertissement au client, blocage des "
                  "bénéficiaires signalés et partage d'information sectoriel."},
    {"nom": "Pig butchering", "alias": "Sha Zhu Pan", "categorie": "Escroqueries",
     "description": "Escroquerie hybride mêlant relation de confiance (amicale ou amoureuse) et faux "
                    "investissement crypto : la victime voit de faux gains sur une plateforme truquée "
                    "et investit toujours plus.",
     "identifier": "Achats de crypto croissants et répétés par un client sans antécédent, liquidation "
                   "d'épargne ou souscription de crédits pour financer ces achats.",
     "combattre": "Analyse des adresses de destination, conversation de prévention avec le client, "
                  "signalement aux plateformes et à PHAROS / police."},
    {"nom": "Fraude à l'avance de frais", "alias": "Escroquerie 419", "categorie": "Escroqueries",
     "description": "La victime se voit promettre une grosse somme (héritage, gain, prêt, contrat) à "
                    "condition de payer d'abord des frais (taxes, avocat, déblocage) qui n'ont "
                    "aucune contrepartie.",
     "identifier": "Paiements successifs vers des tiers étrangers avec libellés « frais », « taxe » ou "
                   "« déblocage », souvent par mandat ou crypto.",
     "combattre": "Sensibilisation, détection des libellés et bénéficiaires types, entretien avec "
                  "le client avant exécution des opérations à risque."},
    {"nom": "Système de Ponzi", "alias": "Pyramide financière", "categorie": "Escroqueries",
     "description": "Les rendements versés aux anciens investisseurs proviennent des apports des "
                    "nouveaux et non d'une activité réelle ; le système s'effondre dès que les "
                    "entrées ralentissent.",
     "identifier": "Société collectant de nombreux apports de particuliers et versant des sommes "
                   "régulières à d'autres particuliers, sans activité économique visible.",
     "combattre": "Analyse des flux entrants/sortants de l'entité, vérification des agréments "
                  "(CIF, PSI), déclaration de soupçon et alerte AMF."},
    {"nom": "Faux site marchand", "alias": "Non-livraison", "categorie": "Escroqueries",
     "description": "Boutiques en ligne ou annonces fictives (produits à prix cassés, locations, "
                    "animaux) qui encaissent les paiements sans jamais livrer, souvent avec des "
                    "comptes de réception changeant régulièrement.",
     "identifier": "Compte recevant de nombreux petits virements de particuliers aux libellés de "
                   "commande, puis retraits ou transferts rapides, plaintes clients.",
     "combattre": "Surveillance des comptes collecteurs, KYC marchand renforcé chez les PSP, "
                  "fermeture rapide sur signalements concordants."},
    # ------------------------------------------------------------------ Fraude fiscale
    {"nom": "Carrousel TVA", "alias": "Fraude MTIC", "categorie": "Fraude fiscale",
     "description": "Chaîne de sociétés intracommunautaires où un « opérateur défaillant » collecte la "
                    "TVA sans la reverser puis disparaît, tandis que d'autres maillons en réclament "
                    "le remboursement sur les mêmes marchandises.",
     "identifier": "Sociétés récentes à fort chiffre d'affaires immédiat, flux circulaires entre "
                   "pays de l'UE, biens à forte valeur (téléphones, quotas carbone), marges nulles.",
     "combattre": "Analyse des flux circulaires, vérification des numéros de TVA (VIES), "
                  "vigilance sur les sociétés à croissance anormale et déclaration TRACFIN."},
    {"nom": "Fraude fiscale offshore", "alias": "Dissimulation d'avoirs", "categorie": "Fraude fiscale",
     "description": "Dissimulation de revenus ou de patrimoine au fisc via des comptes, trusts ou "
                    "sociétés dans des juridictions peu coopératives, avec rapatriement discret des "
                    "fonds (cartes, prêts, factures).",
     "identifier": "Virements réguliers vers des juridictions à faible fiscalité, cartes émises à "
                   "l'étranger utilisées localement, structures sans substance.",
     "combattre": "Exploitation des échanges automatiques (CRS/FATCA), justificatifs fiscaux, "
                  "identification des BE et des liens avec des structures offshore."},
    # ------------------------------------------------------ Corruption & fraude interne
    {"nom": "Corruption", "alias": "Pots-de-vin, commissions occultes", "categorie": "Corruption & fraude interne",
     "description": "Versement d'avantages indus à un agent public ou privé pour obtenir un contrat, "
                    "une autorisation ou une décision favorable, souvent maquillé en commission, "
                    "honoraires de conseil ou don.",
     "identifier": "Paiements à des intermédiaires sans prestation réelle, commissions élevées, flux "
                   "vers des PPE ou leurs proches, factures de « conseil » vagues.",
     "combattre": "Vigilance PPE, due diligence des intermédiaires (Sapin II), contrôle des "
                  "justificatifs de prestation et cartographie du risque corruption."},
    {"nom": "Abus de biens sociaux", "alias": "Détournement de fonds", "categorie": "Corruption & fraude interne",
     "description": "Un dirigeant utilise les fonds ou le crédit de la société à des fins personnelles "
                    "ou au profit d'une autre entité dans laquelle il est intéressé, au détriment de "
                    "la société et de ses associés.",
     "identifier": "Virements de la société vers les comptes personnels du dirigeant ou de ses proches, "
                   "dépenses personnelles réglées par la société, prêts non documentés.",
     "combattre": "Analyse des flux entre comptes professionnels et personnels, demande de "
                  "justificatifs, déclaration de soupçon le cas échéant."},
    {"nom": "Fraude interne", "alias": "Collaborateur malveillant", "categorie": "Corruption & fraude interne",
     "description": "Un salarié exploite ses accès pour détourner des fonds (comptes dormants, "
                    "virements fictifs), consulter ou vendre des données clients, ou contourner les "
                    "contrôles au profit de complices.",
     "identifier": "Opérations sur comptes dormants, modifications de données clients sans demande, "
                   "dérogations répétées par le même agent, accès hors horaires.",
     "combattre": "Séparation des tâches, principe des quatre yeux, revue des habilitations, "
                  "congés obligatoires et analyse des logs d'accès."},
    {"nom": "Fraude aux aides publiques", "alias": "Subventions, prêts garantis", "categorie": "Corruption & fraude interne",
     "description": "Obtention indue d'aides publiques (subventions, prêts garantis, chômage partiel, "
                    "primes énergétiques) par fausses déclarations ou sociétés fictives, puis "
                    "détournement des fonds reçus.",
     "identifier": "Société récente ou sans activité recevant une aide importante, fonds aussitôt "
                   "transférés vers l'étranger ou retirés, absence de dépenses opérationnelles.",
     "combattre": "Contrôle de l'éligibilité et de la substance, suivi de l'usage des fonds après "
                  "versement, coopération avec les organismes payeurs."},
    # ------------------------------------------------------------------ Abus de marché
    {"nom": "Délit d'initié & manipulation", "alias": "Abus de marché (MAR)", "categorie": "Abus de marché",
     "description": "Utilisation d'informations privilégiées non publiques pour négocier des titres, ou "
                    "manipulation des cours (pump and dump, spoofing, layering d'ordres) pour en "
                    "tirer un profit indu.",
     "identifier": "Achats importants juste avant une annonce, ordres passés puis annulés en masse, "
                   "proximité du donneur d'ordre avec l'émetteur, gains anormaux.",
     "combattre": "Surveillance des ordres et transactions, listes d'initiés, déclarations "
                  "d'opérations suspectes (STOR) à l'AMF."},
    # ---------------------------------------------------------- Traite & exploitation
    {"nom": "Traite des êtres humains", "alias": "Exploitation sexuelle ou par le travail",
     "categorie": "Traite & exploitation",
     "description": "Exploitation de personnes (prostitution forcée, travail forcé, servitude) dont les "
                    "revenus sont collectés et blanchis par les réseaux ; les victimes servent souvent "
                    "aussi de titulaires de comptes.",
     "identifier": "Plusieurs comptes avec la même adresse ou le même téléphone, dépenses de nuitées "
                   "hôtelières et d'annonces en ligne, retraits rapides par un tiers.",
     "combattre": "Indicateurs dédiés (guides TRACFIN / GAFI), formation des équipes, analyse des "
                  "liens entre comptes et déclaration prioritaire."},
]

assert len(FRAUDES) == 50, len(FRAUDES)
