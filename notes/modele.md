# Baselines (version correcte avec la data Kaggle Favorita)

1. Seasonal Naive
2. ETS / Theta
3. Croston-SBA (intermittent)
4. Baseline Smart (routing)
5. Backtesting (rolling-origin)

---

## Note importante (contexte data)

Le dataset **Store Sales – Time Series Forecasting (Corporación Favorita)** est **journalier** et l’horizon de prédiction de la compétition est **15 jours**.
Dans notre projet “assistant stock”, on peut travailler de deux façons (compatibles) :

* **Vue daily** : prédire J+1…J+15 (fidèle à Kaggle)
* **Vue weekly** : agréger en semaines pour piloter des décisions “stock” sur un horizon plus long (ex. 8 semaines)

Le texte ci-dessous est valable dans les deux cas : il suffit d’adapter **la saison `s`** et **l’horizon `h`** au grain choisi.

---

## 1) Baseline A — Seasonal Naive (la baseline “bête” mais redoutable)

### Principe

On suppose que la demande suit un **cycle** (saison).
Donc pour prévoir une période future, on prend la valeur de la **même période** lors du cycle précédent :

[
\hat{y}*{t+h} = y*{t+h-s}
]

* (s) = longueur de saison (dépend du grain)

  * **daily** : souvent (s=7) (cycle hebdo), parfois (s=365) (cycle annuel)
  * **weekly** : souvent (s=52) (cycle annuel)
* (h) = horizon (dépend de l’objectif)

  * **daily** : (h \in {1,\dots,15})
  * **weekly** : (h \in {1,\dots,8}) (si tu agrèges)

### Quand ça marche très bien

* produits avec saisonnalité régulière (ex : cycles hebdo ou annuel)
* comportements assez stables (peu de drift)
* séries “denses” (ventes non nulles fréquentes)

### Particularités (important)

* **Zéro tuning** : aucun paramètre à apprendre.
* **Benchmark dur à battre** : très souvent une baseline solide.
* **Mais** : si promos/événements cassent le schéma, ou si la série est très sparse, ça peut rater.

### Différence clé

* Seasonal Naive = “copier/coller du passé saisonnier”
  → pas de tendance explicite, pas d’utilisation de promo.

---

## 2) Baseline B — ETS / Theta (la baseline statistique robuste)

Ici on passe à des modèles “classiques” très utilisés, **simples mais solides**.

### 2.1 ETS (Exponential Smoothing)

ETS décompose la série en :

* **niveau** (level)
* **tendance** (trend)
* **saison** (seasonality)

Idée : les observations récentes comptent plus (poids exponentiels).

#### Pourquoi c’est fort

* capte un **niveau** qui bouge
* capte une **tendance**
* gère une **saisonnalité**
* souvent stable et robuste

#### Particularités

* il faut assez d’historique pour apprendre la saison (surtout si (s=52))
* peut être moins adapté aux séries très intermittentes (beaucoup de zéros)

### 2.2 Theta

Theta est un benchmark très connu en forecasting.
Intuition : on combine une composante “tendance” + une composante “lissage”.

#### Pourquoi on le garde comme baseline

* souvent très bon sans réglages lourds
* bon généraliste sur séries **denses**

### Différence ETS vs Theta

* **ETS** : modèle explicitement “niveau/trend/saison”
* **Theta** : benchmark très performant et souvent robuste, moins “interprétable” dans ses briques que ETS mais redoutable en pratique

---

## 3) Baseline C — Croston-SBA (demande intermittente : plein de zéros)

### Le problème “intermittent”

Sur certaines séries (store × family/catégorie), on peut observer :

* 0, 0, 0, 5, 0, 0, 3, 0, 0, 0, 7, …

ETS/Theta peuvent alors :

* lisser vers 0
* mal représenter les “arrivées rares” de demande

### Principe de Croston

Croston sépare le problème en deux :

1. **Taille de la demande quand elle arrive** (valeurs non nulles)
2. **Temps entre deux demandes** (intervalles entre non-zéros)

Puis il prévoit :

[
\hat{y} = \frac{\hat{z}}{\hat{p}}
]

* (\hat{z}) = taille moyenne lissée des demandes non nulles
* (\hat{p}) = intervalle moyen lissé entre demandes

### Croston-SBA (version corrigée)

Croston “classique” a un biais ; **SBA** corrige ce biais (raison pour laquelle on le préfère en baseline).

### Particularités

* conçu pour séries avec beaucoup de zéros
* ne cherche pas une saison ; cherche une **fréquence d’apparition**
* **à activer seulement si** la série est réellement intermittente (sinon ETS/Theta est souvent meilleur)

### Différence clé

* ETS/Theta = bons quand “ça vend souvent”
* Croston-SBA = bon quand “ça vend rarement”

---

## 4) Baseline Smart (hybride) : principe et valeur ajoutée

### Le problème du “one-size-fits-all”

Un seul modèle pour toutes les séries est souvent mauvais car :

* certaines séries sont régulières et saisonnières
* d’autres sont intermittentes et irrégulières

### L’idée Smart

Comme une équipe supply pragmatique :

> On mesure le profil de demande, puis on choisit automatiquement le modèle le plus adapté.

#### Étape 1 — Mesurer le profil de demande

Pour chaque série (store, family/catégorie), calculer :

* **% de zéros**
* **ADI** (Average Demand Interval) = intervalle moyen entre demandes non nulles
* **CV²** = variabilité (sur les demandes non nulles)

Intuition :

* ADI grand → ventes rares → intermittent
* CV² grand → demande instable

#### Étape 2 — Routing (règles simples)

Exemple de règles défendables :

* si `%zéros > 60%` **ou** `ADI > 1.32` → **Croston-SBA**
* sinon → **AutoETS** (ou Theta)
* Seasonal Naive reste un benchmark de référence

#### Étape 3 — Variante encore plus pro (optionnelle)

Au lieu de seuils fixes :

* tu testes 2–3 modèles sur 1–2 splits rapides
* tu gardes le meilleur par série (mini “model selection” par série)

### Pourquoi c’est une vraie plus-value

* raisonnement métier clair : “produits rares ≠ produits réguliers”
* robustesse sans complexité énorme
* système maintenable

---

## 5) Backtesting (Rolling-Origin) : le principe et pourquoi c’est indispensable

### Pourquoi un seul split est dangereux

Tu peux tomber sur une période “facile” → performance gonflée.
Mais en avançant dans le temps, le comportement change (promos, drift, etc.).

### Rolling-Origin (walk-forward)

Tu simules la vraie vie :

* tu entraînes sur le passé
* tu prédis l’horizon futur
* tu compares à la réalité
* tu avances dans le temps et tu recommences

Exemples :

* **Daily (Kaggle)** : train jusqu’à date T → test sur **T+1…T+15**
* **Weekly (agrégé)** : train jusqu’à semaine W → test sur **W+1…W+8**

### Ce que ça te donne (portfolio crédible)

* performance moyenne réaliste
* stabilité dans le temps (variance)
* diagnostic : périodes/segments où ça casse (promos, événements, drift)

### Bonus : backtest par segments

RMSE/MAE (ou autre) :

* par store
* par family/catégorie
* par intermittent vs dense
* par promo vs non-promo (si dispo)

Ça répond directement aux questions business : “où ça marche / où ça casse”.

---

## Résumé ultra clair (différences)

* **Seasonal Naive** : copie le passé saisonnier, benchmark solide.
* **ETS/Theta** : modèles stats robustes pour séries régulières, captent niveau/tendance/saison.
* **Croston-SBA** : spécialisé pour séries très “zéro” (intermittentes) — à activer conditionnellement.
* **Baseline Smart** : route automatiquement chaque série vers le bon modèle.
* **Backtest rolling** : seule façon crédible de simuler la réalité et tester la stabilité.

