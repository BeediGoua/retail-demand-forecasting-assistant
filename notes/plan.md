

## 0) Ce que tu dois avoir localement (check rapide)

Dans ton dossier `data/raw/` tu dois voir (au minimum) :

* `train.csv`, `test.csv`, `stores.csv`, `holidays_events.csv`, `oil.csv`, `transactions.csv`, `sample_submission.csv`

Si tu as ça, on démarre.

---

## 1) Charger les données + audit “anti-erreurs”

### Objectif

Vérifier que tout est cohérent avant de construire quoi que ce soit.

### À vérifier (très important)

1. **Types** : `date` doit être en datetime.
2. **Granularité** : une ligne = (`date`, `store_nbr`, `family`) dans `train`.
3. **Doublons** : pas de doublon sur (`date`, `store_nbr`, `family`).
4. **Valeurs manquantes** :

   * `oil` a souvent des trous → normal, faudra remplir.
   * `onpromotion` peut avoir des 0.
5. **Sparsité** : % de zéros par série (store×family) → utile pour Croston.

Livrable conseillé : un notebook `01_audit_eda.ipynb` avec :

* nb lignes/colonnes
* période couverte
* top familles/stores
* histogramme des ventes
* heatmap % de zéros par famille

---

## 2) Construire la “table canonique” (celle qui sert à tout)

### Objectif

Avoir **une seule table** au bon grain, où toutes les features sont jointes.

**Clé canonique :** `(date, store_nbr, family)`

### Jointures recommandées

* `train/test` + `stores.csv` via `store_nbr`
* * `transactions.csv` via (`date`, `store_nbr`)
* * `oil.csv` via `date`
* * `holidays_events.csv` via `date` (mais attention : il peut y avoir plusieurs événements le même jour)

### Feature engineering calendrier (indispensable)

Créer :

* `day_of_week`, `week_of_year`, `month`, `year`
* `is_weekend`
* (option) `payday_proxy` : 15 et fin de mois (le dataset mentionne que ça impacte)

Livrable : une table finale (DataFrame) `df_canon` ou un export parquet.

---

## 3) Choisir ton “grain” de travail : daily ou weekly

Tu as 2 voies (tu peux faire les 2, mais commence par une seule) :

### Option A — Daily (fidèle à Kaggle)

* horizon = **15 jours**
* baselines : seasonal naive (s=7), ETS/Theta, etc.
* décisions stock plus “court terme”

### Option B — Weekly (pour coller à ton projet “8 semaines”)

Tu agrèges :

* `sales_week = somme des sales sur la semaine`
* `onpromotion_week = somme ou moyenne`
* `transactions_week = somme`
* `oil_week = moyenne`

Et tu passes en :

* horizon = **8 semaines**
* seasonal naive (s=52)

Mon conseil :
**Fais Weekly** si ton objectif c’est “inventory assistant” + newsvendor + top décisions.

Livrable : `df_weekly` avec clé `(year_week, store_nbr, family)`.

---

## 4) Construire la base de données (propre et utile)

### Pourquoi une DB ici ?

Parce que tu veux historiser :

* ventes (faits)
* prévisions (par run / modèle / horizon)
* décisions stock
* métriques + drift

### Schéma minimal (suffisant)

**Dimensions**

* `dim_store(store_nbr, city, state, type, cluster)`
* `dim_item_family(family)`
* `dim_date(date, year, month, week, dow, is_holiday, ...)`

**Faits**

* `fact_sales(date, store_nbr, family, sales, onpromotion, transactions, oil, ...)`
* `fact_forecasts(run_id, date, horizon, store_nbr, family, p50, p10, p90, model_name, model_version)`
* `fact_decisions(run_id, date, store_nbr, family, order_qty, service_level, stockout_risk, expected_cost)`
* `fact_metrics(run_id, metric_name, segment_key, value)`
* `dim_run(run_id, created_at, params_json, git_commit)`

Tech simple :

* **DuckDB** (simple et rapide)
* ou **PostgreSQL** (plus “prod-like”, très bien avec Docker)

---

## 5) Baselines “top” (le pack propre)

### Objectif

Avoir une référence **dure à battre** et crédible.

Baselines à implémenter :

1. **Seasonal Naive**

   * daily : s=7
   * weekly : s=52
2. **ETS / Theta**
3. **Croston-SBA** (si séries intermittentes)
4. **Baseline Smart (routing)**

   * si intermittent → Croston
   * sinon → ETS/Theta
5. **Rolling backtest** (obligatoire)

Livrable : `02_baselines_backtest.ipynb` + un tableau résultats :

* RMSE global
* RMSE par store / family
* RMSE dense vs intermittent

---

## 6) Modèle “fort” (après baselines)

### Objectif

Un modèle global multi-séries (tabulaire), solide et simple à maintenir.

Approche standard :

* LightGBM ou CatBoost
* features :

  * lags (1,2,7,14,28 en daily ; 1,2,4,8 en weekly)
  * rolling mean/median (7/28 jours ou 4/8 semaines)
  * promo stats (rolling sum)
  * calendar features
  * store metadata

Livrable : `03_model_lgbm.ipynb` + backtest rolling.

---

## 7) Incertitude (intervalles) : indispensable pour stock

### Objectif

Produire P10/P50/P90 ou intervalles 80%.

2 méthodes pratiques :

1. **Quantile regression** avec LightGBM (objective quantile)
2. **Conformal prediction** (calibrage des intervalles autour de n’importe quel modèle)

Livrable : `04_uncertainty_calibration.ipynb` :

* courbe de couverture (ex : intervalle 80% couvre-t-il ~80% ?)
* calibration avant/après

---

## 8) Décision stock (étape business)

### Objectif

Transformer (prévision + incertitude) → **commande recommandée**.

Règle newsvendor (simple et défendable) :

* quantile cible = ( \frac{C_u}{C_u + C_o} )
* si rupture coûte cher → quantile haut (ex P90)
* si surstock coûte cher → quantile moyen (P60)

Livrable :

* une table `fact_decisions` avec :

  * `order_qty`
  * `stockout_risk`
  * `expected_cost`

---

## 9) Dashboard / App (livrable portfolio)

Streamlit (simple) avec 4 pages :

1. **Top 20 décisions** (cette semaine / aujourd’hui)
2. **Risque de rupture** (heatmap / tableau)
3. **Qualité des intervalles** (couverture)
4. **Monitoring + drift** (erreur dans le temps)

---

## 10) Arborescence repo (propre)

* `data/raw/` (csv)
* `data/processed/` (parquet)
* `sql/` (schema + queries)
* `src/`

  * `ingest/`
  * `features/`
  * `baselines/`
  * `models/`
  * `uncertainty/`
  * `decision/`
  * `monitoring/`
* `notebooks/01_... 02_...`
* `app/` (streamlit)
* `README.md`
