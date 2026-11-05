"""
Glossaire pédagogique CWP — termes rédigés (une ligne = « terme | catégorie | définition »).
Pour ajouter un terme : ajouter une ligne ; aucune autre modification nécessaire.
Les définitions sont des définitions de travail : vérifier les textes officiels pour tout usage formel.
"""

RAW = r"""
# ===================== FINANCE DE MARCHÉ =====================
Action | Finance de marché | Titre de propriété représentant une fraction du capital d'une société, donnant droit à dividende, vote et information.
Obligation | Finance de marché | Titre de créance négociable émis par un État ou une entreprise, rémunéré par un coupon et remboursé à l'échéance.
Coupon | Finance de marché | Intérêt périodique versé au porteur d'une obligation, exprimé en pourcentage du nominal.
Nominal (valeur faciale) | Finance de marché | Montant de référence d'un titre de créance servant au calcul des intérêts et au remboursement.
Rendement actuariel | Finance de marché | Taux qui égalise le prix d'une obligation et la valeur actuelle de ses flux futurs ; mesure la rentabilité si le titre est conservé jusqu'à l'échéance.
Duration | Finance de marché | Durée de vie moyenne pondérée des flux d'une obligation ; mesure approximative de sa sensibilité aux variations de taux.
Sensibilité (taux) | Finance de marché | Variation relative du prix d'une obligation pour une variation de 1 point des taux d'intérêt.
Convexité | Finance de marché | Mesure de la courbure de la relation prix-taux d'une obligation, complétant la duration pour les fortes variations de taux.
Courbe des taux | Finance de marché | Représentation des taux d'intérêt en fonction de leur maturité pour un même émetteur ou une même classe de risque.
Spread de crédit | Finance de marché | Écart de rendement entre une obligation risquée et un titre sans risque de même maturité, rémunérant le risque de défaut.
Produit dérivé | Finance de marché | Instrument dont la valeur dépend d'un actif sous-jacent (action, taux, devise, matière première, indice).
Contrat à terme (future) | Finance de marché | Engagement standardisé, négocié sur un marché organisé, d'acheter ou vendre un sous-jacent à un prix et une date fixés.
Forward | Finance de marché | Contrat à terme de gré à gré, non standardisé, conclu entre deux contreparties.
Option d'achat (call) | Finance de marché | Droit, et non obligation, d'acheter un sous-jacent à un prix d'exercice donné, moyennant une prime.
Option de vente (put) | Finance de marché | Droit, et non obligation, de vendre un sous-jacent à un prix d'exercice donné, moyennant une prime.
Swap | Finance de marché | Contrat d'échange de flux financiers entre deux parties (taux fixe contre variable, devises, crédit…).
CDS (Credit Default Swap) | Finance de marché | Dérivé de crédit par lequel l'acheteur paie une prime pour être indemnisé en cas d'événement de crédit sur une entité de référence.
Volatilité | Finance de marché | Mesure de l'amplitude des variations du prix d'un actif, généralement l'écart-type annualisé des rendements.
Value at Risk (VaR) | Finance de marché | Perte maximale potentielle d'un portefeuille sur un horizon donné avec un niveau de confiance donné.
Expected Shortfall | Finance de marché | Perte moyenne au-delà de la VaR ; mesure de risque de queue retenue par la FRTB.
Bêta | Finance de marché | Sensibilité de la rentabilité d'un titre aux mouvements du marché dans son ensemble.
Alpha | Finance de marché | Surperformance d'un portefeuille par rapport à la rentabilité attendue compte tenu de son risque.
Ratio de Sharpe | Finance de marché | Rentabilité excédentaire par unité de volatilité ; mesure la performance ajustée du risque.
MEDAF (CAPM) | Finance de marché | Modèle reliant la rentabilité attendue d'un actif à son bêta et à la prime de risque du marché.
Liquidité de marché | Finance de marché | Capacité à acheter ou vendre rapidement un actif sans impact significatif sur son prix.
Fourchette (bid-ask spread) | Finance de marché | Écart entre le meilleur prix acheteur et le meilleur prix vendeur d'un instrument.
Teneur de marché (market maker) | Finance de marché | Intermédiaire qui affiche en continu des prix d'achat et de vente pour assurer la liquidité.
Marché primaire | Finance de marché | Marché de l'émission des titres nouveaux, où l'émetteur lève des fonds.
Marché secondaire | Finance de marché | Marché d'échange des titres déjà émis entre investisseurs.
Introduction en bourse (IPO) | Finance de marché | Première cotation des actions d'une société sur un marché réglementé.
OPA / OPE | Finance de marché | Offre publique d'achat (en numéraire) ou d'échange (en titres) visant à prendre le contrôle d'une société cotée.
Délit d'initié | Finance de marché | Utilisation ou communication d'une information privilégiée pour réaliser des opérations sur un instrument financier.
Manipulation de cours | Finance de marché | Opérations ou diffusion d'informations visant à fixer un cours à un niveau anormal ou artificiel.
Spoofing | Finance de marché | Passation d'ordres sans intention de les exécuter pour tromper le marché sur l'offre ou la demande.
Front running | Finance de marché | Opération pour compte propre réalisée en anticipant un ordre client connu, au détriment de ce client.
Abus de marché (MAR) | Finance de marché | Règlement (UE) 596/2014 réprimant opérations d'initiés, divulgation illicite et manipulations de marché.
MiFID II / MiFIR | Finance de marché | Cadre européen des marchés d'instruments financiers : protection des investisseurs, transparence, organisation des marchés.
EMIR | Finance de marché | Règlement européen sur les dérivés de gré à gré : compensation centrale, déclaration aux référentiels centraux, réduction des risques.
Chambre de compensation (CCP) | Finance de marché | Contrepartie centrale qui s'interpose entre acheteur et vendeur pour garantir la bonne fin des transactions.
Règlement-livraison | Finance de marché | Étape post-marché d'échange définitif des titres contre les espèces.
Dépositaire central (CSD) | Finance de marché | Infrastructure qui tient les comptes de titres et assure le règlement-livraison.
Repo (pension livrée) | Finance de marché | Cession temporaire de titres contre liquidités avec engagement de rachat à un prix convenu.
Titrisation | Finance de marché | Transformation d'actifs peu liquides (crédits) en titres négociables adossés à ces actifs.
OPCVM | Finance de marché | Organisme de placement collectif en valeurs mobilières, fonds régi par la directive UCITS.
FIA | Finance de marché | Fonds d'investissement alternatif relevant de la directive AIFM (private equity, immobilier, hedge funds…).
ETF | Finance de marché | Fonds indiciel coté qui réplique la performance d'un indice et se négocie comme une action.
Private equity | Finance de marché | Investissement en capital dans des sociétés non cotées (capital-risque, développement, transmission/LBO).
LBO | Finance de marché | Rachat d'une entreprise financé majoritairement par endettement, remboursé par les flux de la cible.
Hedge fund | Finance de marché | Fonds alternatif utilisant des stratégies variées (levier, vente à découvert, dérivés) visant une performance absolue.
Vente à découvert | Finance de marché | Vente d'un titre emprunté en anticipant une baisse de son cours pour le racheter moins cher.
Effet de levier | Finance de marché | Amplification de l'exposition et des gains ou pertes par l'endettement ou les dérivés.
Appel de marge | Finance de marché | Demande de dépôt de garantie complémentaire lorsque la valeur d'une position se dégrade.
Benchmark (indice de référence) | Finance de marché | Indice servant de référence à la performance d'un portefeuille ou à la fixation de taux (€STR, Euribor).
€STR | Finance de marché | Taux à court terme en euros publié par la BCE, reflétant le coût des emprunts au jour le jour non garantis.
Euribor | Finance de marché | Taux interbancaire de référence de la zone euro pour différentes maturités.
Matières premières (commodities) | Finance de marché | Ressources standardisées (énergie, métaux, agricoles) négociées sur marchés au comptant et à terme.
Change au comptant (spot FX) | Finance de marché | Échange immédiat de deux devises au cours du jour, livrable généralement à J+2.
Couverture (hedging) | Finance de marché | Prise de position destinée à réduire ou neutraliser un risque existant.
Arbitrage | Finance de marché | Exploitation d'écarts de prix entre marchés ou instruments pour réaliser un gain avec un risque limité.
# ===================== ANALYSE FINANCIÈRE & COMPTABILITÉ =====================
Bilan | Analyse financière | État de la situation patrimoniale d'une entreprise à une date : actifs, capitaux propres et dettes.
Compte de résultat | Analyse financière | État récapitulant produits et charges d'un exercice et déterminant le résultat net.
Tableau des flux de trésorerie | Analyse financière | État décrivant les flux de trésorerie liés à l'exploitation, à l'investissement et au financement.
Liasse fiscale | Analyse financière | Ensemble des formulaires fiscaux normalisés déposés avec la déclaration de résultat (2050 à 2059 en France).
Annexe | Analyse financière | Document comptable complétant bilan et compte de résultat par les méthodes et informations significatives.
Chiffre d'affaires | Analyse financière | Montant des ventes de biens et services réalisées avec les tiers dans le cadre de l'activité normale.
Valeur ajoutée | Analyse financière | Richesse créée par l'entreprise : production moins consommations intermédiaires.
EBE / EBITDA | Analyse financière | Excédent brut d'exploitation : résultat d'exploitation avant amortissements, provisions, intérêts et impôts.
Résultat d'exploitation (EBIT) | Analyse financière | Résultat issu de l'activité courante avant charges financières et impôts.
Résultat net | Analyse financière | Bénéfice ou perte de l'exercice après toutes charges, y compris impôt sur les sociétés.
Capacité d'autofinancement (CAF) | Analyse financière | Ressource interne dégagée par l'activité, disponible pour investir, rembourser ou distribuer.
Besoin en fonds de roulement (BFR) | Analyse financière | Besoin de financement du cycle d'exploitation : stocks + créances clients − dettes fournisseurs.
Fonds de roulement | Analyse financière | Excédent des ressources stables sur les emplois stables, finançant le BFR.
Trésorerie nette | Analyse financière | Disponibilités moins concours bancaires courants ; égale au fonds de roulement moins le BFR.
Endettement net | Analyse financière | Dettes financières moins trésorerie et placements disponibles.
Gearing | Analyse financière | Ratio endettement net / capitaux propres mesurant la structure financière.
Levier financier (dette/EBITDA) | Analyse financière | Nombre d'années d'EBITDA nécessaires pour rembourser la dette nette ; indicateur clé des covenants.
Ratio de couverture des intérêts | Analyse financière | EBIT ou EBITDA rapporté aux charges d'intérêts ; capacité à servir la dette.
Ratio de liquidité générale | Analyse financière | Actif circulant / passif circulant ; capacité à honorer les dettes à court terme.
Ratio de liquidité immédiate | Analyse financière | Trésorerie disponible / passif exigible à court terme.
DSO (délai clients) | Analyse financière | Délai moyen d'encaissement des créances clients exprimé en jours de chiffre d'affaires.
DPO (délai fournisseurs) | Analyse financière | Délai moyen de paiement des fournisseurs exprimé en jours d'achats.
Rotation des stocks | Analyse financière | Nombre de jours de stock ou nombre de rotations annuelles ; mesure l'efficacité de la gestion des stocks.
Marge brute | Analyse financière | Chiffre d'affaires moins coût des ventes, rapportée au chiffre d'affaires.
ROE | Analyse financière | Rentabilité des capitaux propres : résultat net / capitaux propres.
ROA | Analyse financière | Rentabilité de l'actif : résultat net / total actif.
ROCE | Analyse financière | Rentabilité des capitaux employés : résultat d'exploitation après impôt / capitaux employés.
Free cash flow | Analyse financière | Flux de trésorerie disponible après investissements, revenant aux apporteurs de capitaux.
Capitaux propres | Analyse financière | Ressources appartenant aux associés : capital, réserves, report à nouveau, résultat.
Capitaux propres négatifs | Analyse financière | Situation où les pertes cumulées excèdent les apports ; signal de fragilité (procédure si inférieurs à la moitié du capital).
Goodwill (écart d'acquisition) | Analyse financière | Différence entre le prix d'acquisition d'une société et la juste valeur de ses actifs nets identifiables.
Dépréciation (impairment) | Analyse financière | Constatation comptable d'une perte de valeur d'un actif lorsque sa valeur recouvrable devient inférieure à sa valeur nette comptable.
Amortissement | Analyse financière | Constatation de la consommation des avantages économiques d'un actif immobilisé sur sa durée d'utilisation.
Provision | Analyse financière | Passif dont l'échéance ou le montant est incertain, constitué pour un risque ou une charge probable.
Comptes consolidés | Analyse financière | États financiers présentant un groupe comme une seule entité économique.
Normes IFRS | Analyse financière | Référentiel comptable international obligatoire pour les comptes consolidés des sociétés cotées de l'UE.
Plan comptable général (PCG) | Analyse financière | Référentiel comptable français applicable aux comptes sociaux.
Grand livre | Analyse financière | Document regroupant l'ensemble des comptes de l'entreprise et des écritures qui les mouvementent.
FEC (fichier des écritures comptables) | Analyse financière | Fichier normalisé de toutes les écritures d'un exercice, remis à l'administration fiscale en cas de contrôle.
Commissaire aux comptes | Analyse financière | Professionnel indépendant certifiant la régularité, la sincérité et l'image fidèle des comptes.
Réserves du commissaire aux comptes | Analyse financière | Limitation ou désaccord exprimé dans le rapport de certification ; signal d'alerte pour l'analyste.
Procédure d'alerte | Analyse financière | Procédure engagée par le commissaire aux comptes face à des faits compromettant la continuité d'exploitation.
Continuité d'exploitation | Analyse financière | Hypothèse selon laquelle l'entreprise poursuivra son activité dans un avenir prévisible.
Window dressing | Analyse financière | Habillage temporaire des comptes à la clôture pour améliorer la présentation des ratios.
Comptabilité créative | Analyse financière | Usage abusif des marges d'appréciation comptables pour embellir l'image financière.
Loi de Benford | Analyse financière | Loi statistique de distribution des premiers chiffres, utilisée pour détecter des données comptables manipulées.
DCF (flux actualisés) | Analyse financière | Méthode d'évaluation fondée sur l'actualisation des flux de trésorerie futurs au coût du capital.
WACC (CMPC) | Analyse financière | Coût moyen pondéré du capital : taux d'actualisation reflétant le coût des fonds propres et de la dette.
Multiples de valorisation | Analyse financière | Évaluation par comparaison (VE/EBITDA, PER, VE/CA) avec des sociétés ou transactions comparables.
Valeur d'entreprise | Analyse financière | Valeur des capitaux propres augmentée de la dette nette ; valeur de l'outil économique.
PER | Analyse financière | Price Earnings Ratio : cours de l'action rapporté au bénéfice par action.
Covenant | Analyse financière | Engagement contractuel de l'emprunteur (ratios à respecter, restrictions) dont la violation peut rendre la dette exigible.
Hors-bilan | Analyse financière | Engagements donnés ou reçus non inscrits au bilan (cautions, garanties, crédit-bail, engagements de rachat).
Parties liées | Analyse financière | Personnes ou entités ayant un lien de contrôle ou d'influence ; les transactions avec elles doivent être signalées.
# ===================== CRÉDIT =====================
Analyse crédit | Crédit | Évaluation de la capacité et de la volonté d'un emprunteur à rembourser sa dette.
Scoring crédit | Crédit | Modèle statistique attribuant une note de probabilité de défaut à un emprunteur.
Probabilité de défaut (PD) | Crédit | Probabilité qu'une contrepartie fasse défaut sur un horizon d'un an.
Perte en cas de défaut (LGD) | Crédit | Part de l'exposition perdue en cas de défaut, après recouvrements et garanties.
Exposition en cas de défaut (EAD) | Crédit | Montant exposé au moment du défaut, y compris tirages futurs probables.
Perte attendue | Crédit | Produit PD × LGD × EAD ; base du provisionnement et de la tarification.
IFRS 9 | Crédit | Norme de provisionnement des pertes de crédit attendues en trois stages selon la dégradation du risque.
Créance douteuse (NPL) | Crédit | Prêt non performant : impayé de plus de 90 jours ou remboursement improbable.
Restructuration (forbearance) | Crédit | Concession accordée à un emprunteur en difficulté (délai, taux, abandon partiel).
Notation externe | Crédit | Évaluation de la solvabilité d'un émetteur par une agence (S&P, Moody's, Fitch).
Investment grade | Crédit | Catégorie de notation de bonne qualité (BBB- et au-dessus chez S&P).
High yield | Crédit | Catégorie spéculative de notation (BB+ et en dessous), mieux rémunérée et plus risquée.
Garantie (sûreté) | Crédit | Droit accordé au créancier pour sécuriser le remboursement : sûreté réelle (hypothèque, nantissement) ou personnelle (caution).
Caution | Crédit | Engagement d'un tiers de payer la dette du débiteur si celui-ci ne s'exécute pas.
Nantissement | Crédit | Sûreté portant sur un bien meuble incorporel (fonds de commerce, titres, créances).
Hypothèque | Crédit | Sûreté réelle portant sur un immeuble sans dépossession du débiteur.
Affacturage | Crédit | Cession de créances clients à un factor qui en assure le financement et le recouvrement.
Crédit-bail | Crédit | Location d'un bien assortie d'une option d'achat en fin de contrat.
Crédit documentaire | Crédit | Engagement bancaire de payer l'exportateur contre remise de documents conformes ; outil du commerce international.
Lettre de crédit stand-by | Crédit | Garantie bancaire mobilisable en cas de défaillance du donneur d'ordre.
Concentration du risque | Crédit | Exposition excessive sur une même contrepartie, un même groupe ou un même secteur.
Grands risques | Crédit | Expositions dépassant 10 % des fonds propres éligibles, soumises à une limite de 25 %.
Bâle III | Crédit | Accords prudentiels renforçant fonds propres, levier et liquidité des banques.
Ratio CET1 | Crédit | Fonds propres de base de catégorie 1 rapportés aux actifs pondérés par les risques.
RWA (actifs pondérés) | Crédit | Expositions pondérées selon leur risque, dénominateur des ratios de solvabilité.
LCR | Crédit | Ratio de liquidité à 30 jours : actifs liquides de haute qualité / sorties nettes de trésorerie en stress.
NSFR | Crédit | Ratio de financement stable net sur un an.
Procédure de sauvegarde | Crédit | Procédure collective préventive pour une entreprise en difficulté non encore en cessation des paiements.
Redressement judiciaire | Crédit | Procédure collective pour une entreprise en cessation des paiements dont le redressement paraît possible.
Liquidation judiciaire | Crédit | Procédure mettant fin à l'activité d'une entreprise dont le redressement est manifestement impossible.
Cessation des paiements | Crédit | Impossibilité de faire face au passif exigible avec l'actif disponible.
Fichier FICP | Crédit | Fichier national des incidents de remboursement des crédits aux particuliers, tenu par la Banque de France.
Cotation Banque de France | Crédit | Appréciation par la Banque de France de la capacité d'une entreprise à honorer ses engagements à trois ans.
# ===================== BANQUE & PAIEMENTS =====================
Virement SEPA (SCT) | Banque & paiements | Virement en euros au sein de l'espace SEPA selon un format harmonisé.
Virement instantané (SCT Inst) | Banque & paiements | Virement SEPA exécuté en moins de 10 secondes, 24 h/24 ; vérification du bénéficiaire obligatoire (règlement 2024/886).
Prélèvement SEPA (SDD) | Banque & paiements | Paiement initié par le créancier sur la base d'un mandat signé par le débiteur.
SWIFT | Banque & paiements | Réseau de messagerie financière interbancaire mondial (messages MT et ISO 20022).
ISO 20022 | Banque & paiements | Norme de messagerie financière structurée remplaçant progressivement les messages MT de SWIFT.
Message MT103 | Banque & paiements | Message SWIFT de virement client unitaire transfrontalier.
Message MT202 COV | Banque & paiements | Message de couverture interbancaire devant transporter les informations donneur d'ordre et bénéficiaire.
BIC | Banque & paiements | Code d'identification international d'un établissement bancaire.
IBAN | Banque & paiements | Numéro international de compte bancaire normalisé.
Correspondance bancaire | Banque & paiements | Relation par laquelle une banque fournit des services (comptes, paiements) à une autre banque, souvent étrangère.
Compte nostro / vostro | Banque & paiements | Compte détenu par une banque chez un correspondant (nostro) ou ouvert pour un correspondant (vostro).
Nested account | Banque & paiements | Utilisation indirecte d'une relation de correspondance par des banques tierces non connues du correspondant.
Payable-through account | Banque & paiements | Compte de correspondance utilisé directement par les clients de la banque intermédiaire.
De-risking | Banque & paiements | Retrait ou refus de relations d'affaires par catégories entières de clients jugées risquées plutôt qu'au cas par cas.
Établissement de paiement | Banque & paiements | Prestataire agréé fournissant des services de paiement sans pouvoir recevoir de dépôts ni octroyer de crédit au-delà des paiements.
Établissement de monnaie électronique | Banque & paiements | Prestataire agréé émettant de la monnaie électronique (cartes prépayées, portefeuilles).
Agent de prestataire de paiement | Banque & paiements | Personne agissant pour le compte d'un établissement de paiement, sous sa responsabilité LCB-FT.
Transmission de fonds (money remittance) | Banque & paiements | Service de transfert d'argent sans compte, souvent transfrontalier, exposé au risque de blanchiment.
Hawala | Banque & paiements | Système informel de transfert de valeur fondé sur la confiance et la compensation entre intermédiaires, sans mouvement physique de fonds.
DSP2 (PSD2) | Banque & paiements | Directive européenne sur les services de paiement : authentification forte, accès aux comptes, nouveaux acteurs.
Authentification forte (SCA) | Banque & paiements | Authentification combinant au moins deux facteurs indépendants (connaissance, possession, inhérence).
Initiation de paiement | Banque & paiements | Service permettant à un tiers agréé d'initier un paiement depuis le compte du client.
Agrégation de comptes | Banque & paiements | Service d'information consolidant les comptes détenus dans plusieurs banques.
Chargeback (rétrofacturation) | Banque & paiements | Annulation d'une transaction carte à l'initiative du porteur via sa banque.
Acquéreur | Banque & paiements | Établissement qui reçoit les paiements carte pour le compte du commerçant.
PSP | Banque & paiements | Prestataire de services de paiement, notamment pour l'encaissement en ligne des commerçants.
Payment facilitator | Banque & paiements | Acteur qui agrège des sous-marchands sous son propre contrat d'acquisition.
Transaction laundering | Banque & paiements | Traitement de paiements d'une activité illicite au travers du compte marchand d'une activité apparemment légitime.
Merchant Category Code (MCC) | Banque & paiements | Code à quatre chiffres classant l'activité d'un commerçant dans les réseaux carte.
Fichier central des chèques (FCC) | Banque & paiements | Fichier Banque de France des interdictions bancaires d'émettre des chèques et retraits de cartes.
FICOBA | Banque & paiements | Fichier national des comptes bancaires et assimilés, géré par la DGFiP.
Espèces | Banque & paiements | Billets et pièces ; moyen de paiement anonyme, principal vecteur du placement en blanchiment.
Limite de paiement en espèces | Banque & paiements | En France 1 000 € entre professionnel et particulier résident ; l'AMLR fixe un plafond européen de 10 000 €.
# ===================== LCB-FT =====================
Blanchiment de capitaux | LCB-FT | Fait de faciliter la justification mensongère de l'origine de biens ou revenus issus d'un crime ou délit, ou d'apporter son concours à leur placement, dissimulation ou conversion (art. 324-1 Code pénal).
Infraction sous-jacente (prédicat) | LCB-FT | Crime ou délit ayant généré les fonds blanchis (trafic, fraude, corruption, fraude fiscale…).
Placement | LCB-FT | Première phase du blanchiment : introduction des fonds illicites dans le système financier.
Empilement (layering) | LCB-FT | Deuxième phase : multiplication d'opérations pour brouiller la trace de l'origine des fonds.
Intégration | LCB-FT | Troisième phase : réinjection des fonds blanchis dans l'économie légale sous une apparence légitime.
Autoblanchiment | LCB-FT | Blanchiment par l'auteur même de l'infraction d'origine ; punissable en droit français.
Présomption de blanchiment | LCB-FT | Art. 324-1-1 C. pén. : présomption d'illicéité lorsque les conditions d'une opération n'ont d'autre justification que de dissimuler l'origine des fonds.
Financement du terrorisme | LCB-FT | Fait de fournir, réunir ou gérer des fonds en vue de les voir utilisés pour commettre un acte terroriste (art. 421-2-2 C. pén.).
Financement de la prolifération | LCB-FT | Mise à disposition de fonds ou services contribuant au développement d'armes de destruction massive.
Assujetti | LCB-FT | Professionnel soumis aux obligations LCB-FT (art. L561-2 CMF) : banques, assurances, PSP, notaires, agents immobiliers, CASP…
Classification des risques | LCB-FT | Cartographie des risques de blanchiment de l'assujetti, par client, produit, canal et géographie.
Évaluation nationale des risques (ENR) | LCB-FT | Analyse des menaces et vulnérabilités LCB-FT du pays, publiée par le COLB en France.
Évaluation supranationale des risques | LCB-FT | Analyse des risques LCB-FT à l'échelle de l'UE publiée par la Commission européenne.
Vigilance constante | LCB-FT | Obligation de suivre la relation d'affaires et d'examiner les opérations pour s'assurer de leur cohérence avec la connaissance du client.
Examen renforcé | LCB-FT | Art. L561-10-2 CMF : examen des opérations complexes, d'un montant inhabituellement élevé ou sans justification économique.
Profil transactionnel | LCB-FT | Comportement attendu du client (montants, fréquences, contreparties, pays) servant de référence à la détection d'anomalies.
Scénario de détection | LCB-FT | Règle automatisée de surveillance des opérations générant des alertes selon des seuils et typologies.
Alerte | LCB-FT | Signal produit par un outil de surveillance ou une remontée humaine, nécessitant une analyse documentée.
Analyse N1 | LCB-FT | Premier niveau d'analyse d'une alerte : qualification rapide, levée des faux positifs, escalade si doute.
Analyse N2 | LCB-FT | Analyse approfondie d'une alerte escaladée : investigation, entretien, pièces justificatives, décision de déclaration.
Faux positif | LCB-FT | Alerte qui, après analyse, ne révèle aucune anomalie.
Taux de faux positifs | LCB-FT | Proportion d'alertes classées sans suite ; indicateur de calibrage des scénarios.
Déclaration de soupçon (DS) | LCB-FT | Déclaration à TRACFIN des sommes ou opérations dont l'assujetti sait, soupçonne ou a de bonnes raisons de soupçonner l'origine illicite (art. L561-15 CMF).
ERMES | LCB-FT | Plateforme de télé-déclaration des déclarations de soupçon à TRACFIN.
Tipping-off | LCB-FT | Divulgation interdite au client ou à un tiers de l'existence d'une déclaration de soupçon (art. L561-18 CMF).
Droit d'opposition TRACFIN | LCB-FT | Faculté de TRACFIN de reporter l'exécution d'une opération signalée (10 jours ouvrables).
Déclaration systématique (COSI) | LCB-FT | Communication systématique à TRACFIN de certaines opérations (versements/retraits d'espèces au-delà de seuils, transmissions de fonds).
Correspondant TRACFIN | LCB-FT | Personne désignée par l'assujetti pour répondre aux demandes de TRACFIN.
Déclarant TRACFIN | LCB-FT | Personne habilitée à effectuer les déclarations de soupçon au nom de l'assujetti.
Droit de communication | LCB-FT | Pouvoir de TRACFIN d'obtenir tout document utile auprès des assujettis.
Conservation des documents | LCB-FT | Obligation de conserver pièces d'identification et documents relatifs aux opérations pendant 5 ans.
Typologie | LCB-FT | Schéma récurrent de blanchiment ou de fraude décrit par les autorités pour aider à la détection.
Signal d'alerte (red flag) | LCB-FT | Indicateur concret qui doit attirer l'attention sur un risque possible de blanchiment ou de fraude.
Mule financière | LCB-FT | Personne qui prête ou ouvre un compte pour faire transiter des fonds d'origine frauduleuse.
Compte rebond | LCB-FT | Compte utilisé pour recevoir et retransférer rapidement des fonds afin de rompre la traçabilité.
Société écran | LCB-FT | Structure sans activité réelle utilisée pour détenir des actifs ou faire transiter des fonds en masquant le bénéficiaire.
Société de façade | LCB-FT | Entreprise ayant une activité réelle servant à mêler fonds licites et illicites.
Prête-nom (homme de paille) | LCB-FT | Personne qui apparaît à la place du véritable bénéficiaire ou dirigeant.
Domiciliation | LCB-FT | Fourniture d'un siège social ou d'une adresse administrative à une entreprise ; activité réglementée et à risque.
Fiducie / trust | LCB-FT | Dispositif par lequel des biens sont confiés à un fiduciaire au profit de bénéficiaires ; les bénéficiaires effectifs doivent être identifiés.
Constituant (settlor) | LCB-FT | Personne qui transfère des biens à un trust ou une fiducie.
Protecteur (trust) | LCB-FT | Personne chargée de surveiller le trustee ; considérée comme bénéficiaire effectif.
Cash intensive business | LCB-FT | Activité manipulant beaucoup d'espèces (restauration, commerce de détail, laverie), propice au mélange de fonds.
Schtroumpfage (smurfing) | LCB-FT | Fractionnement de dépôts entre plusieurs personnes pour rester sous les seuils.
Fractionnement (structuring) | LCB-FT | Découpage d'une opération en plusieurs montants inférieurs aux seuils de vigilance ou de déclaration.
Cuckoo smurfing | LCB-FT | Dépôt de fonds illicites sur le compte d'un tiers qui attend un virement légitime de l'étranger.
Blanchiment commercial (TBML) | LCB-FT | Blanchiment par le commerce international : sur/sous-facturation, facturation multiple, fausses descriptions de marchandises.
Surfacturation | LCB-FT | Facturation au-dessus de la valeur réelle des biens pour transférer de la valeur vers l'exportateur.
Sous-facturation | LCB-FT | Facturation en dessous de la valeur réelle pour transférer de la valeur vers l'importateur.
Phantom shipment | LCB-FT | Facture correspondant à une expédition fictive, sans marchandise réelle.
Black Market Peso Exchange | LCB-FT | Schéma de compensation par lequel des narcodollars américains financent des importations latino-américaines.
Blanchiment immobilier | LCB-FT | Acquisition de biens immobiliers avec des fonds illicites, souvent via sociétés, apport en espèces ou prix manipulés.
Prêt adossé (loan back) | LCB-FT | Faux prêt consenti par une structure contrôlée par le blanchisseur pour justifier des fonds.
Professionnel complice (gatekeeper) | LCB-FT | Avocat, notaire, comptable ou conseiller qui facilite, sciemment ou non, des montages de blanchiment.
Blanchiment par les jeux | LCB-FT | Utilisation de casinos ou paris pour convertir des espèces en gains apparemment légitimes.
Blanchiment par l'art | LCB-FT | Utilisation d'œuvres d'art (prix subjectifs, anonymat, ports francs) pour transférer ou stocker de la valeur.
Port franc | LCB-FT | Zone d'entreposage sous douane où des biens de valeur peuvent être stockés et échangés en suspension de taxes.
Zone franche | LCB-FT | Zone économique aux contrôles douaniers allégés, exposée au TBML et au contournement de sanctions.
Collecte de fonds associative | LCB-FT | Activité des OBNL pouvant être détournée pour financer le terrorisme (recommandation 8 du GAFI).
Microfinancement du terrorisme | LCB-FT | Financement d'actes terroristes par de petites sommes d'origine souvent licite (prêts à la consommation, aides).
Cellule de renseignement financier (CRF) | LCB-FT | Organisme national recevant et analysant les déclarations de soupçon (TRACFIN en France).
Groupe Egmont | LCB-FT | Réseau international de coopération entre cellules de renseignement financier.
COLB | LCB-FT | Conseil d'orientation de la lutte contre le blanchiment de capitaux et le financement du terrorisme, qui pilote l'ENR française.
Contrôle permanent | LCB-FT | Contrôles de premier et deuxième niveau intégrés aux processus, distincts du contrôle périodique (audit).
Trois lignes de défense | LCB-FT | Modèle de gouvernance des risques : opérationnels (1), fonctions de contrôle (2), audit interne (3).
Responsable LCB-FT | LCB-FT | Personne désignée en charge de la mise en œuvre du dispositif LCB-FT (membre de la direction ou cadre dédié).
Arrêté du 6 janvier 2021 | LCB-FT | Arrêté relatif au dispositif et au contrôle interne LCB-FT et gel des avoirs des établissements du secteur bancaire et assurance.
Questionnaire LCB-FT (QLB) | LCB-FT | Questionnaire annuel transmis à l'ACPR décrivant le dispositif LCB-FT de l'établissement.
Approche groupe | LCB-FT | Obligation de mettre en place un dispositif LCB-FT homogène dans toutes les filiales et succursales, y compris à l'étranger.
Partage d'informations intra-groupe | LCB-FT | Échange d'informations LCB-FT entre entités d'un même groupe, encadré par la loi.
Tiers introducteur | LCB-FT | Tiers sur lequel un assujetti s'appuie pour l'identification du client ; l'assujetti reste responsable.
Externalisation LCB-FT | LCB-FT | Recours à un prestataire pour certaines tâches (filtrage, KYC) sans transfert de responsabilité.
AMLD5 | LCB-FT | 5e directive (UE) 2018/843 : crypto-actifs, registres des bénéficiaires effectifs, pays tiers à haut risque.
Pays tiers à haut risque (UE) | LCB-FT | Juridictions identifiées par règlement délégué de la Commission, imposant des mesures de vigilance renforcées.
# ===================== KYC / VIGILANCE CLIENT =====================
Entrée en relation | KYC | Ouverture d'une relation d'affaires précédée de l'identification, de la vérification et de l'évaluation du risque du client.
Identification | KYC | Recueil des éléments d'identité du client (nom, prénom, date et lieu de naissance, adresse, numéro d'immatriculation).
Vérification d'identité | KYC | Contrôle des éléments d'identification sur un document probant (pièce d'identité officielle, extrait Kbis…).
Pièce d'identité probante | KYC | Document officiel en cours de validité comportant photographie (carte d'identité, passeport, titre de séjour).
Bande MRZ | KYC | Zone de lecture automatique d'une pièce d'identité dont la cohérence (sommes de contrôle) aide à détecter les faux.
Entrée en relation à distance | KYC | Ouverture sans présence physique, nécessitant des mesures complémentaires (identification électronique, premier virement depuis un compte à son nom…).
Identification électronique (eIDAS) | KYC | Moyens d'identification électronique reconnus au niveau européen selon des niveaux de garantie (faible, substantiel, élevé).
Portefeuille d'identité numérique européen | KYC | Wallet d'identité prévu par le règlement eIDAS 2 pour s'identifier et partager des attributs vérifiés.
PVID | KYC | Prestataire de vérification d'identité à distance certifié par l'ANSSI.
Liveness detection | KYC | Contrôle biométrique vérifiant qu'une personne réelle et vivante est présente lors de l'identification à distance.
Deepfake | KYC | Contenu audio ou vidéo synthétique imitant une personne réelle, utilisé pour contourner l'identification à distance.
Objet et nature de la relation | KYC | Informations sur le but de la relation d'affaires (activité, opérations prévues, origine des fonds).
Origine des fonds | KYC | Provenance des fonds utilisés dans une opération ou la relation (salaire, vente, héritage…).
Origine du patrimoine | KYC | Provenance de l'ensemble du patrimoine du client ; exigée en vigilance renforcée (PPE, haut risque).
Profil de risque client | KYC | Niveau de risque LCB-FT attribué au client (faible, moyen, élevé) déterminant les mesures de vigilance.
Vigilance simplifiée | KYC | Mesures allégées pour les relations présentant un risque faible, dans les cas prévus par les textes.
Vigilance renforcée | KYC | Mesures complémentaires pour les relations à risque élevé : informations supplémentaires, validation hiérarchique, suivi accru.
Revue périodique (KYC refresh) | KYC | Mise à jour des informations client à une fréquence fixée selon le niveau de risque.
Événement déclencheur | KYC | Fait justifiant une revue KYC anticipée (changement d'activité, alerte, information négative).
Kbis | KYC | Extrait d'immatriculation au registre du commerce et des sociétés attestant l'existence juridique d'une société française.
Registre national des entreprises (RNE) | KYC | Registre unique tenu par l'INPI centralisant les informations des entreprises françaises depuis 2023.
Registre des bénéficiaires effectifs (RBE) | KYC | Registre déclarant les bénéficiaires effectifs des sociétés ; accès restreint aux personnes justifiant d'un intérêt légitime depuis l'arrêt CJUE 2022.
Signalement de divergence | KYC | Obligation des assujettis de signaler les écarts entre le RBE et les informations dont ils disposent.
Chaîne de détention | KYC | Ensemble des liens capitalistiques entre la société cliente et ses bénéficiaires effectifs.
Contrôle par d'autres moyens | KYC | Contrôle d'une société sans détention majoritaire du capital (pacte, droit de nomination, pouvoir de fait).
Dirigeant par défaut | KYC | Représentant légal retenu comme bénéficiaire effectif lorsqu'aucune personne physique n'est identifiée.
Actions au porteur | KYC | Titres non nominatifs facilitant l'anonymat des détenteurs ; facteur de risque élevé.
Personne morale de droit étranger | KYC | Société constituée hors de France, nécessitant la vérification de son existence auprès du registre de son pays.
LEI | KYC | Legal Entity Identifier : identifiant mondial à 20 caractères des entités juridiques, géré par la GLEIF.
SIREN / SIRET | KYC | Identifiants INSEE de l'entreprise (9 chiffres) et de l'établissement (14 chiffres).
Code NAF / APE | KYC | Code de l'activité principale exercée attribué par l'INSEE.
Client occasionnel | KYC | Personne réalisant une opération ponctuelle sans relation d'affaires ; identification au-delà de seuils.
Relation d'affaires | KYC | Relation professionnelle ou commerciale censée s'inscrire dans une certaine durée.
Proche de PPE | KYC | Membre de la famille d'une PPE (conjoint, enfants, parents) soumis aux mêmes mesures.
Personne étroitement associée | KYC | Personne ayant des liens d'affaires étroits avec une PPE ou bénéficiaire d'une entité créée au profit d'une PPE.
PPE nationale | KYC | PPE exerçant une fonction dans le pays de l'assujetti ; soumise à vigilance renforcée dans l'UE.
Fonctions publiques importantes | KYC | Liste réglementaire des fonctions conférant la qualité de PPE (art. R561-18 CMF).
Adverse media (presse négative) | KYC | Informations défavorables publiées sur un client ou une contrepartie, prises en compte dans l'évaluation du risque.
Filtrage des noms | KYC | Comparaison des clients aux listes de sanctions, de PPE et d'informations négatives.
Levée d'homonymie | KYC | Analyse permettant de confirmer ou d'écarter qu'un client correspond à une personne listée.
Correspondance approchante (fuzzy matching) | KYC | Technique de comparaison tolérant fautes, inversions et translittérations.
Translittération | KYC | Transcription d'un nom d'un alphabet à un autre (cyrillique, arabe), source de multiples variantes.
Contrôle de cohérence | KYC | Vérification que les informations déclarées sont cohérentes entre elles et avec les opérations.
Refus d'entrée en relation | KYC | Obligation de ne pas ouvrir la relation lorsque l'identification ou la connaissance client ne peut être assurée.
Rupture de la relation | KYC | Fin de la relation d'affaires lorsque la vigilance ne peut plus être exercée, sans préjudice d'une déclaration de soupçon.
# ===================== SANCTIONS =====================
Gel des avoirs | Sanctions | Mesure interdisant tout mouvement, transfert ou utilisation des fonds et ressources économiques d'une personne désignée.
Interdiction de mise à disposition | Sanctions | Interdiction de fournir, directement ou indirectement, des fonds ou ressources économiques à une personne désignée.
Personne désignée | Sanctions | Personne physique, morale ou entité inscrite sur une liste de sanctions.
Ressources économiques | Sanctions | Avoirs de toute nature, corporels ou incorporels, pouvant servir à obtenir des fonds, biens ou services.
Mesures restrictives (UE) | Sanctions | Sanctions adoptées par le Conseil de l'UE dans le cadre de la PESC : gels, interdictions sectorielles, interdictions de voyager.
PESC | Sanctions | Politique étrangère et de sécurité commune de l'UE, base des décisions de sanctions.
Règlement de sanctions UE | Sanctions | Acte directement applicable mettant en œuvre une décision PESC ; il fixe les interdictions et les annexes de personnes listées.
Sanctions sectorielles | Sanctions | Restrictions visant des secteurs (finance, énergie, défense) plutôt que des personnes nommées.
Sanctions secondaires | Sanctions | Mesures américaines visant des personnes non américaines qui commercent avec des cibles sanctionnées.
Extraterritorialité | Sanctions | Application d'une loi nationale à des opérations ou personnes situées hors du territoire de l'État émetteur.
US nexus | Sanctions | Lien avec les États-Unis (dollar, personne américaine, territoire, bien d'origine américaine) déclenchant la compétence OFAC.
Règle des 50 % (OFAC) | Sanctions | Toute entité détenue à 50 % ou plus, seule ou ensemble, par des personnes bloquées est elle-même bloquée.
Critère de propriété et de contrôle (UE) | Sanctions | Entité détenue à plus de 50 % ou contrôlée par une personne désignée, présumée soumise au gel.
OFAC | Sanctions | Office of Foreign Assets Control, service du Trésor américain administrant les sanctions économiques des États-Unis.
OFSI | Sanctions | Office of Financial Sanctions Implementation, autorité britannique de mise en œuvre des sanctions financières.
DG Trésor (service des sanctions) | Sanctions | Autorité française compétente pour les gels d'avoirs, les autorisations et les déclarations de gel.
Registre national des gels | Sanctions | Base publique de la DG Trésor recensant les personnes soumises à un gel en France.
Gel national | Sanctions | Mesure de gel décidée par le ministre de l'Économie (art. L562-2 CMF), notamment en matière de terrorisme.
Licence (autorisation) | Sanctions | Autorisation délivrée par l'autorité compétente de réaliser une opération autrement interdite.
Licence générale OFAC | Sanctions | Autorisation publiée par l'OFAC permettant certaines catégories d'opérations sans demande individuelle.
Wind-down | Sanctions | Période transitoire autorisant la liquidation d'opérations en cours après une nouvelle sanction.
Clause d'antériorité | Sanctions | Exception permettant l'exécution de contrats conclus avant l'entrée en vigueur d'une mesure, sous conditions.
Déclaration de gel | Sanctions | Information obligatoire de la DG Trésor des fonds gelés et des opérations bloquées.
Filtrage des opérations | Sanctions | Contrôle des messages de paiement (donneur d'ordre, bénéficiaire, banques, motif) contre les listes de sanctions.
Contournement de sanctions | Sanctions | Ensemble des techniques visant à échapper aux sanctions : prête-noms, sociétés écrans, pays tiers, documents falsifiés.
Clause anti-contournement | Sanctions | Interdiction de participer sciemment et volontairement à des activités visant à contourner les mesures restrictives.
No Russia clause | Sanctions | Clause contractuelle imposée par le règlement UE 833/2014 interdisant la réexportation vers la Russie de biens sensibles.
Biens à haute priorité (Common High Priority List) | Sanctions | Liste de produits critiques pour l'armée russe établie par l'UE, les États-Unis, le Royaume-Uni et le Japon.
Plafonnement du prix du pétrole | Sanctions | Mécanisme du G7 interdisant les services maritimes pour le pétrole russe vendu au-dessus d'un prix plafond.
Flotte fantôme | Sanctions | Navires vieillissants à propriété opaque transportant du pétrole sous sanctions, souvent avec AIS coupé.
AIS | Sanctions | Système d'identification automatique des navires ; ses coupures sont un signal de contournement.
Transbordement navire à navire (STS) | Sanctions | Transfert de cargaison en mer entre navires, utilisé pour masquer l'origine de produits sanctionnés.
Changement de pavillon (flag hopping) | Sanctions | Réimmatriculation fréquente d'un navire pour échapper à la surveillance.
Numéro IMO | Sanctions | Identifiant unique et permanent d'un navire, plus fiable que son nom pour le filtrage.
Sanctions ONU | Sanctions | Mesures adoptées par le Conseil de sécurité (chapitre VII), contraignantes pour tous les États membres.
Comité des sanctions | Sanctions | Organe subsidiaire du Conseil de sécurité gérant un régime (inscriptions, dérogations, radiations).
Régime mondial droits de l'homme (UE) | Sanctions | Régime européen permettant de sanctionner des auteurs de violations graves des droits de l'homme partout dans le monde.
Magnitsky (Global Magnitsky) | Sanctions | Dispositifs américains sanctionnant corruption et violations des droits de l'homme.
SDGT | Sanctions | Specially Designated Global Terrorist : désignation américaine au titre du terrorisme.
FTO | Sanctions | Foreign Terrorist Organization désignée par le Département d'État ; tout soutien matériel est pénalement réprimé.
Radiation (delisting) | Sanctions | Retrait d'une personne d'une liste de sanctions, après décision de l'autorité ou d'une juridiction.
Recours contre une inscription | Sanctions | Contestation devant le Tribunal de l'UE d'une inscription sur une liste de sanctions.
Paquet de sanctions | Sanctions | Ensemble de mesures adoptées simultanément par l'UE (ex. paquets successifs contre la Russie).
Fuite de fonds vers pays tiers | Sanctions | Redirection de flux vers des juridictions non sanctionnantes servant de plaque tournante.
Sanctions Compliance Program | Sanctions | Programme de conformité sanctions attendu par l'OFAC : engagement de la direction, évaluation des risques, contrôles, tests, formation.
Divulgation volontaire (voluntary self-disclosure) | Sanctions | Signalement spontané d'une violation à l'autorité, facteur d'atténuation des pénalités.
# ===================== EMBARGOS & CONTRÔLE EXPORT =====================
Embargo | Embargos & export | Interdiction totale ou partielle du commerce avec un pays (armes, biens, services).
Embargo sur les armes | Embargos & export | Interdiction de vendre, fournir ou transférer des armes et matériels connexes à un pays ou groupe.
Bien à double usage | Embargos & export | Bien, logiciel ou technologie utilisable à des fins civiles et militaires (règlement (UE) 2021/821).
Règlement (UE) 2021/821 | Embargos & export | Régime européen de contrôle des exportations, du courtage, de l'assistance technique et du transit des biens à double usage.
Annexe I double usage | Embargos & export | Liste européenne des biens à double usage soumis à autorisation, classés en dix catégories.
Clause attrape-tout (catch-all) | Embargos & export | Obligation d'autorisation pour un bien non listé dès lors que l'exportateur sait ou est informé d'un usage militaire ou sensible.
SBDU | Embargos & export | Service des biens à double usage, autorité française délivrant les licences d'exportation.
Licence d'exportation | Embargos & export | Autorisation administrative préalable à l'exportation d'un bien contrôlé.
Certificat d'utilisateur final | Embargos & export | Document par lequel le destinataire s'engage sur l'utilisation finale et l'absence de réexportation.
Utilisateur final | Embargos & export | Destinataire réel qui utilisera le bien exporté, à distinguer des intermédiaires.
Détournement de destination | Embargos & export | Réexportation de biens vers un pays ou utilisateur interdit via un pays tiers.
Pays de transit à risque | Embargos & export | Juridiction utilisée comme étape de réexportation vers une destination sanctionnée.
Code SH / nomenclature combinée | Embargos & export | Classement douanier des marchandises permettant d'identifier les biens soumis à restrictions.
ECCN | Embargos & export | Export Control Classification Number : classification américaine des biens dans la Commerce Control List.
EAR | Embargos & export | Export Administration Regulations : réglementation américaine du contrôle des exportations administrée par le BIS.
Entity List (BIS) | Embargos & export | Liste américaine d'entités soumises à licence pour recevoir des biens soumis aux EAR.
Règle du produit direct étranger (FDPR) | Embargos & export | Règle américaine soumettant aux EAR des biens produits à l'étranger avec des technologies américaines.
ITAR | Embargos & export | International Traffic in Arms Regulations : contrôle américain des biens et services de défense.
Matériel de guerre | Embargos & export | Armes et matériels soumis en France à autorisation d'exportation (licence CIEEMG).
Courtage | Embargos & export | Négociation d'opérations portant sur des biens contrôlés entre pays tiers, soumise à autorisation.
Assistance technique | Embargos & export | Aide technique liée à la réparation, au développement ou à l'utilisation de biens contrôlés, elle-même contrôlée.
Incoterms | Embargos & export | Règles de la CCI répartissant frais, risques et formalités entre vendeur et acheteur (EXW, FOB, CIF, DAP…).
Connaissement (bill of lading) | Embargos & export | Document de transport maritime attestant la prise en charge des marchandises et représentant leur propriété.
Certificat d'origine | Embargos & export | Document attestant le pays d'origine des marchandises.
Déclaration en douane | Embargos & export | Document par lequel l'exportateur ou l'importateur déclare les marchandises à l'administration douanière.
Opérateur économique agréé (OEA) | Embargos & export | Statut douanier reconnaissant la fiabilité d'une entreprise dans la chaîne logistique.
Programme interne de conformité (ICP) | Embargos & export | Dispositif d'une entreprise pour respecter le contrôle des exportations (recommandation (UE) 2019/1318).
# ===================== FRAUDE =====================
Fraude | Fraude | Acte intentionnel visant à obtenir un avantage indu en trompant une personne ou une organisation.
Escroquerie | Fraude | Fait de tromper une personne par manœuvres frauduleuses pour la déterminer à remettre des fonds ou un bien (art. 313-1 C. pén.).
Abus de confiance | Fraude | Détournement de fonds ou biens remis à charge de les rendre ou d'en faire un usage déterminé (art. 314-1 C. pén.).
Faux et usage de faux | Fraude | Altération frauduleuse de la vérité dans un écrit, et utilisation de ce document (art. 441-1 C. pén.).
Fraude au président (FOVI) | Fraude | Usurpation de l'identité d'un dirigeant pour obtenir un virement urgent et confidentiel.
Fraude au changement de RIB | Fraude | Usurpation d'un fournisseur pour faire modifier ses coordonnées bancaires et détourner les paiements.
Fraude au faux conseiller | Fraude | Appel d'un fraudeur se faisant passer pour la banque afin d'obtenir la validation d'opérations.
Fraude au virement autorisé (APP) | Fraude | Virement émis par la victime elle-même, manipulée par le fraudeur.
Phishing (hameçonnage) | Fraude | Message frauduleux imitant un organisme de confiance pour obtenir identifiants ou données bancaires.
Smishing / vishing | Fraude | Hameçonnage par SMS / par téléphone.
Prise de contrôle de compte (ATO) | Fraude | Accès frauduleux au compte d'un client à l'aide d'identifiants volés.
SIM swap | Fraude | Détournement du numéro de téléphone d'une victime pour intercepter les codes d'authentification.
Usurpation d'identité | Fraude | Utilisation de l'identité d'un tiers pour réaliser des opérations en son nom (art. 226-4-1 C. pén.).
Identité synthétique | Fraude | Identité fictive combinant des éléments réels et inventés, construite pour ouvrir des comptes et obtenir du crédit.
Faux documents | Fraude | Pièces contrefaites ou falsifiées (identité, bulletins de salaire, avis d'imposition, Kbis).
Fraude documentaire | Fraude | Production de documents faux ou altérés pour obtenir un service, un crédit ou ouvrir un compte.
Fraude à la carte | Fraude | Utilisation frauduleuse d'une carte ou de ses données (vol, contrefaçon, paiement à distance).
Skimming | Fraude | Copie des données de piste magnétique d'une carte au moyen d'un dispositif dissimulé.
Carding | Fraude | Test et revente de données de cartes volées sur des places de marché illicites.
Fraude au crédit | Fraude | Obtention d'un crédit au moyen d'informations fausses ou d'une identité usurpée, sans intention de rembourser.
Bust-out | Fraude | Constitution d'un historique crédible puis utilisation maximale des lignes de crédit avant disparition.
Fraude à l'assurance | Fraude | Déclaration de sinistre fictif, exagéré ou provoqué pour obtenir une indemnisation.
Fraude interne | Fraude | Fraude commise par un collaborateur (détournement, faux comptes, contournement de contrôles).
Fraude comptable | Fraude | Manipulation des états financiers pour tromper investisseurs, prêteurs ou autorités.
Chaîne de Ponzi | Fraude | Escroquerie rémunérant les investisseurs anciens avec les fonds des nouveaux, sans activité réelle.
Pyramide financière | Fraude | Système où les gains dépendent du recrutement de nouveaux participants.
Arnaque à l'investissement | Fraude | Offre fictive de placement (crypto, forex, diamants) promettant des rendements élevés.
Romance scam | Fraude | Escroquerie sentimentale par laquelle le fraudeur obtient des fonds après avoir gagné la confiance de la victime.
Pig butchering | Fraude | Escroquerie combinant relation de confiance et faux investissement crypto, souvent opérée depuis des centres organisés.
Fraude à la TVA carrousel | Fraude | Fraude intracommunautaire où un opérateur collecte la TVA sans la reverser puis disparaît (trader manquant).
Trader manquant | Fraude | Société qui collecte la TVA dans une fraude carrousel et disparaît sans la reverser.
Fraude aux prestations sociales | Fraude | Obtention indue d'aides ou prestations par fausse déclaration.
Fraude aux aides publiques | Fraude | Détournement de subventions ou prêts garantis par l'État (ex. PGE) au moyen de déclarations mensongères.
Fraude au chèque | Fraude | Vol, falsification ou contrefaçon de chèques.
Faux ordres de virement | Fraude | Ordres de paiement falsifiés ou émis sans mandat du titulaire.
Ingénierie sociale | Fraude | Manipulation psychologique visant à obtenir informations ou actions de la victime.
Business Email Compromise (BEC) | Fraude | Compromission ou imitation de messageries professionnelles pour détourner des paiements.
Fraude au marketplace | Fraude | Ventes fictives, faux vendeurs ou faux acheteurs sur plateformes en ligne.
Triangulation fraud | Fraude | Faux vendeur en ligne qui exécute la commande avec une carte volée et encaisse le paiement du vrai client.
Bon de commande frauduleux | Fraude | Commande passée au nom d'une entreprise réelle sans intention de payer les marchandises.
Abus de biens sociaux | Fraude | Usage des biens ou du crédit d'une société par un dirigeant, de mauvaise foi, contraire à l'intérêt social (art. L241-3 C. com.).
Banqueroute | Fraude | Infraction du dirigeant d'une entreprise en procédure collective (détournement d'actif, comptabilité fictive…).
Organisation frauduleuse d'insolvabilité | Fraude | Fait d'organiser ou d'aggraver son insolvabilité pour se soustraire à ses créanciers.
Analyse de lien (link analysis) | Fraude | Technique de mise en relation d'entités (comptes, adresses, appareils, téléphones) pour révéler des réseaux de fraude.
Empreinte d'appareil (device fingerprinting) | Fraude | Identification d'un appareil à partir de ses caractéristiques pour détecter des comptes liés.
Velocity check | Fraude | Contrôle de la fréquence d'événements (ouvertures, paiements) sur une courte période.
# ===================== FISCALITÉ =====================
Fraude fiscale | Fiscalité | Soustraction frauduleuse à l'établissement ou au paiement de l'impôt (art. 1741 CGI).
Blanchiment de fraude fiscale | Fiscalité | Blanchiment du produit d'une fraude fiscale ; la fraude fiscale est une infraction sous-jacente en France.
Évasion fiscale | Fiscalité | Réduction de l'impôt par des moyens à la limite de la légalité, souvent par délocalisation de bases taxables.
Optimisation fiscale | Fiscalité | Utilisation légale des dispositifs fiscaux pour réduire la charge d'impôt.
Abus de droit fiscal | Fiscalité | Montage à but exclusivement (ou principalement) fiscal, contraire à l'intention du législateur (art. L64 et L64 A LPF).
Paradis fiscal | Fiscalité | Juridiction à fiscalité faible ou nulle, à opacité et à faible coopération administrative.
Liste UE des juridictions non coopératives | Fiscalité | Liste établie par le Conseil de l'UE des pays ne respectant pas les standards de bonne gouvernance fiscale.
ETNC | Fiscalité | États et territoires non coopératifs au sens de l'article 238-0 A du CGI, entraînant des mesures fiscales dissuasives.
Prix de transfert | Fiscalité | Prix pratiqués entre entreprises d'un même groupe ; doivent respecter le principe de pleine concurrence.
Principe de pleine concurrence | Fiscalité | Les transactions intragroupe doivent être conclues aux conditions qu'appliqueraient des parties indépendantes.
BEPS | Fiscalité | Projet OCDE/G20 contre l'érosion de la base d'imposition et le transfert de bénéfices.
Pilier 2 (impôt minimum mondial) | Fiscalité | Impôt minimum effectif de 15 % pour les groupes réalisant plus de 750 M€ de chiffre d'affaires.
Établissement stable | Fiscalité | Installation fixe d'affaires créant une imposition dans l'État où elle se situe.
Domiciliation fiscale | Fiscalité | Lieu de résidence fiscale déterminant l'État qui impose l'ensemble des revenus.
Société interposée | Fiscalité | Structure placée entre le contribuable et ses revenus pour les faire échapper à l'impôt.
Compte non déclaré à l'étranger | Fiscalité | Compte détenu hors de France sans déclaration annuelle (formulaire 3916), sanctionné par une amende.
Échange automatique d'informations (CRS) | Fiscalité | Norme OCDE d'échange annuel des informations sur les comptes financiers des non-résidents.
FATCA | Fiscalité | Loi américaine obligeant les institutions financières étrangères à déclarer les comptes des contribuables américains.
DAC6 | Fiscalité | Directive européenne imposant la déclaration des dispositifs transfrontières de planification fiscale agressive.
Régularisation fiscale | Fiscalité | Démarche spontanée d'un contribuable pour déclarer des avoirs ou revenus non déclarés.
Fraude à la TVA | Fiscalité | Soustraction de la TVA due ou obtention indue de remboursements (fausses factures, carrousel).
Fausse facture | Fiscalité | Facture fictive ou de complaisance utilisée pour minorer l'impôt ou justifier des flux.
Travail dissimulé | Fiscalité | Activité ou emploi non déclaré, générant fraude sociale et fiscale et des flux en espèces.
Police fiscale (SEJF) | Fiscalité | Service d'enquêtes judiciaires des finances chargé des enquêtes sur la fraude fiscale complexe.
Parquet national financier (PNF) | Fiscalité | Parquet spécialisé dans la grande délinquance économique et financière (corruption, fraude fiscale complexe).
# ===================== CRYPTO-ACTIFS =====================
Crypto-actif | Crypto-actifs | Représentation numérique de valeur ou de droits utilisant une technologie de registre distribué.
Blockchain | Crypto-actifs | Registre distribué, horodaté et partagé d'opérations, organisé en blocs chaînés.
Stablecoin | Crypto-actifs | Crypto-actif visant une valeur stable par adossement à une monnaie ou à un panier d'actifs.
Jeton de monnaie électronique (EMT) | Crypto-actifs | Stablecoin adossé à une seule monnaie officielle au sens de MiCA.
Jeton se référant à des actifs (ART) | Crypto-actifs | Stablecoin adossé à plusieurs actifs au sens de MiCA.
MiCA | Crypto-actifs | Règlement (UE) 2023/1114 encadrant l'émission de crypto-actifs et les prestataires de services (CASP).
CASP (PSCA) | Crypto-actifs | Prestataire de services sur crypto-actifs agréé au titre de MiCA.
PSAN | Crypto-actifs | Prestataire de services sur actifs numériques enregistré auprès de l'AMF, régime français antérieur à MiCA.
Règle de voyage (Travel Rule) | Crypto-actifs | Obligation de transmettre les informations sur l'émetteur et le bénéficiaire des transferts de crypto-actifs (règlement TFR 2023/1113).
Portefeuille non hébergé (self-hosted wallet) | Crypto-actifs | Portefeuille dont l'utilisateur contrôle seul les clés privées, sans prestataire.
Clé privée | Crypto-actifs | Secret cryptographique permettant de disposer des crypto-actifs d'une adresse.
Adresse blockchain | Crypto-actifs | Identifiant public permettant de recevoir des crypto-actifs.
Mixer (mélangeur) | Crypto-actifs | Service mélangeant les fonds de plusieurs utilisateurs pour rompre la traçabilité.
Privacy coin | Crypto-actifs | Crypto-actif conçu pour masquer montants et parties (Monero, Zcash).
Chain hopping | Crypto-actifs | Conversion successive entre blockchains pour brouiller la piste des fonds.
Bridge (pont inter-chaînes) | Crypto-actifs | Protocole de transfert d'actifs entre blockchains, souvent cible de piratages.
DeFi | Crypto-actifs | Finance décentralisée : services financiers fournis par des protocoles automatisés sans intermédiaire central.
DEX | Crypto-actifs | Plateforme d'échange décentralisée fonctionnant par contrats intelligents.
Contrat intelligent | Crypto-actifs | Programme exécuté sur une blockchain appliquant automatiquement des conditions prédéfinies.
NFT | Crypto-actifs | Jeton non fongible représentant un actif numérique unique, exposé au wash trading.
Wash trading | Crypto-actifs | Opérations d'achat-vente avec soi-même pour créer un volume ou un prix artificiel.
Rug pull | Crypto-actifs | Escroquerie où les créateurs d'un projet retirent brutalement la liquidité et disparaissent.
Analyse on-chain | Crypto-actifs | Analyse des transactions publiques d'une blockchain pour tracer les flux et attribuer des adresses.
Clustering d'adresses | Crypto-actifs | Regroupement d'adresses présumées contrôlées par une même entité.
Ransomware | Crypto-actifs | Logiciel malveillant chiffrant des données contre rançon, généralement payée en crypto-actifs.
Off-ramp / on-ramp | Crypto-actifs | Points de conversion entre crypto-actifs et monnaie officielle, lieux privilégiés de la vigilance.
Distributeur de crypto (crypto ATM) | Crypto-actifs | Automate d'achat ou de vente de crypto-actifs contre espèces, à risque élevé.
P2P crypto | Crypto-actifs | Échange direct entre particuliers, souvent hors plateforme régulée.
# ===================== CORRUPTION & ÉTHIQUE =====================
Corruption active | Corruption | Fait de proposer ou d'accorder un avantage indu à une personne pour qu'elle accomplisse ou s'abstienne d'accomplir un acte de sa fonction.
Corruption passive | Corruption | Fait pour une personne de solliciter ou d'accepter un avantage indu en échange d'un acte de sa fonction.
Trafic d'influence | Corruption | Abus d'influence réelle ou supposée en vue d'obtenir une décision favorable d'une autorité, contre avantage.
Prise illégale d'intérêts | Corruption | Fait pour un agent public de prendre un intérêt dans une opération dont il a la charge.
Favoritisme | Corruption | Octroi d'un avantage injustifié dans un marché public en violation des règles d'égalité.
Détournement de fonds publics | Corruption | Fait pour un agent public de détourner des fonds qui lui ont été remis en raison de ses fonctions.
Concussion | Corruption | Fait pour un agent public de percevoir des sommes qu'il sait ne pas être dues.
Pot-de-vin | Corruption | Somme ou avantage versé pour obtenir indûment une décision.
Paiement de facilitation | Corruption | Petit paiement à un agent public pour accélérer une formalité ; interdit en droit français.
Commission occulte | Corruption | Rémunération dissimulée d'un intermédiaire servant à financer la corruption.
Intermédiaire à risque | Corruption | Agent commercial ou consultant dont la rémunération ou la prestation est mal justifiée.
Loi Sapin II | Corruption | Loi n° 2016-1691 imposant un programme anticorruption aux grandes entreprises et créant l'AFA.
AFA | Corruption | Agence française anticorruption, chargée de contrôler les programmes de conformité anticorruption.
Cartographie des risques de corruption | Corruption | Pilier Sapin II identifiant, évaluant et hiérarchisant les risques de corruption par processus.
Évaluation des tiers | Corruption | Due diligence sur clients, fournisseurs et intermédiaires selon leur exposition au risque de corruption.
CJIP | Corruption | Convention judiciaire d'intérêt public : transaction pénale avec une personne morale (amende, programme de mise en conformité).
FCPA | Corruption | Foreign Corrupt Practices Act : loi américaine réprimant la corruption d'agents publics étrangers.
UK Bribery Act | Corruption | Loi britannique de 2010 réprimant la corruption, dont le défaut de prévention par une entreprise.
Lanceur d'alerte | Corruption | Personne signalant, sans contrepartie financière directe et de bonne foi, des faits illicites ; protégée par la loi Waserman.
Conflit d'intérêts | Corruption | Situation où un intérêt personnel peut influencer l'exercice impartial d'une fonction.
Cadeaux et invitations | Corruption | Avantages offerts ou reçus devant être encadrés (seuils, registre, validation).
Mécénat et sponsoring | Corruption | Dons et parrainages pouvant masquer des avantages indus et devant faire l'objet de diligences.
Indice de perception de la corruption (IPC) | Corruption | Classement annuel de Transparency International mesurant la corruption perçue dans le secteur public.
Kleptocratie | Corruption | Système de gouvernement où les dirigeants s'enrichissent par le détournement des ressources publiques.
Biens mal acquis | Corruption | Patrimoine acquis dans un pays avec des fonds détournés à l'étranger par des dirigeants ou leurs proches.
Recouvrement des avoirs | Corruption | Identification, saisie et restitution des avoirs d'origine illicite.
AGRASC | Corruption | Agence de gestion et de recouvrement des avoirs saisis et confisqués.
# ===================== AUTORITÉS & RÉGULATION =====================
AMF | Régulation | Autorité des marchés financiers, régulateur français des marchés et des PSAN.
Banque de France | Régulation | Banque centrale française, membre de l'Eurosystème, adossée à l'ACPR.
BCE | Régulation | Banque centrale européenne, responsable de la politique monétaire et de la supervision bancaire (MSU).
MSU | Régulation | Mécanisme de surveillance unique : supervision directe des banques importantes de la zone euro par la BCE.
EBA | Régulation | Autorité bancaire européenne, qui élabore normes et orientations, y compris en LCB-FT jusqu'au transfert à l'AMLA.
ESMA | Régulation | Autorité européenne des marchés financiers.
EIOPA | Régulation | Autorité européenne des assurances et des pensions professionnelles.
DGFiP | Régulation | Direction générale des Finances publiques.
DGDDI (douanes) | Régulation | Direction générale des douanes et droits indirects, compétente pour le contrôle des flux de marchandises et d'espèces transfrontaliers.
Déclaration d'argent liquide | Régulation | Obligation de déclarer en douane les sommes d'au moins 10 000 € transportées à l'entrée ou à la sortie de l'UE.
CNIL | Régulation | Commission nationale de l'informatique et des libertés.
RGPD | Régulation | Règlement général sur la protection des données, applicable aux traitements LCB-FT.
FinCEN | Régulation | Cellule de renseignement financier américaine, rattachée au Trésor.
BIS (Bureau of Industry and Security) | Régulation | Agence du Département du Commerce américain administrant les EAR.
FCA | Régulation | Financial Conduct Authority, régulateur britannique des services financiers.
FINMA | Régulation | Autorité fédérale suisse de surveillance des marchés financiers.
BaFin | Régulation | Autorité fédérale allemande de supervision financière.
Commission des sanctions (ACPR) | Régulation | Organe juridictionnel de l'ACPR prononçant sanctions disciplinaires et pécuniaires.
Mise en demeure | Régulation | Injonction de l'autorité de se conformer à une obligation dans un délai donné.
Lignes directrices | Régulation | Documents interprétatifs publiés par une autorité pour préciser ses attentes.
Code monétaire et financier (CMF) | Régulation | Code regroupant les règles applicables aux activités bancaires, financières et LCB-FT en France.
DORA | Régulation | Règlement (UE) 2022/2554 sur la résilience opérationnelle numérique du secteur financier, applicable depuis le 17 janvier 2025.
CSRD | Régulation | Directive sur la publication d'informations de durabilité par les entreprises.
CSDDD | Régulation | Directive sur le devoir de vigilance des entreprises en matière de durabilité.
Devoir de vigilance | Régulation | Loi n° 2017-399 imposant aux grandes entreprises un plan de vigilance sur les droits humains et l'environnement.
AI Act | Régulation | Règlement (UE) 2024/1689 sur l'intelligence artificielle, encadrant notamment les systèmes à haut risque.
# ===================== GOUVERNANCE, CONTRÔLE & OUTILS =====================
Conformité (compliance) | Gouvernance | Fonction veillant au respect des lois, règlements et normes professionnelles applicables.
Risque de non-conformité | Gouvernance | Risque de sanction, de perte financière ou d'atteinte à la réputation lié au non-respect des règles.
Risque de réputation | Gouvernance | Risque d'atteinte à l'image et à la confiance des clients, investisseurs et autorités.
Risque opérationnel | Gouvernance | Risque de pertes résultant de processus, personnes, systèmes inadéquats ou d'événements externes.
Contrôle interne | Gouvernance | Ensemble des dispositifs permettant la maîtrise des activités et des risques.
Arrêté du 3 novembre 2014 | Gouvernance | Texte français relatif au contrôle interne des établissements bancaires et des prestataires de services d'investissement.
Plan de contrôle | Gouvernance | Programme formalisé des contrôles à réaliser, leur fréquence et leurs responsables.
Piste d'audit | Gouvernance | Traçabilité permettant de reconstituer une opération ou une décision de bout en bout.
Comité de conformité | Gouvernance | Instance de gouvernance examinant les risques de non-conformité et les décisions sensibles.
Escalade | Gouvernance | Remontée d'un dossier au niveau hiérarchique ou à la fonction compétente pour décision.
Matrice de risques | Gouvernance | Outil croisant probabilité et impact pour hiérarchiser les risques.
Risque inhérent | Gouvernance | Niveau de risque avant prise en compte des contrôles.
Risque résiduel | Gouvernance | Niveau de risque subsistant après application des contrôles.
Indicateur clé de risque (KRI) | Gouvernance | Mesure quantitative suivie pour anticiper l'évolution d'un risque.
Tableau de bord conformité | Gouvernance | Synthèse périodique des indicateurs de conformité pour la direction.
Formation LCB-FT | Gouvernance | Obligation de former et sensibiliser régulièrement le personnel exposé.
Data lineage | Outils & données | Traçabilité de l'origine et des transformations des données utilisées par les outils de conformité.
Qualité des données | Outils & données | Exactitude, exhaustivité et fraîcheur des données client et transactionnelles, condition de l'efficacité des contrôles.
Moteur de règles | Outils & données | Logiciel appliquant des règles paramétrées pour produire des alertes.
Apprentissage automatique (ML) | Outils & données | Techniques statistiques permettant à un système d'apprendre des données pour détecter, classer ou prévoir.
Apprentissage supervisé | Outils & données | Apprentissage à partir d'exemples étiquetés (ex. alertes déclarées ou non).
Apprentissage non supervisé | Outils & données | Recherche de structures sans étiquettes (clustering, détection d'anomalies).
Isolation Forest | Outils & données | Algorithme de détection d'anomalies isolant les observations atypiques par partitions aléatoires.
Explicabilité | Outils & données | Capacité à justifier la décision d'un modèle, exigée par les superviseurs et l'AI Act.
Validation de modèle | Outils & données | Revue indépendante de la conception, des données et de la performance d'un modèle.
Dérive de modèle | Outils & données | Dégradation de la performance d'un modèle lorsque les données évoluent.
OSINT | Outils & données | Renseignement en sources ouvertes : registres, presse, réseaux sociaux, bases publiques.
Graphe de relations | Outils & données | Représentation des liens entre personnes, sociétés, comptes et adresses.
Géolocalisation IP | Outils & données | Localisation approximative d'un appareil à partir de son adresse IP, utilisée en prévention de la fraude.
VPN / proxy | Outils & données | Outils masquant l'adresse IP réelle ; signal de risque en entrée en relation à distance.
# ===================== COMMERCE INTERNATIONAL & ASSURANCE =====================
Financement du commerce (trade finance) | Commerce international | Instruments bancaires facilitant les échanges internationaux (crédit documentaire, garanties, affacturage).
Remise documentaire | Commerce international | Encaissement par lequel la banque remet les documents à l'importateur contre paiement ou acceptation.
Garantie à première demande | Commerce international | Engagement bancaire autonome de payer sur simple demande du bénéficiaire.
Double facturation | Commerce international | Émission de plusieurs factures pour une même expédition afin d'obtenir plusieurs paiements.
Prix de marché de référence | Commerce international | Prix moyen d'une marchandise servant à détecter sur- ou sous-facturation.
Dual-use red flags | Commerce international | Signaux d'alerte : client nouveau, usage final vague, paiement par tiers, itinéraire illogique, refus d'installation.
Assurance-vie | Assurance | Contrat d'épargne ou de prévoyance exposé au blanchiment (versements importants, rachats rapides, changements de bénéficiaire).
Rachat anticipé | Assurance | Retrait des fonds d'un contrat avant terme ; un rachat rapide après versement est un signal d'alerte.
Bénéficiaire de contrat | Assurance | Personne désignée pour recevoir le capital ; sa modification doit être contrôlée.
Contrat de capitalisation | Assurance | Placement anonyme dans le passé, transmissible, nécessitant une vigilance sur le souscripteur et le porteur.
"""


def terms():
    out = []
    for line in RAW.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) == 3:
            out.append(dict(terme=parts[0], categorie=parts[1], definition=parts[2], source="CWP (rédaction)"))
    return out
