# Stratégie de Modélisation (Bilan Audit & Feuille de Route)

> **"Data First, Models Second."**
> Ce document définit la stratégie de modélisation basée sur l'audit réel des données du projet (`weekly_canon.parquet`).

---

## 1. Audit des Données (La Réalité du Terrain)

Avant de choisir des armes, nous avons analysé le champ de bataille (Script: `scripts/quick_audit.py`).

| Métrique | Valeur | Interprétation |
| :--- | :--- | :--- |
| **Séries Temporelles** | 1,782 (54 Magasins x 33 Familles) | Volume suffisant pour du Machine Learning global. |
| **Sparsity Globale** | **25.2%** de zéros | Une méthodologie hybride est **obligatoire**. Un modèle unique échouera. |
| **Volatilité (CV > 1)** | **27.7%** des séries | Presque 1/3 des produits sont erratiques. Il faut des **intervalles de confiance** larges. |

### Le Grand Écart (Segmenter pour régner)
Il existe deux mondes distincts dans vos données :

*   **Le Monde "Intermittent" (Besoin de Croston/SBA)**
    *   `BOOKS` (94% zéros), `BABY CARE` (85% zéros).
    *   *Problème* : Un modèle standard prédira 0.001 tout le temps.
    *   *Solution* : Modèles spécialisés (Croston) ou Tweedie Loss.

*   **Le Monde "Dense" (Besoin de ML/Boosting)**
    *   `EGGS`, `DELI`, `LIQUOR` (< 8% zéros).
    *   *Problème* : La difficulté ici n'est pas le zéro, mais la **promotion** et le **calendrier**.
    *   *Solution* : XGBoost/CatBoost avec features exogènes.

---

## 2. Phase 1 : Baselines (Le Plancher de Performance)

Nous ne lançons pas "une" baseline, mais une **Suite de 3 Baselines** pour couvrir les cas identifiés.

### A. Seasonal Naive (Le Roi du "Dense")
*   **Pour qui ?** Les produits stables (`EGGS`, `BREAD`).
*   **Logique** : `Ventes(t) = Ventes(t-52)`
*   **Pourquoi ?** Si on ne bat pas ça sur le pain ou les œufs, notre IA est inutile.

### B. Moving Average 4-Weeks (Le Suiveur de Tendance)
*   **Pour qui ?** Les produits en changement rapide ou nouvelle tendance.
*   **Logique** : `Ventes(t) = Moyenne(4 dernières semaines)`
*   **Pourquoi ?** Capture mieux les changements récents que la saisonnalité pure.

### C. Croston-SBA (Le Sauveteur du "Sparse")
*   **Pour qui ?** `BOOKS`, `BABY CARE`, `LADIESWEAR`.
*   **Logique** : Prédit séparément la *probabilité* d'une vente et la *quantité*.
*   **Pourquoi ?** Seasonal Naive sur des livres donnera presque toujours 0 (trop de zéros l'an dernier).

> **Action Immédiate** : Implémenter ces 3 dans `scripts/run_baselines.py`.

---

## 3. Phase 2 : Modélisation Avancée (L'Intelligence Artificielle)

Une fois les baselines posées, nous utiliserons le **State-of-the-Art (Gagnants Kaggle M5)**.

### Le Champion : Gradient Boosting (CatBoost / LightGBM)
Pourquoi eux et pas Prophet ou ARIMA ?
1.  **Variables Exogènes** : Ils intègrent triviale le prix du pétrole, les jours fériés (`is_holiday`), et surtout les **promotions** (`onpromotion`). Les méthodes statistiques (ARIMA) gèrent mal ça.
2.  **Global Model** : Un seul modèle apprend sur les 1782 séries à la fois (Cross-learning). Si le magasin A a compris une tendance, le magasin B en profite.
3.  **Vitesse** : 100x plus rapide que d'entraîner 1782 modèles ARIMA séparés.

### Stratégie pour les Zéros (Le "Secret")
Pour gérer les produits `BOOKS` et `EGGS` avec le même modèle, nous utiliserons la fonction de coût **Tweedie** (`objective='tweedie'`).
*   C'est une distribution mathématique qui gère naturellement une masse de zéros ET une distribution continue.
*   C'est LA technique standard pour le Retail moderne.

---

## 4. Phase 3 : Moteur de Décision (Le Business)

Le modèle ne sortira pas un chiffre, mais une **Distribution**.

*   Au lieu de dire : *"On va vendre 10 unités"*
*   Il dira : *"Il y a 90% de chances quon vende entre 2 et 18 unités. Médiane = 10."*

C'est là que l'algo **Newsvendor** intervient :
*   Sur `BOOKS` (Marge haute, Vente rare) -> On stocke un peu plus que la médiane (Risque calculé).
*   Sur `EGGS` (Périssable) -> On fait attention au surstock.

---

## Synthèse : Le Plan d'Action Modifié

1.  **Baseline Suite** : Coder `scripts/run_baselines.py` (Naive + Ma4W + Croston). Comparer les erreurs.
2.  **Features** : Créer le script `src/features/engineering.py` (Lags, Rolling stats).
3.  **ML** : Entraîner un CatBoost avec `loss_function='Tweedie:variance_power=1.5'`.
