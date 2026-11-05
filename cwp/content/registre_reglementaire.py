"""
cwp.content.registre_reglementaire — Registre des textes réglementaires suivis par CWP (2021 → 2031).

Un texte = une entrée. Pour ajouter un texte, copiez un bloc et adaptez-le.
- adoption / application : "AAAA-MM-JJ" ; application = date d'application principale
  (ou date limite de transposition pour une directive).
- jalons : autres échéances datées (entrée en vigueur, application par étapes…).
- projet=True : texte non encore publié (accord politique, proposition).
- a_verifier : point du calendrier susceptible d'évoluer.
Les dates proviennent du Journal officiel de l'UE, de Légifrance et des publications des autorités ;
vérifiez-les dans le texte officiel avant toute diffusion externe.
"""

THEMES = ["LCB-FT", "Sanctions & embargos", "Crypto-actifs", "Paiements", "Résilience & numérique",
          "Prudentiel", "ESG & fiscalité"]


def _eli(kind: str, year: int, num: int) -> str:
    return f"https://eur-lex.europa.eu/eli/{kind}/{year}/{num}/oj"


def _lgf(q: str) -> str:
    return "https://www.legifrance.gouv.fr/search/all?tab_selection=all&query=" + q.replace(" ", "+")


EBA_PUBS = "https://www.eba.europa.eu/publications-and-media/publications"
FATF_RECS = "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html"

REGISTRE = [
    # ------------------------------------------------------------------ LCB-FT — paquet européen
    dict(id="amlr", nom="AMLR — Règlement unique LCB-FT", theme="LCB-FT", juridiction="Union européenne",
         type="Règlement", reference="Règlement (UE) 2024/1624 du 31 mai 2024",
         adoption="2024-05-31", application="2027-07-10",
         jalons=[("2024-07-09", "Entrée en vigueur"), ("2027-07-10", "Application directe dans toute l'UE"),
                 ("2029-07-10", "Obligations étendues aux agents et clubs de football professionnels")],
         cible="Banques, PSP / EME, PSAN (CASP), assurances, SGP, professions non financières",
         objectif="Remplacer la mosaïque des transpositions nationales par un « single rulebook » LCB-FT "
                  "directement applicable dans toute l'UE.",
         obligation="Vigilance harmonisée : identification et vérification des clients, bénéficiaires effectifs "
                    "(seuil de 25 % et contrôle par d'autres moyens), revue périodique selon le risque, "
                    "gestion du risque de contournement des sanctions financières ciblées.",
         contrainte="Plafond européen de 10 000 € pour les paiements en espèces ; sanctions renforcées "
                    "prévues par l'AMLD6 sous la supervision coordonnée de l'AMLA.",
         lien=_eli("reg", 2024, 1624)),
    dict(id="amld6", nom="AMLD6 — Sixième directive LCB-FT", theme="LCB-FT", juridiction="Union européenne",
         type="Directive", reference="Directive (UE) 2024/1640 du 31 mai 2024",
         adoption="2024-05-31", application="2027-07-10",
         jalons=[("2025-07-10", "Transposition de l'article 74"),
                 ("2026-07-10", "Registres des bénéficiaires effectifs et registres immobiliers (art. 11 à 15)"),
                 ("2027-07-10", "Date limite générale de transposition"),
                 ("2029-07-10", "Point d'accès unique aux informations immobilières (art. 18)")],
         cible="États membres, superviseurs, CRF (TRACFIN) ; impacts indirects pour tous les assujettis",
         objectif="Organiser les mécanismes nationaux : registres des bénéficiaires effectifs, cellules de "
                  "renseignement financier, pouvoirs et coopération des superviseurs.",
         obligation="Registres BE interconnectés et accès des assujettis, signalement des divergences, "
                    "méthodologie de supervision fondée sur les risques.",
         contrainte="Sanctions pécuniaires harmonisées : pour les établissements de crédit et financiers, "
                    "jusqu'à au moins 10 M€ ou 10 % du chiffre d'affaires annuel.",
         lien=_eli("dir", 2024, 1640)),
    dict(id="amlar", nom="AMLAR — Création de l'AMLA", theme="LCB-FT", juridiction="Union européenne",
         type="Règlement", reference="Règlement (UE) 2024/1620 du 31 mai 2024",
         adoption="2024-05-31", application="2028-07-01",
         jalons=[("2024-06-26", "Entrée en vigueur"),
                 ("2026-07-10", "Premières orientations et normes techniques de l'AMLA"),
                 ("2027-07-01", "Sélection des entités soumises à la supervision directe (prévue courant 2027)"),
                 ("2028-07-01", "Début de la supervision directe par l'AMLA (prévu)")],
         a_verifier="Calendrier de sélection et de supervision directe annoncé par l'AMLA.",
         cible="Établissements financiers transfrontaliers à haut risque (supervision directe), "
               "superviseurs nationaux (ACPR, AMF)",
         objectif="Créer l'Autorité européenne de lutte contre le blanchiment (Francfort), chargée de "
                  "coordonner les superviseurs et les CRF et de superviser directement certains établissements.",
         obligation="Normes techniques et orientations de l'AMLA à intégrer dans les dispositifs ; "
                    "remontée de données de supervision vers l'AMLA.",
         contrainte="Pour les entités sélectionnées : supervision directe, pouvoirs d'enquête et de sanction "
                    "de l'AMLA.",
         lien=_eli("reg", 2024, 1620)),
    dict(id="arrete-2021", nom="Arrêté contrôle interne LCB-FT et gel des avoirs", theme="LCB-FT",
         juridiction="France", type="Arrêté",
         reference="Arrêté du 6 janvier 2021 relatif au dispositif et au contrôle interne en matière de LCB-FT "
                   "et de gel des avoirs",
         adoption="2021-01-06", application="2021-03-01",
         jalons=[("2021-03-01", "Entrée en vigueur")],
         cible="Organismes financiers assujettis supervisés par l'ACPR",
         objectif="Préciser l'organisation du dispositif LCB-FT et de gel des avoirs : classification des "
                  "risques, procédures, contrôle interne et responsabilités au sein des groupes.",
         obligation="Classification des risques tenant compte des travaux du GAFI et de l'UE, procédures "
                    "écrites, dispositif de détection des opérations visant à contourner les mesures de gel.",
         contrainte="Contrôle interne proportionné et responsabilité de la maison mère sur le dispositif "
                    "de groupe ; manquements sanctionnables par l'ACPR.",
         lien=_lgf("arrêté 6 janvier 2021 contrôle interne blanchiment")),
    # ------------------------------------------------------------------ LCB-FT — orientations EBA
    dict(id="eba-gl-2022-05", nom="Orientations EBA sur le responsable LCB-FT", theme="LCB-FT",
         juridiction="Union européenne", type="Orientations", reference="EBA/GL/2022/05",
         adoption="2022-06-14", application="2022-12-01", jalons=[],
         cible="Établissements de crédit et financiers",
         objectif="Préciser le rôle du membre de l'organe de direction responsable LCB-FT et du responsable "
                  "de la conformité LCB-FT.",
         obligation="Désignation formelle, profil et moyens du responsable LCB-FT, reporting régulier à "
                    "l'organe de direction, organisation au niveau du groupe.",
         contrainte="Le superviseur apprécie l'adéquation des moyens et de l'indépendance de la fonction.",
         lien=EBA_PUBS),
    dict(id="eba-gl-2022-15", nom="Orientations EBA sur l'entrée en relation à distance", theme="LCB-FT",
         juridiction="Union européenne", type="Orientations", reference="EBA/GL/2022/15",
         adoption="2022-11-22", application="2023-10-02", jalons=[],
         cible="Établissements de crédit et financiers pratiquant l'onboarding à distance",
         objectif="Encadrer les solutions d'identification et de vérification à distance des clients.",
         obligation="Politique d'onboarding à distance, contrôle de la fiabilité des documents et des données "
                    "biométriques, tests et suivi des prestataires.",
         contrainte="L'établissement reste responsable des solutions externalisées et de leur efficacité.",
         lien=EBA_PUBS),
    dict(id="eba-gl-2024-01", nom="Orientations EBA facteurs de risque BC-FT étendues aux CASP", theme="LCB-FT",
         juridiction="Union européenne", type="Orientations", reference="EBA/GL/2024/01",
         adoption="2024-01-16", application="2024-12-30", jalons=[],
         cible="PSAN / CASP, banques en relation avec des CASP",
         objectif="Intégrer les prestataires de services sur crypto-actifs dans les orientations sur les "
                  "facteurs de risque BC-FT.",
         obligation="Facteurs de risque spécifiques aux crypto-actifs (adresses auto-hébergées, mixeurs, "
                    "anonymat) et mesures de vigilance adaptées.",
         contrainte="Prise en compte attendue dans la classification des risques et la vigilance des CASP.",
         lien=EBA_PUBS),
    # ------------------------------------------------------------------ Sanctions & embargos
    dict(id="dual-use", nom="Règlement « biens à double usage »", theme="Sanctions & embargos",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2021/821 du 20 mai 2021",
         adoption="2021-05-20", application="2021-09-09", jalons=[("2021-09-09", "Application")],
         cible="Exportateurs, banques finançant le commerce international (trade finance)",
         objectif="Refondre le régime de contrôle des exportations, transferts, courtage et transit des biens "
                  "à double usage.",
         obligation="Licences d'exportation, contrôles « catch-all », programme interne de conformité "
                    "pour les exportateurs.",
         contrainte="Exportation sans licence pénalement sanctionnée ; vigilance attendue des banques sur "
                    "les opérations de trade finance.",
         lien=_eli("reg", 2021, 821)),
    dict(id="dir-2024-1226", nom="Directive pénalisant la violation des mesures restrictives",
         theme="Sanctions & embargos", juridiction="Union européenne", type="Directive",
         reference="Directive (UE) 2024/1226 du 24 avril 2024",
         adoption="2024-04-24", application="2025-05-20", jalons=[("2025-05-20", "Date limite de transposition")],
         cible="Personnes morales et physiques, établissements financiers",
         objectif="Harmoniser les infractions pénales et les peines en cas de violation ou de contournement "
                  "des sanctions de l'UE.",
         obligation="Infractions définies : mise à disposition de fonds, non-gel, contournement, fausses "
                    "informations aux autorités.",
         contrainte="Amendes pour les personnes morales jusqu'à 5 % du chiffre d'affaires mondial ou 40 M€ "
                    "selon l'infraction.",
         lien=_eli("dir", 2024, 1226)),
    dict(id="eba-gl-2024-14", nom="Orientations EBA sur les mesures restrictives", theme="Sanctions & embargos",
         juridiction="Union européenne", type="Orientations", reference="EBA/GL/2024/14 et EBA/GL/2024/15",
         adoption="2024-11-14", application="2025-12-30", jalons=[("2025-12-30", "Application")],
         cible="Banques, PSP / EME, PSAN (CASP)",
         objectif="Fixer un standard européen pour les politiques, procédures et contrôles internes de mise en "
                  "œuvre des sanctions de l'UE et nationales.",
         obligation="Évaluation de l'exposition aux sanctions, gouvernance, filtrage des clients et des "
                    "transactions, gestion des alertes et calibrage des outils.",
         contrainte="Application depuis le 30 décembre 2025 ; contrôle par l'ACPR et l'AMF (orientations "
                    "reprises par l'AMF, DOC-2025-02).",
         lien="https://www.amf-france.org/en/regulation/policy/doc-2025-02"),
    dict(id="dir-2024-1260", nom="Directive recouvrement et confiscation des avoirs",
         theme="Sanctions & embargos", juridiction="Union européenne", type="Directive",
         reference="Directive (UE) 2024/1260 du 24 avril 2024",
         adoption="2024-04-24", application="2026-11-23",
         jalons=[("2024-05-22", "Entrée en vigueur"), ("2026-11-23", "Date limite de transposition"),
                 ("2027-05-24", "Stratégie nationale de recouvrement des avoirs")],
         cible="Autorités judiciaires et répressives ; établissements sollicités pour le dépistage et le gel",
         objectif="Renforcer le dépistage, le gel, la confiscation et la gestion des avoirs d'origine criminelle.",
         obligation="Enquêtes patrimoniales immédiates, gel rapide, confiscation élargie et de valeur, "
                    "confiscation des avoirs inexpliqués liés à la criminalité organisée.",
         contrainte="Hausse attendue des réquisitions et demandes de gel adressées aux établissements financiers.",
         lien=_eli("dir", 2024, 1260)),
    # ------------------------------------------------------------------ Crypto-actifs
    dict(id="tfr", nom="TFR — Travel rule fonds et crypto-actifs", theme="Crypto-actifs",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2023/1113 du 31 mai 2023",
         adoption="2023-05-31", application="2024-12-30", jalons=[("2024-12-30", "Application")],
         cible="PSP, EME, PSAN / CASP",
         objectif="Assurer la traçabilité des transferts de fonds et étendre la « travel rule » aux "
                  "transferts de crypto-actifs.",
         obligation="Transmission des informations sur le donneur d'ordre et le bénéficiaire, sans seuil pour "
                    "les crypto-actifs ; contrôles sur les adresses auto-hébergées.",
         contrainte="Transferts incomplets à rejeter ou suspendre ; prestataires défaillants à signaler.",
         lien=_eli("reg", 2023, 1113)),
    dict(id="eba-gl-2024-11", nom="Orientations EBA « travel rule »", theme="Crypto-actifs",
         juridiction="Union européenne", type="Orientations", reference="EBA/GL/2024/11",
         adoption="2024-07-04", application="2024-12-30", jalons=[],
         cible="PSP, PSAN / CASP",
         objectif="Préciser les procédures de détection des informations manquantes et de traitement "
                  "des transferts incomplets.",
         obligation="Procédures de vérification des champs, gestion des transferts incomplets, "
                    "évaluation des contreparties.",
         contrainte="Suivi des prestataires défaillants de manière répétée et signalement aux autorités.",
         lien=EBA_PUBS),
    dict(id="mica", nom="MiCA — Marchés de crypto-actifs", theme="Crypto-actifs",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2023/1114 du 31 mai 2023",
         adoption="2023-05-31", application="2024-12-30",
         jalons=[("2024-06-30", "Jetons se référant à des actifs et jetons de monnaie électronique"),
                 ("2024-12-30", "Application générale (CASP)"),
                 ("2026-07-01", "Fin du régime transitoire des PSAN en France")],
         cible="PSAN / CASP, émetteurs de jetons, banques offrant des services crypto",
         objectif="Créer un cadre européen unique pour l'émission de crypto-actifs et les services sur "
                  "crypto-actifs, avec un agrément valable dans toute l'UE.",
         obligation="Agrément CASP, exigences de gouvernance, de fonds propres, de conservation et de "
                    "protection des clients ; règles pour les émetteurs de stablecoins.",
         contrainte="Activité sans agrément MiCA interdite après la période transitoire.",
         lien=_eli("reg", 2023, 1114)),
    dict(id="ord-2024-936", nom="Ordonnance d'adaptation à MiCA", theme="Crypto-actifs", juridiction="France",
         type="Ordonnance", reference="Ordonnance n° 2024-936 du 15 octobre 2024 relative aux marchés de crypto-actifs",
         adoption="2024-10-15", application="2024-12-30",
         jalons=[("2024-10-18", "Dispositions sur les jetons (EMT, ART)"), ("2024-12-30", "Application générale"),
                 ("2026-07-01", "Fin du régime national des PSAN")],
         cible="PSAN / CASP, émetteurs de jetons",
         objectif="Adapter le droit français à MiCA et organiser la sortie du régime PSAN national.",
         obligation="Désignation de l'AMF et de l'ACPR comme autorités compétentes, articulation avec le "
                    "code monétaire et financier.",
         contrainte="Les PSAN enregistrés devaient obtenir l'agrément MiCA avant le 1er juillet 2026.",
         lien=_lgf("ordonnance 2024-936")),
    dict(id="ord-2024-937", nom="Ordonnance LCB-FT sur les transferts de crypto-actifs", theme="Crypto-actifs",
         juridiction="France", type="Ordonnance",
         reference="Ordonnance n° 2024-937 du 15 octobre 2024 relative au renforcement des obligations de LCB-FT "
                   "en matière de transfert de crypto-actifs",
         adoption="2024-10-15", application="2024-12-30", jalons=[],
         a_verifier="Date d'application alignée sur celle du TFR.",
         cible="PSAN / CASP, PSP",
         objectif="Transposer en droit français les modifications de la directive LCB-FT introduites par le TFR.",
         obligation="Intégration des CASP parmi les assujettis LCB-FT et vigilance sur les transferts de "
                    "crypto-actifs.",
         contrainte="Supervision partagée ACPR / AMF pendant la période transitoire jusqu'au 1er juillet 2026.",
         lien=_lgf("ordonnance 2024-937")),
    # ------------------------------------------------------------------ Paiements
    dict(id="ipr", nom="Règlement sur les virements instantanés", theme="Paiements",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2024/886 du 13 mars 2024",
         adoption="2024-03-13", application="2025-01-09",
         jalons=[("2025-01-09", "Réception des virements instantanés et filtrage sanctions quotidien"),
                 ("2025-10-09", "Émission des virements instantanés et vérification du bénéficiaire (VoP)"),
                 ("2027-04-09", "Obligations étendues aux établissements de paiement et de monnaie électronique")],
         cible="Banques, PSP / EME de la zone euro",
         objectif="Généraliser le virement instantané en euros, au même prix qu'un virement classique.",
         obligation="Vérification de concordance nom / IBAN avant paiement ; filtrage des clients contre les "
                    "listes de sanctions de l'UE au moins une fois par jour plutôt que transaction par transaction.",
         contrainte="Le PSP qui n'effectue pas la vérification du bénéficiaire est responsable du préjudice subi "
                    "par le payeur.",
         lien=_eli("reg", 2024, 886)),
    dict(id="psr-psd3", nom="PSR / PSD3 — Réforme des services de paiement", theme="Paiements",
         juridiction="Union européenne", type="Règlement", reference="Proposition de règlement PSR et directive PSD3 (juin 2023)",
         adoption="2025-11-27", application=None, projet=True,
         jalons=[("2025-11-27", "Accord provisoire Parlement / Conseil"),
                 ("2028-01-01", "Application attendue après une période transitoire d'environ 21 mois")],
         a_verifier="Textes définitifs et dates de publication / d'application à confirmer au Journal officiel.",
         cible="Banques, PSP / EME, plateformes en ligne",
         objectif="Moderniser les règles des services de paiement et renforcer la lutte contre la fraude.",
         obligation="Vérification nom / IBAN pour tous les virements, partage de données de fraude entre PSP, "
                    "renforcement de l'authentification forte.",
         contrainte="Remboursement intégral des victimes de fraude au faux conseiller sous conditions ; "
                    "responsabilité du PSP dépourvu de mesures antifraude adaptées.",
         lien="https://www.europarl.europa.eu/legislative-train/theme-an-economy-that-works-for-people/"
              "file-payment-services-and-electronic-money-services-(directive)"),
    dict(id="ccd2", nom="CCD2 — Directive crédit à la consommation", theme="Paiements",
         juridiction="Union européenne", type="Directive", reference="Directive (UE) 2023/2225 du 18 octobre 2023",
         adoption="2023-10-18", application="2026-11-20",
         jalons=[("2025-11-20", "Date limite de transposition"), ("2026-11-20", "Application")],
         cible="Prêteurs, établissements de crédit, intermédiaires, plateformes de « buy now pay later »",
         objectif="Moderniser la protection des emprunteurs, y compris pour le paiement fractionné et les "
                  "petits crédits.",
         obligation="Évaluation de solvabilité renforcée, informations précontractuelles, encadrement de la "
                    "publicité et de la vente en ligne.",
         contrainte="Sanctions effectives et dissuasives fixées par les États membres.",
         lien=_eli("dir", 2023, 2225)),
    # ------------------------------------------------------------------ Résilience & numérique
    dict(id="dora", nom="DORA — Résilience opérationnelle numérique", theme="Résilience & numérique",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2022/2554 du 14 décembre 2022",
         adoption="2022-12-14", application="2025-01-17", jalons=[("2025-01-17", "Application")],
         cible="Banques, assurances, PSP / EME, CASP, SGP, prestataires TIC critiques",
         objectif="Garantir la résilience numérique du secteur financier face aux incidents TIC et cyber.",
         obligation="Cadre de gestion du risque TIC, notification des incidents majeurs, tests de résilience, "
                    "registre des contrats avec les prestataires TIC.",
         contrainte="Supervision directe des prestataires TIC critiques par les autorités européennes.",
         lien=_eli("reg", 2022, 2554)),
    dict(id="ai-act", nom="AI Act — Règlement sur l'intelligence artificielle", theme="Résilience & numérique",
         juridiction="Union européenne", type="Règlement", reference="Règlement (UE) 2024/1689 du 13 juin 2024",
         adoption="2024-06-13", application="2026-08-02",
         jalons=[("2025-02-02", "Pratiques d'IA interdites"), ("2025-08-02", "Modèles d'IA à usage général"),
                 ("2026-08-02", "Application générale (dont systèmes à haut risque de l'annexe III)"),
                 ("2027-08-02", "Systèmes à haut risque de l'annexe I")],
         a_verifier="Le calendrier des systèmes à haut risque peut être décalé par l'omnibus numérique.",
         cible="Banques et assureurs utilisant l'IA (scoring de crédit, tarification), fournisseurs d'IA",
         objectif="Encadrer les systèmes d'IA selon leur niveau de risque.",
         obligation="Pour les systèmes à haut risque (ex. évaluation de solvabilité) : gestion des risques, "
                    "qualité des données, documentation, supervision humaine.",
         contrainte="Amendes jusqu'à 35 M€ ou 7 % du chiffre d'affaires mondial pour les pratiques interdites.",
         lien=_eli("reg", 2024, 1689)),
    # ------------------------------------------------------------------ Prudentiel
    dict(id="crr3", nom="CRR3 — Finalisation de Bâle III", theme="Prudentiel", juridiction="Union européenne",
         type="Règlement", reference="Règlement (UE) 2024/1623 du 31 mai 2024",
         adoption="2024-05-31", application="2025-01-01", jalons=[("2025-01-01", "Application")],
         cible="Établissements de crédit et entreprises d'investissement",
         objectif="Transposer la finalisation de Bâle III : risque de crédit, risque opérationnel, output floor.",
         obligation="Nouvelles méthodes de calcul des exigences de fonds propres et reporting associé.",
         contrainte="Plancher de fonds propres (output floor) introduit progressivement.",
         lien=_eli("reg", 2024, 1623)),
    dict(id="crd6", nom="CRD6 — Directive exigences de fonds propres", theme="Prudentiel",
         juridiction="Union européenne", type="Directive", reference="Directive (UE) 2024/1619 du 31 mai 2024",
         adoption="2024-05-31", application="2026-01-11",
         jalons=[("2026-01-10", "Date limite de transposition"),
                 ("2027-01-11", "Régime des succursales de pays tiers")],
         cible="Établissements de crédit, succursales de pays tiers",
         objectif="Renforcer la gouvernance, l'honorabilité des dirigeants et l'encadrement des succursales "
                  "de pays tiers.",
         obligation="Évaluation de l'aptitude des dirigeants, intégration des risques ESG, agrément des "
                    "succursales de pays tiers.",
         contrainte="Pouvoirs de sanction harmonisés des superviseurs.",
         lien=_eli("dir", 2024, 1619)),
    # ------------------------------------------------------------------ ESG & fiscalité
    dict(id="csrd", nom="CSRD — Reporting de durabilité", theme="ESG & fiscalité",
         juridiction="Union européenne", type="Directive", reference="Directive (UE) 2022/2464 du 14 décembre 2022",
         adoption="2022-12-14", application="2024-01-01",
         jalons=[("2024-01-01", "Premières entreprises (exercice 2024)")],
         a_verifier="Vagues suivantes reportées par la directive « stop-the-clock » (UE) 2025/794 et l'omnibus.",
         cible="Grandes entreprises et établissements financiers",
         objectif="Généraliser un reporting de durabilité normé (ESRS) et audité.",
         obligation="Double matérialité, publication selon les normes ESRS, assurance par un tiers.",
         contrainte="Calendrier progressif, en partie reporté par les textes omnibus.",
         lien=_eli("dir", 2022, 2464)),
    dict(id="dac8", nom="DAC8 — Échange d'informations sur les crypto-actifs", theme="ESG & fiscalité",
         juridiction="Union européenne", type="Directive", reference="Directive (UE) 2023/2226 du 17 octobre 2023",
         adoption="2023-10-17", application="2026-01-01", jalons=[("2026-01-01", "Application")],
         cible="PSAN / CASP",
         objectif="Étendre l'échange automatique d'informations fiscales aux crypto-actifs.",
         obligation="Collecte et déclaration des informations sur les utilisateurs et leurs transactions "
                    "(diligence fiscale des clients).",
         contrainte="Sanctions nationales en cas de défaut de déclaration.",
         lien=_eli("dir", 2023, 2226)),
    # ------------------------------------------------------------------ International (GAFI)
    dict(id="fatf-r24", nom="GAFI — Recommandation 24 révisée (bénéficiaires effectifs)", theme="LCB-FT",
         juridiction="International (GAFI)", type="Recommandation", reference="Recommandation 24 du GAFI, révision de mars 2022",
         adoption="2022-03-04", application="2022-03-04", jalons=[],
         cible="Juridictions, registres BE ; impacts pour tous les assujettis",
         objectif="Renforcer la transparence des personnes morales et l'accès aux bénéficiaires effectifs.",
         obligation="Approche multiple (registre, informations détenues par les sociétés et les assujettis), "
                    "informations adéquates, exactes et à jour.",
         contrainte="Évaluée dans le cycle d'évaluations mutuelles en cours.",
         lien=FATF_RECS),
    dict(id="fatf-r16", nom="GAFI — Recommandation 16 révisée (transparence des paiements)", theme="Paiements",
         juridiction="International (GAFI)", type="Recommandation", reference="Recommandation 16 du GAFI, révision de juin 2025",
         adoption="2025-06-18", application="2030-12-31",
         jalons=[("2030-12-31", "Mise en œuvre attendue d'ici fin 2030")],
         cible="Banques, PSP, PSAN",
         objectif="Moderniser les règles de transparence des virements (« travel rule ») et clarifier les "
                  "responsabilités le long de la chaîne de paiement.",
         obligation="Données enrichies sur le donneur d'ordre et le bénéficiaire, vérification de concordance "
                    "nom / compte.",
         contrainte="Transposition attendue dans les législations nationales et européennes.",
         lien=FATF_RECS),
]


# --------------------------------------------------------------------------- #
# Résumés : ce que dit chaque texte (partie « L'essentiel » de la fiche)
# --------------------------------------------------------------------------- #
RESUMES = {
    "amlr": "L'AMLR fixe directement, pour toutes les entités assujetties de l'UE, les règles de vigilance à "
            "l'égard de la clientèle, de transparence des bénéficiaires effectifs et de déclaration des opérations "
            "suspectes, jusque-là réparties entre la directive et les lois nationales. Il élargit le champ des "
            "assujettis (prestataires sur crypto-actifs, plateformes de financement participatif, négociants en "
            "biens de grande valeur, clubs et agents de football professionnels). Les informations à recueillir "
            "sur les clients sont harmonisées et la mise à jour des dossiers est rythmée par le risque, au moins "
            "une fois par an pour les clients à risque élevé et au moins tous les cinq ans pour les autres. "
            "Le bénéficiaire effectif s'apprécie par la détention d'au moins 25 % ou par le contrôle exercé "
            "par d'autres moyens. Le texte encadre la vigilance simplifiée et renforcée, notamment vis-à-vis des "
            "pays tiers à haut risque, interdit les comptes anonymes et plafonne les paiements en espèces à 10 000 €.",
    "amld6": "L'AMLD6 regroupe les règles que chaque État membre doit organiser. Elle impose des registres "
             "centraux des bénéficiaires effectifs interconnectés au niveau européen, accessibles aux assujettis "
             "et aux personnes justifiant d'un intérêt légitime, avec signalement des divergences. Elle prévoit "
             "des registres de comptes bancaires interconnectés et un accès des autorités aux informations "
             "immobilières. Elle renforce les cellules de renseignement financier comme TRACFIN (suspension "
             "d'opérations, accès à l'information, analyses conjointes) et fixe une méthodologie commune de "
             "supervision fondée sur les risques. Elle harmonise enfin les mesures administratives et les "
             "sanctions applicables aux assujettis.",
    "amlar": "Le règlement crée l'AMLA, autorité européenne de lutte contre le blanchiment installée à Francfort. "
             "Elle supervisera directement jusqu'à 40 groupes financiers transfrontaliers à haut risque, "
             "sélectionnés selon des critères de risque et de présence dans plusieurs États membres. Elle "
             "coordonne les superviseurs nationaux du secteur financier et non financier, élabore les normes "
             "techniques et orientations qui précisent l'AMLR, et soutient la coopération entre cellules de "
             "renseignement financier. Elle dispose de pouvoirs d'enquête et de sanction envers les entités "
             "qu'elle supervise directement.",
    "arrete-2021": "L'arrêté précise l'organisation attendue du dispositif LCB-FT et de gel des avoirs des "
                   "organismes financiers. Il impose une classification des risques documentée et mise à jour, "
                   "tenant compte des travaux du GAFI, de l'OCDE et de l'UE, des procédures écrites et des outils "
                   "de détection et d'analyse des opérations atypiques. Il encadre le recours à des prestataires "
                   "externes et exige un contrôle interne permanent et périodique adapté à la taille et à "
                   "l'activité. Pour le gel des avoirs, il demande un dispositif de détection des personnes "
                   "désignées et des opérations visant à contourner les mesures. Il organise enfin la "
                   "responsabilité de l'entreprise mère sur le dispositif de groupe.",
    "eba-gl-2022-05": "Les orientations précisent le rôle de l'organe de direction, qui doit désigner l'un de ses "
                      "membres comme responsable de la conformité aux obligations LCB-FT. Elles détaillent les "
                      "missions, le positionnement hiérarchique, l'indépendance et les moyens du responsable de la "
                      "conformité LCB-FT, ainsi que son accès à l'information. Ce dernier rend compte au moins "
                      "une fois par an à l'organe de direction dans un rapport d'activité. Les orientations "
                      "encadrent également l'organisation de la fonction au sein des groupes et l'externalisation "
                      "de tâches opérationnelles.",
    "eba-gl-2022-15": "Les orientations décrivent comment identifier et vérifier un client à distance. "
                      "L'établissement doit adopter une politique et des procédures dédiées, définir les données "
                      "à collecter et vérifier l'authenticité des documents et la correspondance avec la personne, "
                      "par exemple au moyen de la biométrie ou de la vidéo. La solution technique doit être évaluée "
                      "avant son déploiement puis testée et suivie régulièrement. En cas de recours à un tiers ou "
                      "à un prestataire, l'établissement reste responsable du respect de ses obligations.",
    "eba-gl-2024-01": "Ces orientations étendent les orientations sur les facteurs de risque BC-FT aux prestataires "
                      "de services sur crypto-actifs. Elles décrivent les facteurs de risque propres à ce secteur : "
                      "anonymat, transactions avec des adresses auto-hébergées, exposition à des mixeurs ou à des "
                      "plateformes non régulées, produits renforçant la confidentialité. Elles détaillent les "
                      "mesures de vigilance attendues, dont l'utilisation d'outils d'analyse de la blockchain, et "
                      "précisent ce qui est attendu des banques qui entretiennent des relations avec des CASP.",
    "dual-use": "Le règlement refond le régime européen de contrôle des exportations, du courtage, de l'assistance "
                "technique, du transit et des transferts de biens à double usage. Il introduit des contrôles sur "
                "certains outils de cybersurveillance au regard des droits de l'homme et crée de nouvelles "
                "autorisations générales européennes. Les exportateurs recourant à des licences globales doivent "
                "disposer d'un programme interne de conformité. Le texte renforce aussi la coopération et "
                "l'échange d'informations entre les États membres et la Commission.",
    "dir-2024-1226": "La directive harmonise les infractions pénales de violation des mesures restrictives de l'UE : "
                     "mise à disposition de fonds ou de ressources économiques à une personne désignée, non-gel "
                     "des avoirs, transactions et services interdits, et contournement des sanctions, notamment "
                     "par la dissimulation de la propriété réelle des fonds. Elle fixe des peines d'emprisonnement "
                     "minimales pour les personnes physiques et des amendes pour les personnes morales, calculées "
                     "en pourcentage du chiffre d'affaires mondial ou en montant fixe. Elle prévoit des "
                     "circonstances aggravantes, la confiscation des produits et la coopération entre autorités.",
    "eba-gl-2024-14": "Deux jeux d'orientations s'appliquent depuis le 30 décembre 2025. Le premier vise tous les "
                      "établissements supervisés par l'EBA : gouvernance, évaluation de l'exposition aux sanctions "
                      "et dispositif de gestion des risques liés aux mesures restrictives, sous la responsabilité "
                      "de l'organe de direction et d'un responsable désigné. Le second vise les PSP et les CASP : "
                      "politiques et procédures pour appliquer les mesures restrictives lors des transferts de "
                      "fonds et de crypto-actifs. Ils exigent le filtrage des clients et des transactions, une "
                      "gestion documentée des alertes, ainsi qu'un choix, un paramétrage et des tests justifiés "
                      "des outils de filtrage.",
    "dir-2024-1260": "La directive renforce le dépistage, le gel, la confiscation et la gestion des avoirs d'origine "
                     "criminelle. Les États doivent pouvoir lancer rapidement des enquêtes patrimoniales, geler "
                     "les biens et confisquer les instruments et produits d'infractions, y compris en valeur "
                     "équivalente ou auprès de tiers qui savaient que le transfert visait à éviter la confiscation. "
                     "Elle permet la confiscation sans condamnation dans certains cas (maladie, fuite, décès) et "
                     "celle des avoirs inexpliqués liés à la criminalité organisée. Elle renforce les bureaux de "
                     "recouvrement et de gestion des avoirs et impose une stratégie nationale d'ici mai 2027.",
    "tfr": "Le TFR refond le règlement 2015/847 : chaque transfert de fonds doit être accompagné d'informations "
           "sur le donneur d'ordre et le bénéficiaire, et ces règles s'appliquent désormais aux transferts de "
           "crypto-actifs entre prestataires. Pour les crypto-actifs, aucun seuil ne s'applique. Pour les "
           "transferts de plus de 1 000 € avec une adresse auto-hébergée, le prestataire doit vérifier que "
           "l'adresse appartient à son client. Les prestataires intermédiaires et bénéficiaires doivent détecter "
           "les informations manquantes et décider, selon le risque, de rejeter, suspendre ou exécuter le "
           "transfert, et signaler les prestataires défaillants de manière répétée.",
    "eba-gl-2024-11": "Ces orientations précisent les procédures que les PSP, les intermédiaires et les CASP doivent "
                      "mettre en place pour appliquer le TFR. Elles détaillent les informations à transmettre, "
                      "la détection des informations manquantes ou incohérentes, et le traitement des transferts "
                      "incomplets : rejet, suspension ou demande d'informations complémentaires. Elles abordent "
                      "les transferts avec des adresses auto-hébergées, l'interopérabilité des protocoles "
                      "d'échange et le suivi des contreparties défaillantes de manière répétée.",
    "mica": "MiCA crée un régime européen harmonisé pour l'offre au public de crypto-actifs, pour les jetons se "
            "référant à des actifs (ART) et les jetons de monnaie électronique (EMT), ainsi que pour les "
            "prestataires de services sur crypto-actifs. Les CASP doivent être agréés et respecter des exigences "
            "de gouvernance, de fonds propres, de conservation des actifs des clients, de traitement des "
            "réclamations et de gestion des conflits d'intérêts. L'agrément vaut dans toute l'UE grâce au "
            "passeport. Le règlement interdit aussi les abus de marché sur crypto-actifs et prévoit une période "
            "transitoire pour les prestataires déjà en activité.",
    "ord-2024-936": "L'ordonnance adapte le code monétaire et financier à MiCA. Elle répartit les compétences entre "
                    "l'AMF et l'ACPR, organise l'articulation avec le régime national des PSAN et la période "
                    "transitoire, et adapte les pouvoirs de contrôle et de sanction. Le régime PSAN prend fin le "
                    "1er juillet 2026 : les prestataires doivent désormais disposer de l'agrément MiCA pour "
                    "exercer.",
    "ord-2024-937": "L'ordonnance transpose les modifications apportées à la directive LCB-FT par le TFR. Les "
                    "prestataires de services sur crypto-actifs sont pleinement soumis aux obligations LCB-FT du "
                    "code monétaire et financier. Le texte prévoit des mesures de vigilance renforcée pour les "
                    "relations de correspondance avec des prestataires de pays tiers et une attention particulière "
                    "aux transferts impliquant des adresses auto-hébergées.",
    "ipr": "Le règlement modifie le règlement SEPA. Tous les PSP qui proposent des virements en euros doivent offrir "
           "le virement instantané, disponible en permanence, exécuté en dix secondes et facturé au plus au prix "
           "d'un virement classique. Avant chaque virement, le PSP doit proposer gratuitement un service de "
           "vérification du bénéficiaire, qui compare le nom et l'IBAN. Pour les sanctions, le filtrage "
           "transaction par transaction est remplacé par une vérification, au moins quotidienne, de l'ensemble "
           "de la clientèle contre les listes de personnes et d'entités désignées par l'UE.",
    "psr-psd3": "La réforme remplace la DSP2 par un règlement d'application directe (PSR), qui fixe les droits et "
                "obligations dans l'exécution des paiements, et une directive (PSD3), consacrée à l'agrément et "
                "à la supervision des établissements de paiement, qui intègre le régime de la monnaie "
                "électronique. Elle étend la vérification nom / IBAN à tous les virements, organise le partage "
                "d'informations sur la fraude entre PSP et renforce l'authentification forte et l'accès aux "
                "comptes. Elle crée un droit au remboursement des victimes de fraude par usurpation de l'identité "
                "de leur PSP et peut engager la responsabilité des plateformes en ligne qui n'ont pas retiré un "
                "contenu frauduleux signalé.",
    "ccd2": "La directive remplace la directive de 2008 sur le crédit à la consommation. Elle étend la protection "
            "aux crédits de moins de 200 €, aux crédits sans frais et aux formules de paiement fractionné "
            "(« buy now, pay later »). L'évaluation de la solvabilité devient plus exigeante et doit reposer sur "
            "des informations pertinentes et exactes. Le texte encadre la publicité, les ventes liées et les "
            "décisions automatisées, et impose aux États de prévenir les taux ou coûts du crédit excessifs.",
    "dora": "DORA impose aux entités financières un cadre complet de gestion du risque lié aux technologies de "
            "l'information et de la communication, placé sous la responsabilité de l'organe de direction. Il "
            "harmonise la classification et la notification des incidents TIC majeurs, et exige des tests "
            "réguliers de résilience, dont des tests de pénétration fondés sur la menace pour les entités les "
            "plus importantes. Les relations avec les prestataires TIC sont encadrées par des clauses "
            "contractuelles obligatoires et un registre d'information. Les prestataires TIC critiques sont "
            "désignés et supervisés au niveau européen.",
    "ai-act": "L'AI Act classe les systèmes d'intelligence artificielle selon leur niveau de risque. Il interdit "
              "certaines pratiques, comme la notation sociale ou la manipulation. Il soumet les systèmes à haut "
              "risque, dont l'évaluation de la solvabilité des personnes et la tarification en assurance vie et "
              "santé, à des exigences de gestion des risques, de qualité des données, de documentation, de "
              "transparence et de supervision humaine. Il prévoit des obligations spécifiques pour les modèles "
              "d'IA à usage général et des obligations de transparence pour certains systèmes, comme les agents "
              "conversationnels.",
    "crr3": "CRR3 transpose la finalisation des accords de Bâle III. Le texte révise l'approche standard et "
            "encadre les modèles internes pour le risque de crédit, introduit une nouvelle méthode unique pour "
            "le risque opérationnel et révise le risque de CVA. Il instaure un plancher de fonds propres "
            "(« output floor ») limitant l'avantage des modèles internes, introduit progressivement. Il prévoit "
            "aussi des exigences de publication renforcées, notamment sur les risques ESG.",
    "crd6": "CRD6 renforce le cadre prudentiel de gouvernance et de supervision des banques. Elle harmonise "
            "l'évaluation de l'aptitude et de l'honorabilité des dirigeants et des titulaires de fonctions clés, "
            "intègre les risques environnementaux, sociaux et de gouvernance dans la gestion des risques, et "
            "renforce les pouvoirs des superviseurs. Elle impose un agrément et un cadre minimal harmonisé aux "
            "succursales d'établissements de pays tiers qui exercent des activités bancaires dans l'UE.",
    "csrd": "La CSRD remplace la directive sur la publication d'informations non financières. Elle étend le "
            "reporting de durabilité à un nombre beaucoup plus large d'entreprises et l'organise selon des "
            "normes européennes (ESRS) fondées sur la double matérialité : impacts de l'entreprise sur "
            "l'environnement et la société, et effets des enjeux de durabilité sur l'entreprise. Les informations "
            "figurent dans le rapport de gestion et font l'objet d'une assurance par un tiers. Le calendrier a "
            "été en partie reporté par la directive « stop-the-clock » de 2025.",
    "dac8": "DAC8 étend la coopération administrative fiscale aux crypto-actifs. Les prestataires de services sur "
            "crypto-actifs doivent collecter des informations sur leurs utilisateurs (identité, résidence "
            "fiscale) et sur leurs transactions, puis les déclarer chaque année à l'administration fiscale. "
            "Celle-ci les échange automatiquement avec les autres États membres. Le texte s'inspire du cadre "
            "CARF de l'OCDE et renforce aussi certaines règles d'échange existantes.",
    "fatf-r24": "La révision de la Recommandation 24 renforce la transparence des personnes morales. Les pays "
                "doivent adopter une approche multiple combinant un registre des bénéficiaires effectifs ou un "
                "mécanisme équivalent, les informations détenues par les sociétés elles-mêmes et celles recueillies "
                "par les assujettis. Les autorités doivent pouvoir accéder rapidement à des informations "
                "adéquates, exactes et à jour. La révision vise aussi les actions au porteur et les "
                "prête-noms, et impose une évaluation des risques liés aux personnes morales.",
    "fatf-r16": "La révision de la Recommandation 16 modernise les règles de transparence des paiements. Elle "
                "clarifie la responsabilité de chaque acteur de la chaîne de paiement, en commençant par "
                "l'institution qui reçoit l'instruction du client. Les virements transfrontaliers de pair à pair "
                "de plus de 1 000 USD/EUR doivent comporter le nom, l'adresse et la date de naissance du donneur "
                "d'ordre. Les institutions sont invitées à utiliser des outils de vérification des coordonnées du "
                "bénéficiaire pour prévenir la fraude et les erreurs. Les paiements par carte pour l'achat de "
                "biens et de services restent exemptés des exigences complètes.",
}
