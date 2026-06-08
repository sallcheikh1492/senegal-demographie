-- =====================================================================
-- Démographie, santé & conditions de vie au Sénégal (EDS/DHS + Banque mondiale)
-- Schéma PostgreSQL + chargement des données traitées (data/processed/)
-- =====================================================================
DROP TABLE IF EXISTS dhs_national, dhs_subnational, worldbank, dim_indicator CASCADE;

CREATE TABLE dim_indicator (
    code        TEXT PRIMARY KEY,
    indicateur  TEXT,
    source      TEXT
);

-- Séries nationales EDS (format long : 1 ligne par enquête × indicateur)
CREATE TABLE dhs_national (
    annee       INTEGER,
    code        TEXT,
    indicateur  TEXT,
    valeur      NUMERIC,
    PRIMARY KEY (annee, code)
);

-- Détail régional EDS 2023 (14 régions)
CREATE TABLE dhs_subnational (
    region      TEXT,
    region_geo  TEXT,        -- clé ASCII (jointure GeoJSON)
    code        TEXT,
    indicateur  TEXT,
    valeur      NUMERIC
);

-- Indicateurs macro Banque mondiale (format long)
CREATE TABLE worldbank (
    code        TEXT,
    indicateur  TEXT,
    annee       INTEGER,
    valeur      NUMERIC
);

-- Chargement (psql) :
-- \copy dim_indicator    FROM 'data/processed/dim_indicator.csv'    CSV HEADER;
-- \copy dhs_national     FROM 'data/processed/dhs_national.csv'     CSV HEADER;
-- \copy dhs_subnational  FROM 'data/processed/dhs_subnational.csv'  CSV HEADER;
-- \copy worldbank        FROM 'data/processed/worldbank.csv'        CSV HEADER;
