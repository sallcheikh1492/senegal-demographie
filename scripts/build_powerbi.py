# -*- coding: utf-8 -*-
"""
build_powerbi.py — Prépare des tables prêtes pour Power BI (modèle en étoile).

Produit dans powerbi/data/ :
  dim_indicateur.csv  : code, indicateur, source, categorie, sens_positif
  dim_region.csv      : region, region_geo, region_map, latitude, longitude
  dim_annee.csv       : annee, decennie
  faits_national.csv  : annee, code, valeur, source        (EDS + Banque mondiale)
  faits_regional.csv  : region_geo, code, valeur            (EDS 2023, 14 régions)
Le format long + dim_indicateur permet un slicer « indicateur » très flexible.
"""
import os, json
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
GEO = os.path.join(BASE, "data", "geo", "senegal_regions.geojson")
OUT = os.path.join(BASE, "powerbi", "data")
os.makedirs(OUT, exist_ok=True)

dhs_nat = pd.read_csv(os.path.join(PROC, "dhs_national.csv"))
dhs_sub = pd.read_csv(os.path.join(PROC, "dhs_subnational.csv"))
wb = pd.read_csv(os.path.join(PROC, "worldbank.csv"))

# --- Catégorisation des indicateurs ---
CAT = {
    "FE_FRTR_W_TFR": ("Démographie", False), "CM_ECMR_C_U5M": ("Santé", False),
    "CM_ECMR_C_IMR": ("Santé", False), "CM_ECMR_C_NNR": ("Santé", False),
    "FP_CUSM_W_MOD": ("Santé", True), "RH_DELP_C_DHF": ("Santé", True),
    "CN_NUTS_C_HA2": ("Santé", False), "ED_LITR_W_LIT": ("Éducation", True),
    "WS_SRCE_H_IMP": ("Conditions de vie", True), "HC_ELEC_H_ELC": ("Conditions de vie", True),
}
def wb_cat(code):
    if code.startswith("SI.POV"): return ("Pauvreté", False)
    if code in ("SH.DYN.MORT",): return ("Santé", False)
    return ("Démographie", True)

# --- dim_indicateur (union EDS + Banque mondiale) ---
di_dhs = dhs_nat[["code", "indicateur"]].drop_duplicates().assign(source="EDS/DHS")
di_wb = wb[["code", "indicateur"]].drop_duplicates().assign(source="Banque mondiale")
dim_ind = pd.concat([di_dhs, di_wb], ignore_index=True).drop_duplicates("code")
dim_ind["categorie"] = dim_ind["code"].map(
    lambda c: CAT[c][0] if c in CAT else wb_cat(c)[0])
dim_ind["sens_positif"] = dim_ind["code"].map(
    lambda c: CAT[c][1] if c in CAT else wb_cat(c)[1])
dim_ind.to_csv(os.path.join(OUT, "dim_indicateur.csv"), index=False, encoding="utf-8-sig")

# --- faits_national (EDS + Banque mondiale) ---
fn = pd.concat([
    dhs_nat[["annee", "code", "valeur"]].assign(source="EDS/DHS"),
    wb[["annee", "code", "valeur"]].assign(source="Banque mondiale"),
], ignore_index=True)
fn.to_csv(os.path.join(OUT, "faits_national.csv"), index=False, encoding="utf-8-sig")

# --- faits_regional (EDS 2023) ---
dhs_sub[["region_geo", "code", "valeur"]].to_csv(
    os.path.join(OUT, "faits_regional.csv"), index=False, encoding="utf-8-sig")

# --- dim_annee ---
ans = sorted(set(fn["annee"].dropna().astype(int)))
dim_annee = pd.DataFrame({"annee": range(min(ans), max(ans) + 1)})
dim_annee["decennie"] = (dim_annee["annee"] // 10 * 10).astype(str) + "s"
dim_annee.to_csv(os.path.join(OUT, "dim_annee.csv"), index=False, encoding="utf-8-sig")

# --- dim_region avec centroïdes (pour la carte) ---
geo = json.load(open(GEO, encoding="utf-8"))
def rings(g): return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
rows = []
# noms accentués pour affichage
ACC = {"Saint Louis": "Saint-Louis", "Thies": "Thiès", "Kedougou": "Kédougou", "Sedhiou": "Sédhiou"}
for feat in geo["features"]:
    name = feat["properties"]["shapeName"]
    big, cx, cy = -1, None, None
    for poly in rings(feat["geometry"]):
        ext = np.array(poly[0])
        ar = abs(np.sum(ext[:, 0]*np.roll(ext[:, 1], 1) - np.roll(ext[:, 0], 1)*ext[:, 1]))/2
        if ar > big:
            big, cx, cy = ar, ext[:, 0].mean(), ext[:, 1].mean()
    rows.append({"region": ACC.get(name, name), "region_geo": name,
                 "region_map": f"{name}, Senegal",
                 "latitude": round(cy, 4), "longitude": round(cx, 4)})
pd.DataFrame(rows).to_csv(os.path.join(OUT, "dim_region.csv"), index=False, encoding="utf-8-sig")

print("Tables Power BI écrites dans powerbi/data/ :")
for f in sorted(os.listdir(OUT)):
    print("  -", f)
