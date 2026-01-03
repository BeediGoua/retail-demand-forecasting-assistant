### 2.1 L’idée générale

Tu prédis les ventes d’une chaîne de supermarchés en **Équateur** (Corporación Favorita), pour de nombreux couples **(magasin × famille de produits)**, en utilisant des signaux comme les **promotions**, le **calendrier / jours fériés**, le **trafic magasin (transactions)** et un facteur macro (**prix du pétrole**). ([Hugging Face][2])

### 2.2 Fichiers principaux (et variables)

**train.csv (entraînement)**

* clés : `date`, `store_nbr`, `family`
* variables : `onpromotion`
* cible : `sales` (ventes totales pour une famille de produits, dans un magasin, à une date donnée). ([Hugging Face][2])

**test.csv (prédiction)**

* mêmes features que `train.csv` (sans `sales`)
* période à prédire : les **15 jours** après la fin du train (horizon compétition). ([Hugging Face][2])

**stores.csv**

* métadonnées magasin : `city`, `state`, `type`, `cluster`. ([Hugging Face][2])

**holidays_events.csv**

* jours fériés / événements + champs `type`, `locale`, `description`, `transferred` (important à traiter correctement). ([Hugging Face][2])

**oil.csv**

* prix du pétrole quotidien (variable macro pertinente pour l’économie équatorienne). ([Hugging Face][2])

**transactions.csv**

* nombre de transactions par `date` et `store_nbr` (proxy du trafic magasin, souvent très utile comme feature). ([Hugging Face][2])

**Différence avec Zindi** : ici la donnée est **journalière**. Pour rester dans notre cadre “assistant stock” à **H = 8 semaines**, on agrège en **hebdomadaire** (store × family × semaine), puis on applique exactement le même pipeline (prévision + incertitude + décision).

---

## 5) Si tu veux comparer des datasets “proches de Zindi”

Voici les plus pertinents pour ton objectif “retail forecasting + décisions stock” :

1. **Kaggle Store Sales (Favorita, Équateur)** → le plus proche de ton besoin (promos, transactions, holidays, signal macro). ([Hugging Face][2])
2. **M5 Forecasting (Walmart)** → très bon pour multi-séries + prix, mais structure un peu différente (plus orientée “retail large scale”). ([GitHub][3])
3. **Walmart Recruiting – Store Sales Forecasting** → hebdo (souvent), bon pour supply, features type prix carburant/températures/markdowns selon fichiers. ([kaggle.com][4])
4. **Rossmann Store Sales** → très bon sur promos/calendrier/clients, mais moins “grocery family-level”, plus “drugstore daily”. ([Tej Analytics][5])

Si ton objectif est de **reproduire l’esprit Zindi** (promo + transactions + holidays, et pouvoir faire un assistant décisionnel), **Favorita (Store Sales)** est franchement le meilleur remplacement.

---

## 6) Télécharger “Store Sales – Time Series Forecasting” (Kaggle)

Deux voies simples :

### Option A — Via l’interface Kaggle

1. Ouvre la page compétition
2. Clique **“Join Competition”** / accepte les règles
3. Onglet **Data** → **Download All**

### Option B — Via Kaggle CLI (recommandé)

1. Crée un token API Kaggle (Account → “Create New API Token”)
2. Installe : `pip install kaggle`
3. Place `kaggle.json` dans le dossier attendu
4. Lance :

* `kaggle competitions download -c store-sales-time-series-forecasting`
* puis unzip


[1]: https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data?utm_source=chatgpt.com "Store Sales - Time Series Forecasting"
[2]: https://huggingface.co/datasets/t4tiana/store-sales-time-series-forecasting?utm_source=chatgpt.com "t4tiana/store-sales-time-series-forecasting · Datasets at ..."
[3]: https://github.com/keshusharmamrt/M5-Walmart-Sales-Forecasting?utm_source=chatgpt.com "keshusharmamrt/M5-Walmart-Sales-Forecasting"
[4]: https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting?utm_source=chatgpt.com "Walmart Recruiting - Store Sales Forecasting"
[5]: https://tejanalytics.com/RossmanStoresTutorial.html?utm_source=chatgpt.com "Advanced Projects: Tej Data Analytics for developers"
