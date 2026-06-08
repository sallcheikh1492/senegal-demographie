# -*- coding: utf-8 -*-
"""Pipeline complet reproductible : données -> notebooks -> site."""
import os, subprocess, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PY = sys.executable
def run(cmd, cwd=BASE):
    print("\n$", " ".join(cmd)); subprocess.run(cmd, cwd=cwd, check=True)
run([PY, os.path.join("scripts", "download_data.py")])
run([PY, os.path.join("scripts", "_build_notebooks.py")])
for nb in ["01_acquisition_preparation", "02_analyse_exploratoire", "03_tendances_projection"]:
    run([PY, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
         "--ExecutePreprocessor.timeout=600", nb + ".ipynb"], cwd=os.path.join(BASE, "notebooks"))
run([PY, os.path.join("scripts", "build_site.py")])
run([PY, os.path.join("scripts", "build_powerbi.py")])
print("\n✅ Pipeline terminé.")
