-- =====================================================================
-- Requêtes analytiques — Démographie & conditions de vie au Sénégal
-- =====================================================================

-- 1. Évolution de la fécondité (toutes les EDS)
SELECT annee, valeur AS fecondite
FROM dhs_national WHERE code = 'FE_FRTR_W_TFR' ORDER BY annee;

-- 2. Recul de la mortalité des moins de 5 ans (première vs dernière enquête)
SELECT MIN(annee) AS premiere_eds, MAX(annee) AS derniere_eds,
       MAX(valeur) FILTER (WHERE annee = (SELECT MIN(annee) FROM dhs_national WHERE code='CM_ECMR_C_U5M')) AS u5m_debut,
       MAX(valeur) FILTER (WHERE annee = (SELECT MAX(annee) FROM dhs_national WHERE code='CM_ECMR_C_U5M')) AS u5m_fin
FROM dhs_national WHERE code = 'CM_ECMR_C_U5M';

-- 3. Classement des régions par fécondité (EDS 2023)
SELECT region, valeur AS fecondite
FROM dhs_subnational WHERE code = 'FE_FRTR_W_TFR' ORDER BY valeur DESC;

-- 4. Régions les moins équipées en électricité
SELECT region, valeur AS acces_electricite_pct
FROM dhs_subnational WHERE code = 'HC_ELEC_H_ELC' ORDER BY valeur ASC LIMIT 5;

-- 5. Tableau croisé régional : fécondité, électricité, alphabétisation des femmes
SELECT f.region,
       MAX(CASE WHEN f.code='FE_FRTR_W_TFR' THEN f.valeur END) AS fecondite,
       MAX(CASE WHEN f.code='HC_ELEC_H_ELC' THEN f.valeur END) AS electricite_pct,
       MAX(CASE WHEN f.code='ED_LITR_W_LIT' THEN f.valeur END) AS alphabetisation_femmes_pct
FROM dhs_subnational f GROUP BY f.region ORDER BY fecondite DESC;

-- 6. Évolution de la pauvreté nationale (Banque mondiale)
SELECT annee, valeur AS taux_pauvrete_pct
FROM worldbank WHERE code = 'SI.POV.NAHC' ORDER BY annee;

-- 7. Structure par âge la plus récente (part des jeunes)
SELECT annee,
       MAX(valeur) FILTER (WHERE code='SP.POP.0014.TO.ZS') AS pct_0_14,
       MAX(valeur) FILTER (WHERE code='SP.POP.1564.TO.ZS') AS pct_15_64,
       MAX(valeur) FILTER (WHERE code='SP.POP.65UP.TO.ZS') AS pct_65_plus
FROM worldbank WHERE code IN ('SP.POP.0014.TO.ZS','SP.POP.1564.TO.ZS','SP.POP.65UP.TO.ZS')
GROUP BY annee ORDER BY annee DESC LIMIT 1;

-- 8. Écart régional max sur l'accès à l'eau améliorée
SELECT MAX(valeur) - MIN(valeur) AS ecart_pts,
       (SELECT region FROM dhs_subnational WHERE code='WS_SRCE_H_IMP' ORDER BY valeur DESC LIMIT 1) AS region_max,
       (SELECT region FROM dhs_subnational WHERE code='WS_SRCE_H_IMP' ORDER BY valeur ASC LIMIT 1) AS region_min
FROM dhs_subnational WHERE code = 'WS_SRCE_H_IMP';

-- 9. Croissance démographique et population (5 dernières années)
SELECT annee,
       MAX(valeur) FILTER (WHERE code='SP.POP.TOTL') AS population,
       MAX(valeur) FILTER (WHERE code='SP.POP.GROW') AS croissance_pct
FROM worldbank WHERE code IN ('SP.POP.TOTL','SP.POP.GROW')
GROUP BY annee ORDER BY annee DESC LIMIT 5;

-- 10. Régions cumulant les vulnérabilités (forte fécondité + faible électricité + faible alphabétisation)
WITH r AS (
  SELECT region,
    MAX(CASE WHEN code='FE_FRTR_W_TFR' THEN valeur END) AS fecondite,
    MAX(CASE WHEN code='HC_ELEC_H_ELC' THEN valeur END) AS electricite,
    MAX(CASE WHEN code='ED_LITR_W_LIT' THEN valeur END) AS alpha
  FROM dhs_subnational GROUP BY region)
SELECT region, fecondite, electricite, alpha
FROM r
WHERE fecondite >= 4.5 AND electricite <= 50 AND alpha <= 40
ORDER BY fecondite DESC;
