# 📊 Dashboard Power BI — Démographie & conditions de vie au Sénégal

Guide pas-à-pas pour construire le tableau de bord à partir des tables prêtes à
l'emploi (`powerbi/data/`). Temps estimé : **20–30 min**.

> ℹ️ Le fichier `.pbix` est un binaire propriétaire qui ne peut pas être généré
> par script : ce guide + les CSV + les mesures DAX permettent de le reconstruire
> à l'identique dans **Power BI Desktop** (gratuit, Windows).

---

## 1. Préparer les données
Lancer (depuis la racine du projet) :
```bash
python scripts/build_powerbi.py
```
Cela génère dans `powerbi/data/` :

| Table | Rôle | Colonnes clés |
|---|---|---|
| `faits_national.csv`  | **Faits** (séries nationales EDS + Banque mondiale) | annee, code, valeur, source |
| `faits_regional.csv`  | **Faits** (EDS 2023 par région) | region_geo, code, valeur |
| `dim_indicateur.csv`  | **Dimension** indicateurs | code, indicateur, categorie, sens_positif |
| `dim_region.csv`      | **Dimension** régions (+ centroïdes carte) | region, region_geo, region_map, latitude, longitude |
| `dim_annee.csv`       | **Dimension** temps | annee, decennie |

---

## 2. Importer dans Power BI Desktop
1. **Accueil → Obtenir les données → Texte/CSV** ; importer les **5 fichiers** de
   `powerbi/data/`.
2. Pour chaque table, vérifier les types (Power Query) : `valeur` = Nombre décimal,
   `annee`/`latitude`/`longitude` = Nombre, le reste = Texte. **Charger**.

---

## 3. Créer le modèle (vue *Modèle*)
Relier (glisser-déposer) en **un-à-plusieurs** :

```
dim_indicateur[code]   1 ─── *  faits_national[code]
dim_indicateur[code]   1 ─── *  faits_regional[code]
dim_annee[annee]       1 ─── *  faits_national[annee]
dim_region[region_geo] 1 ─── *  faits_regional[region_geo]
```
- Toutes les relations : sens de filtre **simple** (du *dim* vers les *faits*).
- Marquer `dim_annee` comme **table de dates** (facultatif) ou garder `annee` numérique.

---

## 4. Ajouter les mesures DAX
Copier les mesures de [`mesures_dax.txt`](mesures_dax.txt) (clic droit sur
`faits_national` → **Nouvelle mesure**, une par une).

---

## 5. Construire les pages

### 🟦 Page 1 — Vue d'ensemble nationale
- **5 cartes (KPI)** en haut : `KPI Fécondité (dernier)`, `KPI Mortalité -5 ans (dernier)`,
  `KPI Pauvreté (%)`, `KPI Population (millions)`, `KPI Part des moins de 15 ans (%)`.
- **Courbe** (Graphique en courbes) : Axe X = `dim_annee[annee]`, Valeur =
  `Valeur nationale`, et un **segment (slicer)** `dim_indicateur[indicateur]`
  (sélection unique) → l'utilisateur choisit l'indicateur à tracer.
- **Courbe dédiée** : fécondité — filtrer le visuel sur `code = FE_FRTR_W_TFR`,
  ajouter une **ligne constante = 2,1** (seuil de renouvellement).
- **Segment** `source` (EDS/DHS vs Banque mondiale).

### 🟩 Page 2 — Comparaison régionale (EDS 2023)
- **Carte choroplèthe** : visuel **Carte choroplète (Filled map)** →
  Localisation = `dim_region[region_map]` (catégorie de données = *Lieu*),
  Info-bulle/Saturation = `Valeur régionale`. Slicer `dim_indicateur` pour choisir
  l'indicateur cartographié.
  - *Alternative exacte* : visuel **Shape Map** (préversion) avec une carte
    personnalisée — convertir `data/geo/senegal_regions.geojson` en **TopoJSON**
    sur [mapshaper.org](https://mapshaper.org) (Import → Export *TopoJSON*),
    puis « Ajouter une carte » et lier sur `shapeName` ↔ `region_geo`.
  - *Repli fiable* : visuel **Carte (bulles)** avec `latitude`/`longitude` de
    `dim_region` et Taille = `Valeur régionale`.
- **Barres** : Axe Y = `dim_region[region]`, Valeur = `Valeur régionale`, triées.
- **Cartes** : `Région la plus élevée`, `Région la plus basse`, `Écart régional (max - min)`.

### 🟧 Page 3 — Pauvreté & structure de population
- **Courbe** pauvreté : `code = SI.POV.NAHC` sur `annee`.
- **Aires empilées** structure par âge : 3 séries (`SP.POP.0014/1564/65UP.TO.ZS`).
- **Carte** population (millions) + croissance.

---

## 6. Filtres (volet de filtres / segments)
- `dim_annee[annee]` (ou `decennie`)
- `dim_indicateur[indicateur]` et `dim_indicateur[categorie]`
- `dim_region[region]`
- `faits_national[source]`

---

## 7. Mise en forme conseillée
- Thème : bleu marine `#1F4E79`, vert `#27AE60`, rouge `#C0392B`, orange `#E67E22`.
- Titre : « Démographie & conditions de vie au Sénégal — EDS/DHS & Banque mondiale ».
- Bandeau de **transparence des sources** en pied de page (cf. README principal).
- Utiliser la mesure `Couleur indicateur` pour la mise en forme conditionnelle.

---

## 8. Publier
- **Fichier → Enregistrer** sous `powerbi/dashboard_senegal.pbix`.
- (Optionnel) **Publier** sur *Power BI Service* et exporter une image/PDF pour le
  portfolio, ou capturer une copie d'écran à ajouter au README.
