
# Retail Forecasting & Inventory Assistant — Document projet (version adaptée Kaggle Favorita)

## 1) Le problème réel (sans jargon)

Imagine un réseau de supermarchés qui vend des produits du quotidien (riz, huile, boissons…).
Chaque semaine, l’équipe doit décider **combien commander** pour les semaines à venir (on vise **jusqu’à 8 semaines** pour piloter le stock).

Deux erreurs coûtent très cher :

* **Rupture de stock** : le produit n’est plus disponible → ventes perdues + clients frustrés.
* **Surstock** : trop de stock → argent immobilisé + risques de pertes (périssables, casse, stockage, obsolescence).

Le cœur du projet :

> Comment aider un magasin à commander la bonne quantité, au bon moment, en limitant ruptures et surstocks ?

---

## 2) Pourquoi c’est difficile (les obstacles “terrain”)

### A) La demande varie fortement

La demande bouge selon :

* la **saison** (fêtes, rentrée, périodes de paie…)
* les **promotions** (une promo peut faire exploser les ventes)
* des **événements** (jours fériés, événements locaux) et des comportements propres à chaque magasin

### B) Certaines ventes sont rares (beaucoup de zéros)

Selon les magasins et familles, il peut y avoir :

* des périodes longues à **zéro vente**
* des ventes “par à-coups”

➡️ Risque : un modèle “standard” peut apprendre à prédire zéro trop souvent et rater les vrais pics.

### C) L’incertitude est inévitable

Même un bon modèle doit fournir :

* une estimation centrale (“on prévoit ~50”)
* et surtout une **plage plausible** (“ça peut être entre 30 et 80”)

➡️ Cette incertitude est indispensable pour dimensionner un stock “sûr”.

---

## 3) Les questions concrètes à résoudre (côté business)

Un manager retail/supply veut des réponses actionnables :

1. Quels produits risquent la rupture dans 2 à 4 semaines ?
2. Quelles décisions sont prioritaires maintenant ? (Top 20 actions)
3. Si le budget est limité, où faut-il mettre le stock en priorité ?
4. Mes prévisions sont-elles fiables et stables dans le temps ?
5. Est-ce que le comportement a changé récemment ? (drift)
6. Pourquoi ce produit va exploser ? (promo, saison, effet magasin…)

➡️ Le projet doit répondre à ces questions, pas juste sortir un chiffre.

---

## 4) Les données (structure simple, adaptée Kaggle)

### A) Ce qu’on observe réellement (Kaggle Favorita)

On a un historique de ventes **journalier** pour un grand nombre de séries :

> (date, magasin, famille de produits) → ventes

Avec des signaux utiles :

* **promotion** (intensité `onpromotion`)
* **transactions** (proxy trafic magasin)
* **jours fériés / événements**
* **prix du pétrole** (signal macro)
* **métadonnées magasins** (ville, type, cluster…)

### B) Comment on reste cohérent avec notre “assistant stock à 8 semaines”

Même si la data est journalière, notre outil “stock” travaille mieux en **hebdomadaire**.

Donc on crée deux vues :

* **Vue Daily (mode compétition / modèle court-terme)** : prévision à 15 jours
* **Vue Weekly (mode assistant stock)** : on **agrège** les données par semaine pour prévoir **jusqu’à 8 semaines**

➡️ Comme ça, on garde ton objectif “H = 8 semaines” tout en exploitant la richesse Kaggle.

---

## 5) La solution : un assistant de décision (pas juste un modèle)

Nom du projet : **Retail Forecasting & Inventory Assistant**

Le système fait 3 choses :

1. **prévoit la demande**
2. **quantifie l’incertitude**
3. **recommande une action de commande**

Pour chaque **magasin × famille × semaine future**, il produit :

1. **Prévision centrale** (ex : 50)
2. **Incertitude (intervalle)** (ex : 30 à 80)
3. **Recommandation de commande** (ex : 70 pour réduire le risque)
4. **Priorité business** (ex : “critique : risque élevé + impact élevé”)
5. **Explication simple** (promo + tendance + saison + trafic)

➡️ C’est cette couche “assistant” qui transforme le ML en outil.

---

## 6) Ce que font la plupart des projets… et ce qu’on améliore

### Ce que la majorité fait

* un modèle unique (souvent LightGBM)
* une prédiction moyenne
* un split simple
* pas d’intervalles, pas de décision stock, peu de traçabilité

### Notre plus-value (ce qui rend le projet solide)

1. **Rolling backtests** (évaluation réaliste dans le temps)
2. **Intervalles fiables** (calibrés)
3. **Décision stock** (rupture vs surstock)
4. **Base de données + traçabilité** (historisation des runs)
5. **Monitoring + drift** (détecter les dégradations)

➡️ On livre un système complet :
**Forecast → Uncertainty → Decision → Monitoring → UI**

---

## 7) Déroulé du projet (étapes claires)

### Étape 1 — Ingestion + Base de données (fondation “pro”)

On construit une DB (PostgreSQL ou DuckDB) et on stocke :

* ventes daily (canonique)
* ventes weekly (vue agrégée)
* features calendaires / stores / holidays / oil / transactions
* prévisions + décisions + métriques + runs

Tables (idée, mais cohérente) :

* `fact_sales_daily` (date × store × family)
* `fact_sales_weekly` (week × store × family)
* `fact_forecasts` (p50/p10/p90 + horizon)
* `fact_decisions` (order_qty, risk, expected_cost)
* `fact_metrics` (rmse, coverage, drift…)
* `dim_runs` (params, version modèle, date…)

### Étape 2 — Baselines (simples mais pertinentes)

Objectif : référence solide + segmentation des séries.

* baselines simples : médiane, moyenne mobile
* baselines “top” :

  * **Seasonal Naive** (benchmark)
  * **ETS / Theta** (robuste sur séries régulières)
  * **Croston-SBA** (séries avec beaucoup de zéros)
  * **Baseline Smart** : choisir automatiquement la bonne baseline selon le profil de la série (dense vs intermittent)

### Étape 3 — Modèle puissant (style compétition)

Modèle global multi-séries :

* LightGBM / CatBoost
* lags, rolling stats, promo, calendrier, transactions, oil, stores…

Toujours avec :

* **rolling backtest strict**

### Étape 4 — Incertitude (intervalles)

On produit :

* P10 / P50 / P90
  et/ou
* intervalles calibrés

Utilité :

* le stock dépend du risque (scénario haut/bas), pas de la moyenne.

### Étape 5 — Décision stock (la vraie partie business)

Règle simple et défendable :

* rupture très chère → commander plus haut (proche P90)
* surstock très cher → commander plus bas (P50/P60)

On sort :

* `order_qty`, `stockout_risk`, `expected_cost`

### Étape 6 — Dashboard / App (questions métier)

Pages :

* Top 20 décisions cette semaine
* Risque de rupture (2–4 semaines)
* Fiabilité des intervalles (couverture)
* Drift / segments en dégradation

---

## 8) Pitch court (non technique)

> On construit un assistant pour aider un réseau de magasins à mieux gérer leurs stocks.
> À partir d’historiques de ventes (journaliers, avec promos, jours fériés, trafic magasin…), il prévoit la demande, donne une fourchette d’incertitude, puis recommande combien commander pour éviter ruptures et surstocks.
> Le tout est traçable via une base de données et piloté via un dashboard pour prioriser les décisions, vérifier la fiabilité et détecter les changements de comportement.


