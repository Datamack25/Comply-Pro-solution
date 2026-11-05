"""Textes français de référence. Les liens de recherche Légifrance sont à valider ; ajoutez vos textes ici."""
from urllib.parse import quote_plus

def lf(q):
    return "https://www.legifrance.gouv.fr/search/all?tab_selection=all&searchField=ALL&query=" + quote_plus(q)

LEGAL = [
 ("Loi Sapin II", "Loi n° 2016-1691 du 9 décembre 2016", "Transparence, lutte contre la corruption, modernisation de la vie économique : programme de conformité (art. 17), lanceurs d'alerte, AFA.", "https://www.legifrance.gouv.fr/loda/id/JORFTEXT000033558528"),
 ("Loi Sapin I", "Loi n° 93-122 du 29 janvier 1993", "Prévention de la corruption et transparence de la vie économique et des procédures publiques.", lf("loi 93-122 du 29 janvier 1993")),
 ("Loi du 13 novembre 2014 (à confirmer)", "Loi n° 2014-1353 du 13 novembre 2014", "Renforcement de la lutte contre le terrorisme. À confirmer : vous avez écrit « 3 novembre », vérifiez le texte visé.", lf("loi 2014-1353 du 13 novembre 2014")),
 ("Loi Waserman", "Loi n° 2022-401 du 21 mars 2022", "Amélioration de la protection des lanceurs d'alerte.", lf("loi 2022-401 du 21 mars 2022")),
 ("Loi sur le devoir de vigilance", "Loi n° 2017-399 du 27 mars 2017", "Devoir de vigilance des sociétés mères et entreprises donneuses d'ordre.", lf("loi 2017-399 du 27 mars 2017")),
 ("Code monétaire et financier — LCB-FT", "Art. L561-1 et suivants", "Obligations de vigilance, déclaration à TRACFIN, gel des avoirs (L562-1 et s.).", lf("code monétaire et financier L561-1")),
 ("Ordonnance LCB-FT", "Ordonnance n° 2020-115 du 12 février 2020", "Renforcement du dispositif LCB-FT (transposition 5e directive).", lf("ordonnance 2020-115 du 12 février 2020")),
]
