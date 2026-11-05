"""Enrichissement en ligne de commande (pour une tâche planifiée ou GitHub Actions).

    python scripts/enrichir.py            # 5 listes de sanctions + risque pays
    python scripts/enrichir.py ofac ue    # seulement certaines sources
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cwp.data import sources  # noqa: E402

JOBS = {"ofac": sources.enrichir_ofac, "ue": sources.enrichir_ue, "onu": sources.enrichir_onu,
        "uk": sources.enrichir_uk, "fr": sources.enrichir_gels_fr, "pays": sources.enrichir_pays}

if __name__ == "__main__":
    todo = sys.argv[1:] or list(JOBS)
    ko = 0
    for k in todo:
        try:
            print(k, JOBS[k]())
        except Exception as e:  # une source en panne n'arrête pas les autres
            ko += 1
            print(k, "ÉCHEC :", e)
    sys.exit(1 if ko == len(todo) else 0)
