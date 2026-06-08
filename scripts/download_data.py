# -*- coding: utf-8 -*-
"""
download_data.py — Données RÉELLES : démographie, santé & conditions de vie au Sénégal.

Sources officielles, APIs publiques (sans authentification) :
  1. DHS / EDS (api.dhsprogram.com) — enquêtes démographiques et de santé menées
     avec l'ANSD. Séries nationales (1986→2023) + détail RÉGIONAL (EDS 2023).
  2. Banque mondiale (API v2) — pauvreté, Gini, population, structure par âge,
     urbanisation, espérance de vie…
  3. geoBoundaries — contours des 14 régions.

NB : les microdonnées EHCVM/RGPH nécessitent une inscription (ANADS / World Bank
Microdata). On exploite ici les INDICATEURS officiels issus de ces enquêtes,
exposés via les APIs ci-dessus.
"""
import os, json, time, urllib.request
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw"); GEO = os.path.join(BASE, "data", "geo")
os.makedirs(RAW, exist_ok=True); os.makedirs(GEO, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (portfolio data project)"}

def get(url, retries=4):
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception as e:
            print(f"   … tentative {k+1} : {e}"); time.sleep(3)
    raise RuntimeError("Échec : " + url)

# Indicateurs DHS retenus (id → libellé FR)
DHS_IND = {
    "FE_FRTR_W_TFR": "Indice de fécondité (enfants/femme)",
    "CM_ECMR_C_U5M": "Mortalité des moins de 5 ans (‰)",
    "CM_ECMR_C_IMR": "Mortalité infantile (‰)",
    "CM_ECMR_C_NNR": "Mortalité néonatale (‰)",
    "FP_CUSM_W_MOD": "Contraception moderne, femmes mariées (%)",
    "RH_DELP_C_DHF": "Accouchements en établissement de santé (%)",
    "CN_NUTS_C_HA2": "Retard de croissance / malnutrition chronique (%)",
    "ED_LITR_W_LIT": "Alphabétisation des femmes (%)",
    "WS_SRCE_H_IMP": "Accès à une source d'eau améliorée (%)",
    "HC_ELEC_H_ELC": "Ménages avec électricité (%)",
}
ids = ",".join(DHS_IND)

# ---------------------------------------------------------------------------
# 1. DHS national (toutes les enquêtes) — lignes "Total"
# ---------------------------------------------------------------------------
print("1) DHS/EDS — séries nationales (1986→2023)")
u = f"https://api.dhsprogram.com/rest/dhs/data?countryIds=SN&indicatorIds={ids}&f=json&perpage=2000"
d = json.loads(get(u))["Data"]
nat = [{"annee": int(x["SurveyYear"]), "code": x["IndicatorId"],
        "indicateur": DHS_IND.get(x["IndicatorId"], x["Indicator"]),
        "valeur": x["Value"]}
       for x in d if str(x.get("IsTotal")) == "1"]
pd.DataFrame(nat).sort_values(["code", "annee"]).to_csv(
    os.path.join(RAW, "dhs_national.csv"), index=False, encoding="utf-8-sig")
print(f"   ✓ dhs_national.csv ({len(nat)} obs)")

# ---------------------------------------------------------------------------
# 2. DHS sous-national — EDS 2023, par région
# ---------------------------------------------------------------------------
print("2) DHS/EDS — détail régional (EDS 2023)")
u = (f"https://api.dhsprogram.com/rest/dhs/data?countryIds=SN&indicatorIds={ids}"
     f"&surveyIds=SN2023DHS&breakdown=subnational&f=json&perpage=2000")
d = json.loads(get(u))["Data"]
sub = [{"region_label": x["CharacteristicLabel"], "code": x["IndicatorId"],
        "indicateur": DHS_IND.get(x["IndicatorId"], x["Indicator"]),
        "valeur": x["Value"]} for x in d]
pd.DataFrame(sub).to_csv(os.path.join(RAW, "dhs_subnational_2023.csv"),
                         index=False, encoding="utf-8-sig")
print(f"   ✓ dhs_subnational_2023.csv ({len(sub)} obs)")

# ---------------------------------------------------------------------------
# 3. Banque mondiale — pauvreté & démographie
# ---------------------------------------------------------------------------
print("3) Banque mondiale (API)")
WB = {
    "SI.POV.NAHC": "Taux de pauvreté national (%)",
    "SI.POV.GINI": "Indice de Gini",
    "SI.POV.DDAY": "Pauvreté extrême à 2,15 $/j (%)",
    "SP.POP.TOTL": "Population totale",
    "SP.POP.GROW": "Croissance démographique (%)",
    "SP.DYN.LE00.IN": "Espérance de vie (ans)",
    "SP.URB.TOTL.IN.ZS": "Population urbaine (%)",
    "SP.POP.0014.TO.ZS": "Part des 0-14 ans (%)",
    "SP.POP.1564.TO.ZS": "Part des 15-64 ans (%)",
    "SP.POP.65UP.TO.ZS": "Part des 65 ans et + (%)",
    "SH.DYN.MORT": "Mortalité des moins de 5 ans, BM (‰)",
}
rows = []
for code, label in WB.items():
    d = json.loads(get(f"https://api.worldbank.org/v2/country/SEN/indicator/{code}?format=json&per_page=500"))
    if len(d) < 2 or not d[1]:
        print(f"   (pas de données : {code})"); continue
    for o in d[1]:
        if o["value"] is not None:
            rows.append({"code": code, "indicateur": label,
                         "annee": int(o["date"]), "valeur": float(o["value"])})
pd.DataFrame(rows).sort_values(["code", "annee"]).to_csv(
    os.path.join(RAW, "worldbank.csv"), index=False, encoding="utf-8-sig")
print(f"   ✓ worldbank.csv ({len(rows)} obs, {len({r['code'] for r in rows})} indicateurs)")

# ---------------------------------------------------------------------------
# 4. GeoJSON régions
# ---------------------------------------------------------------------------
print("4) GeoJSON régions")
with open(os.path.join(GEO, "senegal_regions.geojson"), "wb") as f:
    f.write(get("https://github.com/wmgeolab/geoBoundaries/raw/main/releaseData/gbOpen/SEN/ADM1/geoBoundaries-SEN-ADM1.geojson"))
print("   ✓ senegal_regions.geojson")
print("\n✅ Données réelles téléchargées (DHS/EDS + Banque mondiale).")
