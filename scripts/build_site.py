# -*- coding: utf-8 -*-
"""Construit le site web statique (docs/) : copie les figures + exporte data.js."""
import os, json, shutil
import pandas as pd, numpy as np
from sklearn.linear_model import LinearRegression

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(BASE, "docs"); ASSETS = os.path.join(DOCS, "assets")
FIG = os.path.join(BASE, "reports", "figures"); PROC = os.path.join(BASE, "data", "processed")
os.makedirs(ASSETS, exist_ok=True)
for f in os.listdir(FIG):
    if f.endswith(".png"): shutil.copy2(os.path.join(FIG, f), os.path.join(ASSETS, f))

nat = pd.read_csv(os.path.join(PROC, "dhs_national_wide.csv"))
subw = pd.read_csv(os.path.join(PROC, "dhs_subnational_wide.csv"))
wb = pd.read_csv(os.path.join(PROC, "worldbank_wide.csv"))

def pts(df, col, xcol="annee"):
    g = df.dropna(subset=[col]).sort_values(xcol)
    return [int(x) for x in g[xcol]], [round(float(v), 1) for v in g[col]]

tfr_x, tfr_y = pts(nat, "FE_FRTR_W_TFR")
u5_x, u5_y = pts(nat, "CM_ECMR_C_U5M")
im_x, im_y = pts(nat, "CM_ECMR_C_IMR")
pov_x, pov_y = pts(wb, "SI.POV.NAHC")
# régional trié par fécondité
sr = subw.dropna(subset=["FE_FRTR_W_TFR"]).sort_values("FE_FRTR_W_TFR")
# projection population
p = wb.dropna(subset=["SP.POP.TOTL"]).sort_values("annee")
an0 = int(p["annee"].iloc[-1]); pop0 = float(p["SP.POP.TOTL"].iloc[-1])
g = wb.dropna(subset=["SP.POP.GROW"])["SP.POP.GROW"].iloc[-5:].mean()/100
proj_x = list(range(an0, 2036)); proj_y = [round(pop0*(1+g)**(y-an0)/1e6, 1) for y in proj_x]
pop_x = [int(x) for x in p["annee"]]; pop_y = [round(float(v)/1e6, 1) for v in p["SP.POP.TOTL"]]
# corr & projection TFR
s = subw.dropna(subset=["ED_LITR_W_LIT", "FE_FRTR_W_TFR"])
corr = round(float(s["ED_LITR_W_LIT"].corr(s["FE_FRTR_W_TFR"])), 2)
t = nat.dropna(subset=["FE_FRTR_W_TFR"]); t = t[t["annee"] >= 1997]
lr = LinearRegression().fit(t[["annee"]], t["FE_FRTR_W_TFR"])
seuil = int(round((2.1 - lr.intercept_)/lr.coef_[0]))

data = {
  "tfr_x": tfr_x, "tfr_y": tfr_y, "u5_x": u5_x, "u5_y": u5_y, "im_x": im_x, "im_y": im_y,
  "pov_x": pov_x, "pov_y": pov_y,
  "reg_labels": sr["region"].tolist(),
  "reg_tfr": [round(float(v),1) for v in sr["FE_FRTR_W_TFR"]],
  "reg_elec": [None if pd.isna(v) else round(float(v)) for v in sr["HC_ELEC_H_ELC"]],
  "reg_lit": [None if pd.isna(v) else round(float(v)) for v in sr["ED_LITR_W_LIT"]],
  "pop_x": pop_x, "pop_y": pop_y, "proj_x": proj_x, "proj_y": proj_y,
  "kpi": {
    "tfr_now": tfr_y[-1], "tfr_first": tfr_y[0],
    "u5_first": u5_y[0], "u5_now": u5_y[-1],
    "pov_now": pov_y[-1], "young": round(float(wb.dropna(subset=["SP.POP.0014.TO.ZS"])["SP.POP.0014.TO.ZS"].iloc[-1])),
    "pop_now": pop_y[-1], "pop_2035": proj_y[-1], "corr": corr, "seuil": seuil,
  },
}
with open(os.path.join(DOCS, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.PROJECT_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
print("Site OK :", len(os.listdir(ASSETS)), "figures |", data["kpi"])
