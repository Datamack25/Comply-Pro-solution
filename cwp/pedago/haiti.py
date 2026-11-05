"""
Base de connaissances « Haïti & Caraïbes — conformité » de CWP.

Statut de vérification de chaque élément : « vérifié » (texte primaire consulté), « source secondaire »
(presse ou synthèse), « à vérifier » (information signalée mais non confirmée). Mettre à jour `verifie_le`.
"""
from __future__ import annotations

VERIFIE_LE = "2026-11-04"

INSTITUTIONS = [
    dict(sigle="BRH", nom="Banque de la République d'Haïti", type="Banque centrale · superviseur",
         role="Autorité de supervision et de sanction des banques, maisons de transfert, bureaux de change et autres institutions "
              "financières agréées. Publie les circulaires LCB-FT et contrôle leur application.",
         textes=["Circulaire n° 99-2 aux banques (7 juin 2018, en vigueur le 2 juillet 2018) — mesures préventives LCB-FT",
                 "Circulaire n° 100-2 aux banques (7 juin 2018) — programme de prévention LCB-FT, officier de conformité",
                 "Loi du 14 mai 2012 sur les banques et autres institutions financières (art. 109 : sanctions)",
                 "Circulaires 114-3 et 121 (sous-agents, bénéficiaires effectifs) citées par la BRH en 2025"],
         assujettis="Banques, maisons de transfert, bureaux de change, coopératives et institutions de microfinance selon leur statut.",
         a_retenir=["La BRH contrôle et sanctionne ; les déclarations de soupçon vont à l'UCREF.",
                    "Juillet 2025 : après les désignations de groupes armés (ONU, États-Unis), la BRH a demandé une surveillance renforcée, "
                    "la détection d'intermédiaires, une diligence renforcée sur les PPE et la déclaration sans délai à l'UCREF.",
                    "Sanctions de la circulaire 99-2 : de l'avertissement au retrait d'agrément, amende de 500 000 HTG par violation, "
                    "300 000 HTG par jour de non-redressement (30 jours au plus)."],
         statut="vérifié (circulaires 99-2 et 100-2 consultées sur brh.ht) / source secondaire (communication de juillet 2025)"),
    dict(sigle="UCREF", nom="Unité centrale de renseignements financiers", type="Cellule de renseignement financier (CRF)",
         role="Reçoit et analyse les déclarations de soupçon des institutions financières et des professions assujetties, "
              "transmet les dossiers aux autorités judiciaires, coopère avec les CRF étrangères. Ses rapports d'enquête sur des "
              "personnalités sont régulièrement relayés par la presse haïtienne.",
         textes=["Loi du 11 novembre 2013 sanctionnant le blanchiment de capitaux et le financement du terrorisme (art. 20 : déclaration "
                 "de soupçon ou rapport confidentiel interne ; art. 59 : sanctions)", "Loi de 2016 modifiant le dispositif (citée par la circulaire 99-2)"],
         assujettis="Institutions financières et entreprises et professions non financières désignées.",
         a_retenir=["Déclaration de soupçon à l'UCREF ; information de l'UCREF si un bénéficiaire effectif ne peut être identifié (circ. 99-2, 3.1).",
                    "Interdiction d'informer le client de la déclaration."],
         statut="vérifié (références de la circulaire 99-2) / à compléter avec le texte de la loi"),
    dict(sigle="ULCC", nom="Unité de lutte contre la corruption", type="Agence anticorruption",
         role="Prévention et investigation de la corruption dans l'administration publique ; reçoit et contrôle les déclarations de "
              "patrimoine des agents publics ; publie des rapports d'enquête transmis à la justice.",
         textes=["Décret de 2004 portant création de l'ULCC", "Loi portant prévention et répression de la corruption (2014)"],
         assujettis="Agents publics et élus (déclaration de patrimoine).",
         a_retenir=["Les rapports de l'ULCC sont une source d'information négative sur les PPE haïtiennes.",
                    "Un rapport ULCC n'est pas une condamnation : vérifier la suite judiciaire."],
         statut="source secondaire (décret 2004 et presse) — vérifier la loi de 2014"),
    dict(sigle="BAFE", nom="Bureau des affaires financières et économiques (Police nationale d'Haïti)", type="Police judiciaire financière",
         role="Unité de la PNH chargée des enquêtes sur la criminalité financière et économique (blanchiment, fraude, corruption), "
              "en lien avec l'UCREF et le parquet.",
         textes=["Organisation de la Police nationale d'Haïti"],
         assujettis="—", a_retenir=["Destinataire des enquêtes pénales ; pas de déclaration directe par les banques (passer par l'UCREF)."],
         statut="à vérifier (texte d'organisation non consulté)"),
    dict(sigle="GAFIC / CFATF", nom="Groupe d'action financière des Caraïbes", type="Organisme régional de type GAFI",
         role="Évalue les dispositifs LCB-FT des pays de la Caraïbe ; Haïti a été évalué en 2019 (4e cycle) et fait l'objet de "
              "rapports de suivi renforcé.",
         textes=["Rapport d'évaluation mutuelle d'Haïti (2019)", "Rapports de suivi renforcé et réévaluations de conformité technique"],
         assujettis="—", a_retenir=["Haïti est sur la liste grise du GAFI depuis juin 2021 (maintenue en 2026)."],
         statut="vérifié (publications GAFI / GAFIC)"),
]

SEUILS = [
    dict(texte="Circulaire BRH n° 99-2 (2018), section 2.1", seuil="600 000 HTG (ou équivalent en devises)",
         obligation="Identification du client pour les transactions importantes en espèces ; agrégation des opérations multiples.",
         statut="vérifié"),
    dict(texte="Circulaire BRH n° 99-2 (2018), section 6", seuil="60 000 HTG (ou équivalent)",
         obligation="Identification du donneur d'ordre et du bénéficiaire des virements électroniques ; informations transmises tout au long de la chaîne.",
         statut="vérifié"),
    dict(texte="Information relayée (vidéo AyiboPost)", seuil="1 300 000 HTG",
         obligation="Information de la BRH par les banques au-delà de ce montant, sous peine de sanction.",
         statut="à vérifier — aucune circulaire confirmant ce seuil n'a été trouvée ; rechercher une circulaire postérieure à 2018 sur brh.ht"),
    dict(texte="Circulaire BRH n° 99-2 (2018), section 7", seuil="5 ans",
         obligation="Conservation des documents après la fin de la relation et après chaque transaction.", statut="vérifié"),
    dict(texte="Circulaire BRH n° 99-2 (2018), section 8", seuil="3 ans / 2 ans",
         obligation="Mise à jour de l'identification : au plus tous les 3 ans, au moins tous les 2 ans pour les clients à risque élevé.",
         statut="vérifié"),
    dict(texte="Circulaire BRH n° 99-2 (2018), section 2.2", seuil="5 jours ouvrables",
         obligation="Envoi des documents pour les comptes ouverts à distance (courrier recommandé avec accusé de réception).", statut="vérifié"),
]

CONTEXTE = [
    ("Une économie majoritairement informelle", [
        "Plus de 70 % de l'activité relèverait encore de l'informel (Bernardin, 2023, cité dans un rapport de la BRH, repris par Le Quotidien 509, avril 2025).",
        "Selon FinScope MSME Haïti 2021 (BRH) : seulement 11 % des micro, petites et moyennes entreprises sont enregistrées, 30 % sont totalement exclues du système financier et 99 % fonctionnent uniquement en espèces.",
        "Conséquence pour la conformité : revenus difficiles à justifier, origine des fonds rarement documentée, profils transactionnels peu fiables, forte part d'espèces dans les dépôts."]),
    ("Le poids des transferts de la diaspora", [
        "Les transferts privés reçus ont atteint environ 3,63 milliards de dollars sur l'exercice clos le 30 septembre 2024 (+10,7 %), selon la note de politique monétaire citée par Le Nouvelliste (janvier 2025).",
        "Ils représentent de l'ordre de 20 % du PIB selon la presse haïtienne (IciHaïti).",
        "Conséquence : corridors États-Unis / Canada / France / République dominicaine → Haïti à fort volume et à faible montant unitaire ; risque de fractionnement, de mules et de paiement de rançons noyés dans des flux familiaux légitimes."]),
    ("Instabilité politique, insécurité et crise économique", [
        "Sept années consécutives de contraction économique jusqu'en 2025 (PIB réel −2,7 % en 2025), inflation moyenne de 28,3 % en 2025, recettes publiques à 4,8 % du PIB (Banque mondiale).",
        "Plus de 5 500 personnes tuées par la violence en 2025 (HCDH, cité par la Banque mondiale) et 1,4 million de déplacés en mars 2026.",
        "Régime de sanctions de l'ONU (résolution 2653 de 2022, renouvelé) ; désignation par les États-Unis de coalitions de gangs comme organisations terroristes étrangères en 2025.",
        "Conséquences : territoires contrôlés par des groupes armés (extorsion, rançons, taxation des routes), institutions judiciaires affaiblies, difficulté d'obtenir des pièces officielles, risque élevé de soutien matériel indirect à des organisations désignées."]),
    ("Faiblesses structurelles du dispositif", [
        "Liste grise du GAFI depuis juin 2021 : déficiences stratégiques relevées lors de l'évaluation mutuelle de 2019.",
        "Identification : documents d'identité et adresses difficiles à vérifier, absence de registre public fiable des bénéficiaires effectifs.",
        "Économie fortement dollarisée et marché des changes informel.",
        "Risque de réduction des relations de correspondance bancaire (de-risking) par les banques étrangères, qui pousse les flux vers des canaux informels."]),
    ("Ce que cela implique pour l'analyste", [
        "Adapter les justificatifs d'origine des fonds (attestations, relevés de transferts, preuves d'activité informelle) plutôt que refuser par principe.",
        "Surveiller les corridors à risque (zones contrôlées par des gangs), les bénéficiaires communs à plusieurs émetteurs et les hausses soudaines de transferts.",
        "Filtrer systématiquement les régimes ONU 2653, OFAC (FTO / SDGT, programme Haïti) et Canada ; examiner la propriété et le contrôle des sous-agents.",
        "Consigner dans CWP les informations locales (rapports ULCC, communiqués UCREF, décisions de justice) via le formulaire « Renseignements internes »."]),
]

CARAIBES = [
    ("Panorama régional", [
        "Le GAFIC regroupe les juridictions de la Caraïbe et d'Amérique centrale ; plusieurs sont ou ont été sur la liste grise (Haïti, Îles Vierges britanniques, Venezuela et Bolivie dans la liste d'octobre 2026 retenue par CWP).",
        "Centres financiers offshore (Îles Vierges britanniques, Îles Caïmans, Bahamas, Panama…) : sociétés écrans et trusts, enjeu de transparence des bénéficiaires effectifs.",
        "Programmes de citoyenneté par investissement de plusieurs États insulaires : risque d'usage par des personnes cherchant à échapper à des sanctions ou à des poursuites.",
        "Économies dépendantes du tourisme, de l'immobilier et des transferts : forte part d'espèces et d'immobilier comme vecteurs de blanchiment.",
        "Routes du trafic de drogue et d'armes entre l'Amérique du Sud, la Caraïbe et l'Amérique du Nord."]),
    ("Corridors à surveiller (Europe – Afrique – Caraïbes)", [
        "France / DOM – Haïti : transferts familiaux, agents de maisons de transfert, espèces.",
        "États-Unis – Haïti / République dominicaine : armes (embargo ONU), paiements de rançons, fret maritime.",
        "Venezuela – Caraïbe : contournement des sanctions américaines (or, pétrole), licences générales mal interprétées.",
        "Nicaragua : secteur aurifère désigné par l'OFAC en 2026."]),
]

VEILLE_QUERIES = {
    "UCREF & BRH": ['UCREF Haïti', '"Banque de la République d\'Haïti" circulaire', 'BRH blanchiment banques Haïti'],
    "ULCC & corruption": ['ULCC Haïti rapport', 'corruption Haïti enquête'],
    "Sanctions & gangs": ['Haïti sanctions gangs OFAC', 'Haiti sanctions UN 2653', 'Viv Ansanm sanctions'],
    "GAFIC / CFATF": ['CFATF GAFIC Caraïbes', 'CFATF plenary Caribbean grey list'],
    "Médias haïtiens": ['site:ayibopost.com blanchiment OR corruption OR BRH', 'site:lenouvelliste.com UCREF OR blanchiment OR BRH',
                        'site:haitilibre.com UCREF OR BRH OR blanchiment'],
}

CATEGORIES_RENSEIGNEMENT = ["Rapport ULCC", "Communiqué / rapport UCREF", "Décision judiciaire locale", "Information BRH",
                            "Presse locale", "Renseignement terrain", "Liste locale (gel, interdiction)", "Autre"]
FIABILITE = ["A — source totalement fiable", "B — habituellement fiable", "C — assez fiable", "D — pas toujours fiable",
             "E — peu fiable", "F — fiabilité non évaluable"]
CREDIBILITE = ["1 — confirmé par d'autres sources", "2 — probablement vrai", "3 — possiblement vrai", "4 — douteux",
               "5 — improbable", "6 — non évaluable"]


def rapport_pdf() -> bytes:
    from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle
    from cwp.exports import common as X
    W = X.CONTENT_W
    s = X.styles()
    story = [X.header_card("Focus Caraïbes · rapport de contexte", "Haïti & Caraïbes : économie informelle, instabilité et conformité",
                           f"Dispositif LCB-FT, seuils, institutions, contraintes de terrain · état au {VERIFIE_LE}", W), Spacer(1, 10)]
    for titre, pts in CONTEXTE:
        story += [KeepTogether([X.section_title(titre, W), Spacer(1, 3)] + [Paragraph(f"• {X.esc(p)}", s["body"]) for p in pts]), Spacer(1, 8)]
    story += [X.section_title("Institutions du dispositif haïtien", W), Spacer(1, 4)]
    for i in INSTITUTIONS:
        story.append(KeepTogether([Paragraph(f"<b>{X.esc(i['sigle'])}</b> — {X.esc(i['nom'])} <font color='#7A7A7A'>({X.esc(i['type'])})</font>", s["body"]),
                                   Paragraph(X.esc(i["role"]), s["small"]),
                                   Paragraph("Textes : " + X.esc(" ; ".join(i["textes"])), s["small_grey"]),
                                   Paragraph("À retenir : " + X.esc(" ".join(i["a_retenir"])), s["small"]),
                                   Paragraph("Statut : " + X.esc(i["statut"]), s["small_grey"]), Spacer(1, 6)]))
    data = [[Paragraph(h, s["label"]) for h in ("TEXTE", "SEUIL", "OBLIGATION", "STATUT")]] + [
        [Paragraph(X.esc(x["texte"]), s["small"]), Paragraph(X.esc(x["seuil"]), s["small"]), Paragraph(X.esc(x["obligation"]), s["small"]),
         Paragraph(X.esc(x["statut"]), s["small_grey"])] for x in SEUILS]
    t = Table(data, colWidths=[W * 0.22, W * 0.16, W * 0.4, W * 0.22], repeatRows=1)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1.1, X.GOLD), ("LINEBELOW", (0, 1), (-1, -1), 0.25, X.LINE), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [Spacer(1, 6), X.section_title("Seuils et délais", W), Spacer(1, 4), t, Spacer(1, 10)]
    for titre, pts in CARAIBES:
        story += [KeepTogether([X.section_title(titre, W), Spacer(1, 3)] + [Paragraph(f"• {X.esc(p)}", s["body"]) for p in pts]), Spacer(1, 8)]
    story += [Paragraph("Sources : BRH (circulaires 99-2 et 100-2), GAFI / GAFIC, Banque mondiale, HaitiLibre, Le Nouvelliste, "
                        "Le Quotidien 509, IciHaïti. Les éléments « à vérifier » doivent être confirmés sur les textes officiels.", s["small_grey"]),
              Spacer(1, 8), X.footer_line("Rapport Haïti & Caraïbes", W)]
    return X.build_pdf(story, title="CWP – Haïti & Caraïbes")
