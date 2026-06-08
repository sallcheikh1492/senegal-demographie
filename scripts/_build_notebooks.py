# -*- coding: utf-8 -*-
"""Construit les notebooks du projet démographie (DHS/EDS + Banque mondiale)."""
import os
import nbformat as nbf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_DIR = os.path.join(BASE, "notebooks"); os.makedirs(NB_DIR, exist_ok=True)

def build(path, cells):
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                      "language_info": {"name": "python"}}
    nb["cells"] = [nbf.v4.new_markdown_cell(s) if k == "md" else nbf.v4.new_code_cell(s) for k, s in cells]
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("écrit :", os.path.relpath(path, BASE))

SETUP = r"""
import os, warnings, json, re, unicodedata
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({"figure.figsize": (11, 5), "figure.dpi": 110, "axes.titlesize": 13})

PROJ = os.getcwd()
if not os.path.isdir(os.path.join(PROJ, "data")):
    PROJ = os.path.dirname(PROJ)
RAW = os.path.join(PROJ, "data", "raw"); PROC = os.path.join(PROJ, "data", "processed")
GEO = os.path.join(PROJ, "data", "geo"); FIG = os.path.join(PROJ, "reports", "figures")
MODELS = os.path.join(PROJ, "models")
for d in (PROC, FIG, MODELS): os.makedirs(d, exist_ok=True)

def deacc(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
print("Racine projet :", PROJ)
"""

# ===========================================================================
# NB01 — ACQUISITION & PRÉPARATION
# ===========================================================================
nb01 = [
("md", """# 01 — Acquisition & préparation (données réelles)
## Démographie, santé & conditions de vie au Sénégal — EDS/DHS & Banque mondiale

**100 % données réelles, via APIs publiques** (téléchargées par
`scripts/download_data.py`) :
- 👶 **DHS / EDS** (api.dhsprogram.com) — enquêtes démographiques et de santé
  menées avec l'ANSD : **séries nationales 1986→2023** + **détail régional (EDS 2023)**.
- 🌍 **Banque mondiale** — pauvreté, Gini, population, structure par âge, urbanisation.
- 🗺️ **geoBoundaries** — 14 régions.

> Les microdonnées EHCVM/RGPH nécessitent une inscription (ANADS) ; on exploite ici
> les **indicateurs officiels** issus de ces enquêtes, exposés par ces APIs.
"""),
("code", SETUP),
("md", "### 1. Chargement"),
("code", r"""
dhs_nat = pd.read_csv(os.path.join(RAW, "dhs_national.csv"))
dhs_sub = pd.read_csv(os.path.join(RAW, "dhs_subnational_2023.csv"))
wb = pd.read_csv(os.path.join(RAW, "worldbank.csv"))
print("DHS national :", dhs_nat.shape, "| DHS régional :", dhs_sub.shape, "| WB :", wb.shape)
dhs_nat.head(3)
"""),
("md", """### 2. Nettoyage du détail régional
Les libellés DHS sont hiérarchiques (zones-agrégats sans préfixe ; régions avec
`..` ; régions créées en 2008 avec `....` ; doublons d'anciennes limites `(2005)`).
On isole les **14 régions administratives actuelles**."""),
("code", r"""
EXCL = {"Nord et Est", "Ouest", "Centre", "Sud"}     # zones-agrégats à exclure
def clean_region(lbl):
    s = re.sub(r"^[.\s]+", "", str(lbl))             # enlève les points de hiérarchie
    s = re.sub(r"\s*\(\d{4}\)\s*", "", s).strip()    # enlève (2005)/(2010)
    return s
sub = dhs_sub.copy()
sub = sub[~sub["region_label"].str.contains(r"\(2005\)")]   # écarte anciennes limites
sub["region"] = sub["region_label"].map(clean_region)
sub = sub[~sub["region"].isin(EXCL)]                        # écarte les zones-agrégats
sub["region_geo"] = sub["region"].map(deacc)               # clé de jointure GeoJSON (ASCII)
print("Régions retenues (", sub["region"].nunique(), "):", sorted(sub["region"].unique()))
"""),
("md", "### 3. Tables larges + dimension des indicateurs"),
("code", r"""
dim_indicator = (dhs_nat[["code", "indicateur"]].drop_duplicates()
                 .assign(source="DHS/EDS"))
dhs_nat_wide = dhs_nat.pivot_table(index="annee", columns="code", values="valeur").reset_index()
dhs_sub_wide = sub.pivot_table(index=["region", "region_geo"], columns="code", values="valeur").reset_index()
wb_wide = wb.pivot_table(index="annee", columns="code", values="valeur").reset_index()
print("national large :", dhs_nat_wide.shape, "| régional large :", dhs_sub_wide.shape)
dhs_sub_wide.head(3)
"""),
("md", "### 4. Validation — valeurs nationales EDS 2023 & amplitude régionale"),
("code", r"""
last = dhs_nat[dhs_nat["annee"] == dhs_nat["annee"].max()]
print("== Indicateurs nationaux EDS", int(dhs_nat['annee'].max()), "==")
for _, r in last.iterrows():
    print(f"  {r['valeur']:>6}  {r['indicateur']}")
tfr = sub[sub["code"] == "FE_FRTR_W_TFR"]
print("\nFécondité régionale 2023 : de", tfr['valeur'].min(), "(",
      tfr.loc[tfr['valeur'].idxmin(),'region'], ") à", tfr['valeur'].max(),
      "(", tfr.loc[tfr['valeur'].idxmax(),'region'], ")")
"""),
("md", "### 5. Écriture dans `data/processed/`"),
("code", r"""
tables = {"dhs_national": dhs_nat, "dhs_national_wide": dhs_nat_wide,
          "dhs_subnational": sub[["region","region_geo","code","indicateur","valeur"]],
          "dhs_subnational_wide": dhs_sub_wide,
          "worldbank": wb, "worldbank_wide": wb_wide, "dim_indicator": dim_indicator}
for name, df in tables.items():
    df.to_csv(os.path.join(PROC, f"{name}.csv"), index=False, encoding="utf-8-sig")
    print(f"  {name:22s} {df.shape}")
print("\n✅ Données réelles préparées.")
"""),
]

# ===========================================================================
# NB02 — EDA
# ===========================================================================
nb02 = [
("md", """# 02 — Analyse exploratoire (données réelles)
## Démographie, santé & conditions de vie au Sénégal

Questions : Où en est la **transition démographique** ? Comment ont reculé la
**mortalité infantile** et la **pauvreté** ? Quelles **disparités régionales**
(fécondité, électricité, éducation) ? Quels liens entre éducation et fécondité ?"""),
("code", SETUP),
("code", r"""
nat = pd.read_csv(os.path.join(PROC, "dhs_national_wide.csv"))
sub = pd.read_csv(os.path.join(PROC, "dhs_subnational.csv"))
subw = pd.read_csv(os.path.join(PROC, "dhs_subnational_wide.csv"))
wb = pd.read_csv(os.path.join(PROC, "worldbank_wide.csv"))
dim = pd.read_csv(os.path.join(PROC, "dim_indicator.csv"))
LAB = dict(zip(dim["code"], dim["indicateur"]))
print("OK |", nat.shape, subw.shape, wb.shape)
"""),
("md", "### 1. Transition démographique : fécondité (EDS) & espérance de vie (BM)"),
("code", r"""
fig, ax1 = plt.subplots()
t = nat.dropna(subset=["FE_FRTR_W_TFR"])
ax1.plot(t["annee"], t["FE_FRTR_W_TFR"], "-o", color="#1f4e79", lw=2, label="Fécondité (enfants/femme)")
ax1.axhline(2.1, color="grey", ls="--", lw=.8); ax1.text(t["annee"].min(), 2.25, "Seuil de renouvellement (2,1)", fontsize=8, color="grey")
ax1.set_ylabel("Indice de fécondité", color="#1f4e79")
ax2 = ax1.twinx()
le = wb.dropna(subset=["SP.DYN.LE00.IN"])
ax2.plot(le["annee"], le["SP.DYN.LE00.IN"], color="#27ae60", lw=1.6, label="Espérance de vie (ans)")
ax2.set_ylabel("Espérance de vie (ans)", color="#27ae60")
ax1.set_title("Transition démographique au Sénégal (1986–2023)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "01_transition.png"), bbox_inches="tight")
plt.close(fig); print("→ 01_transition.png")
"""),
("md", "### 2. Recul de la mortalité des enfants (EDS)"),
("code", r"""
fig, ax = plt.subplots()
for code, col, lab in [("CM_ECMR_C_U5M","#c0392b","Moins de 5 ans"),
                       ("CM_ECMR_C_IMR","#e67e22","Infantile (<1 an)"),
                       ("CM_ECMR_C_NNR","#8e44ad","Néonatale")]:
    g = nat.dropna(subset=[code])
    ax.plot(g["annee"], g[code], "-o", color=col, lw=1.7, label=lab)
ax.set_ylabel("Décès pour 1 000 naissances vivantes"); ax.legend()
ax.set_title("Recul de la mortalité des enfants au Sénégal (EDS)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "02_mortalite.png"), bbox_inches="tight")
plt.close(fig); print("→ 02_mortalite.png")
"""),
("md", "### 3. Population, structure par âge et urbanisation (Banque mondiale)"),
("code", r"""
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
# population + croissance
p = wb.dropna(subset=["SP.POP.TOTL"])
axes[0].plot(p["annee"], p["SP.POP.TOTL"]/1e6, color="#1f4e79", lw=2)
axes[0].set_title("Population totale (millions)"); axes[0].set_ylabel("Millions")
# structure par âge (aire empilée)
a = wb.dropna(subset=["SP.POP.0014.TO.ZS"])
axes[1].stackplot(a["annee"], a["SP.POP.0014.TO.ZS"], a["SP.POP.1564.TO.ZS"], a["SP.POP.65UP.TO.ZS"],
                  labels=["0-14 ans","15-64 ans","65+ ans"], colors=["#74add1","#fdae61","#d73027"])
axes[1].legend(loc="center left", fontsize=8); axes[1].set_title("Structure par âge (%)"); axes[1].set_ylim(0,100)
fig.suptitle("Dynamique de population au Sénégal", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "03_population_age.png"), bbox_inches="tight")
plt.close(fig); print("→ 03_population_age.png | jeunes <15 ans :",
      round(a['SP.POP.0014.TO.ZS'].iloc[-1],1), "%")
"""),
("md", "### 4. Pauvreté & inégalités (Banque mondiale)"),
("code", r"""
fig, ax1 = plt.subplots()
pov = wb.dropna(subset=["SI.POV.NAHC"])
ax1.plot(pov["annee"], pov["SI.POV.NAHC"], "-o", color="#c0392b", lw=2, label="Pauvreté nationale (%)")
ax1.set_ylabel("Taux de pauvreté national (%)", color="#c0392b")
gini = wb.dropna(subset=["SI.POV.GINI"])
ax2 = ax1.twinx()
ax2.plot(gini["annee"], gini["SI.POV.GINI"], "-s", color="#1f4e79", lw=1.5, label="Indice de Gini")
ax2.set_ylabel("Indice de Gini", color="#1f4e79")
ax1.set_title("Pauvreté et inégalités au Sénégal")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "04_pauvrete.png"), bbox_inches="tight")
plt.close(fig); print("→ 04_pauvrete.png")
"""),
("md", "### 5. Disparités régionales (EDS 2023)"),
("code", r"""
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
plots = [("FE_FRTR_W_TFR","Fécondité (enfants/femme)","flare", False),
         ("HC_ELEC_H_ELC","Accès électricité (%)","crest", True),
         ("ED_LITR_W_LIT","Alphabétisation femmes (%)","viridis", True)]
for ax,(code,title,cmap,asc) in zip(axes, plots):
    s = subw[["region",code]].dropna().sort_values(code, ascending=asc)
    sns.barplot(data=s, y="region", x=code, ax=ax, palette=cmap)
    ax.set_title(title); ax.set_xlabel(""); ax.set_ylabel("")
fig.suptitle("Disparités régionales — EDS 2023", y=1.03)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "05_regions_bars.png"), bbox_inches="tight")
plt.close(fig); print("→ 05_regions_bars.png")
"""),
("md", "### 6. Cartes choroplèthes régionales (EDS 2023)"),
("code", r"""
from matplotlib.patches import Polygon as MplPoly
import matplotlib.colors as mcolors, matplotlib.cm as cm
geo = json.load(open(os.path.join(GEO, "senegal_regions.geojson"), encoding="utf-8"))
def rings(g): return [g["coordinates"]] if g["type"]=="Polygon" else g["coordinates"]

def choro(ax, code, title, cmap, fmt="{:.0f}"):
    vmap = dict(zip(subw["region_geo"], subw[code]))
    vals = [v for v in vmap.values() if pd.notna(v)]
    norm = mcolors.Normalize(min(vals), max(vals)); sm = cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    for feat in geo["features"]:
        nm = feat["properties"]["shapeName"]; val = vmap.get(nm)
        color = sm.to_rgba(val) if val is not None and pd.notna(val) else "#eee"
        big=-1; c=None
        for poly in rings(feat["geometry"]):
            ext=np.array(poly[0]); ax.add_patch(MplPoly(ext, closed=True, facecolor=color, edgecolor="white", lw=.5))
            ar=abs(np.sum(ext[:,0]*np.roll(ext[:,1],1)-np.roll(ext[:,0],1)*ext[:,1]))/2
            if ar>big: big,c=ar,(ext[:,0].mean(),ext[:,1].mean())
        if c is not None and val is not None and pd.notna(val):
            ax.annotate(fmt.format(val), c, ha="center", va="center", fontsize=7, weight="bold")
    ax.autoscale(); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=12)
    cb=plt.colorbar(sm, ax=ax, shrink=.55);
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
choro(axes[0], "FE_FRTR_W_TFR", "Fécondité (enfants/femme)", "Reds", "{:.1f}")
choro(axes[1], "HC_ELEC_H_ELC", "Accès à l'électricité (%)", "Greens")
choro(axes[2], "CN_NUTS_C_HA2", "Malnutrition chronique (%)", "OrRd")
fig.suptitle("Cartes régionales — EDS 2023 (données réelles)", y=1.02)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "06_cartes_regionales.png"), bbox_inches="tight", dpi=120)
plt.close(fig); print("→ 06_cartes_regionales.png")
"""),
("md", "### 7. Lien éducation ↔ fécondité (régions, 2023)"),
("code", r"""
s = subw.dropna(subset=["ED_LITR_W_LIT","FE_FRTR_W_TFR"])
corr = s["ED_LITR_W_LIT"].corr(s["FE_FRTR_W_TFR"])
fig, ax = plt.subplots()
ax.scatter(s["ED_LITR_W_LIT"], s["FE_FRTR_W_TFR"], s=60, color="#1f4e79")
for _, r in s.iterrows():
    ax.annotate(r["region"], (r["ED_LITR_W_LIT"], r["FE_FRTR_W_TFR"]), fontsize=7, xytext=(3,3), textcoords="offset points")
z = np.polyfit(s["ED_LITR_W_LIT"], s["FE_FRTR_W_TFR"], 1)
xs = np.linspace(s["ED_LITR_W_LIT"].min(), s["ED_LITR_W_LIT"].max(), 50)
ax.plot(xs, np.polyval(z, xs), color="#c0392b", ls="--", label=f"corr = {corr:.2f}")
ax.set_xlabel("Alphabétisation des femmes (%)"); ax.set_ylabel("Fécondité (enfants/femme)")
ax.legend(); ax.set_title("Plus d'éducation des femmes ↔ moins d'enfants (régions, 2023)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "07_education_fecondite.png"), bbox_inches="tight")
plt.close(fig); print("→ 07_education_fecondite.png | corr =", round(corr,2))
"""),
("md", """### Synthèse EDA
- **Transition démographique** en cours : fécondité de **6,4 (1986) → 4,0 (2023)**,
  espérance de vie en forte hausse, mais population encore très **jeune**.
- **Mortalité des enfants** fortement réduite depuis les années 1990.
- **Pauvreté** en recul mais encore élevée ; inégalités modérées (Gini ~36).
- **Fortes disparités régionales** : Dakar/ouest urbanisés (faible fécondité, fort
  accès aux services) vs régions du sud/est (fécondité élevée, accès plus faible).
- L'**éducation des femmes** est nettement corrélée à une **fécondité plus basse**.
"""),
]

# ===========================================================================
# NB03 — TENDANCES & PROJECTION
# ===========================================================================
nb03 = [
("md", """# 03 — Tendances & projection
Projection simple de la **fécondité** et de la **population** à l'horizon 2035,
à partir des tendances réelles observées."""),
("code", SETUP),
("code", r"""
nat = pd.read_csv(os.path.join(PROC, "dhs_national_wide.csv"))
wb = pd.read_csv(os.path.join(PROC, "worldbank_wide.csv"))
from sklearn.linear_model import LinearRegression
"""),
("md", "### 1. Projection de la fécondité (régression linéaire sur les EDS récentes)"),
("code", r"""
t = nat.dropna(subset=["FE_FRTR_W_TFR"])
t = t[t["annee"] >= 1997]                      # tendance récente
X = t[["annee"]].values; y = t["FE_FRTR_W_TFR"].values
lr = LinearRegression().fit(X, y)
fut = np.arange(t["annee"].min(), 2036).reshape(-1,1)
pred = lr.predict(fut)
# année estimée d'atteinte du seuil de renouvellement (2,1)
an_seuil = (2.1 - lr.intercept_) / lr.coef_[0]
fig, ax = plt.subplots()
ax.plot(t["annee"], y, "o", color="#1f4e79", label="EDS observé")
ax.plot(fut.ravel(), pred, "--", color="#c0392b", label="Tendance projetée")
ax.axhline(2.1, color="grey", ls=":"); ax.text(1998, 2.2, "Renouvellement (2,1)", fontsize=8, color="grey")
ax.legend(); ax.set_ylabel("Indice de fécondité"); ax.set_title("Projection de la fécondité au Sénégal")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "08_projection_fecondite.png"), bbox_inches="tight")
plt.close(fig)
print("Fécondité projetée 2035 : %.1f enfants/femme" % lr.predict([[2035]])[0])
print("Seuil de renouvellement (2,1) atteint vers :", int(round(an_seuil)))
"""),
("md", "### 2. Projection de la population (taux de croissance récent)"),
("code", r"""
p = wb.dropna(subset=["SP.POP.TOTL"]).sort_values("annee")
pop0 = p["SP.POP.TOTL"].iloc[-1]; an0 = int(p["annee"].iloc[-1])
g = wb.dropna(subset=["SP.POP.GROW"])["SP.POP.GROW"].iloc[-5:].mean() / 100
years = list(range(an0, 2036))
proj = [pop0 * (1+g)**(yr-an0) for yr in years]
fig, ax = plt.subplots()
ax.plot(p["annee"], p["SP.POP.TOTL"]/1e6, color="#1f4e79", lw=2, label="Observé (BM)")
ax.plot(years, np.array(proj)/1e6, "--", color="#c0392b", lw=2, label=f"Projection (+{g*100:.1f}%/an)")
ax.legend(); ax.set_ylabel("Population (millions)"); ax.set_title("Projection de la population du Sénégal (2035)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "09_projection_population.png"), bbox_inches="tight")
plt.close(fig)
pd.DataFrame({"annee": years, "population_projetee": proj}).to_csv(
    os.path.join(MODELS, "projection_population.csv"), index=False, encoding="utf-8-sig")
print("Population %d : %.1f M -> projection 2035 : %.1f M" % (an0, pop0/1e6, proj[-1]/1e6))
"""),
("md", """### Conclusion
- Si la tendance se poursuit, la fécondité continue de **baisser** mais le seuil de
  renouvellement (2,1) ne serait atteint qu'**au-delà de 2035** → la population
  continuera de croître fortement (**dividende démographique** potentiel).
- ⚠️ Projections linéaires simples, à titre illustratif : la réalité dépendra des
  politiques (éducation, planification familiale, santé) et du contexte socio-économique.
"""),
]

build(os.path.join(NB_DIR, "01_acquisition_preparation.ipynb"), nb01)
build(os.path.join(NB_DIR, "02_analyse_exploratoire.ipynb"), nb02)
build(os.path.join(NB_DIR, "03_tendances_projection.ipynb"), nb03)
print("Notebooks construits.")
