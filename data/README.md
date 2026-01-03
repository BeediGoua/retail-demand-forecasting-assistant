# Données du Projet

Ce projet utilise le dataset **Store Sales - Time Series Forecasting** de Kaggle (Corporación Favorita).

## Téléchargement des Données

### Option 1 : Via Kaggle CLI (Recommandé)

```bash
# Installer Kaggle CLI
pip install kaggle

# Télécharger le dataset
kaggle competitions download -c store-sales-time-series-forecasting

# Décompresser dans data/raw/
unzip store-sales-time-series-forecasting.zip -d data/raw/
```

### Option 2 : Téléchargement Manuel

1. Aller sur : https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data
2. Télécharger tous les fichiers CSV
3. Les placer dans le dossier `data/raw/`

## Fichiers Attendus

Après téléchargement, vous devriez avoir :
```
data/raw/
├── train.csv
├── test.csv
├── stores.csv
├── oil.csv
├── holidays_events.csv
├── transactions.csv
└── sample_submission.csv
```

## Génération des Données Procesées

Une fois les données brutes en place, lancez le pipeline :

```bash
python scripts/preprocessing.py
python scripts/build_warehouse.py
```

Cela générera :
- `data/processed/*.parquet` (Données nettoyées)
- `data/retail.sqlite` (Data Warehouse)
