# Stratégie de Prévision "Baseline" : Le Guide Complet

Ce document détaille la logique, les mathématiques et les choix stratégiques derrière notre "Baseline" (le modèle de référence). L'objectif n'est pas seulement de donner des formules, mais d'expliquer **pourquoi** chaque décision a été prise.

---

## 1. La Philosophie : "Le Juste Outil pour la Juste Tâche"

En Retail, tous les produits ne se ressemblent pas.
*   Le **Pain de Mie** se vend tous les jours, avec une régularité d'horloge.
*   La **Truffe Noire** se vend rarement, parfois par pics imprévisibles.

Utiliser le même modèle mathématique pour ces deux produits serait une erreur fondamentale.
*   Un modèle de "Moyenne" est excellent pour le Pain, mais catastrophique pour la Truffe (il prédirait 0.05 truffe par jour, ce qui est physiquement impossible et logistiquement inutile).

C'est pourquoi nous avons rejeté l'idée d'un "Modèle Unique" au profit d'une **Stratégie Hybride (Piecewise Hybrid)**. Nous analysons d'abord le comportement du produit, puis nous lui assignons l'expert mathématique le plus adapté.

---

## 2. Les Candidats (Nos Modèles Élémentaires)

Nous avons mis en compétition trois approches classiques. Voici leur fonctionnement intime.

### A. Le Saisonnier Naïf (`Seasonal Naive`)
**L'intuition** : "L'histoire se répète."
Si nous sommes la semaine 42 de 2017, le client va probablement acheter la même chose qu'à la semaine 42 de 2016.

**La Formule** :
$$ \hat{y}_{t} = y_{t-52} $$
*   $\hat{y}_{t}$ : La prévision pour aujourd'hui.
*   $y_{t-52}$ : La vente réelle d'il y a exactement 52 semaines (1 an).

**Pourquoi ce choix ?**
Le Retail est dominé par le calendrier (Noël, Rentrée, Soldes). Ce modèle capture parfaitement ces pics récurrents sans aucun calcul complexe. C'est le "niveau zéro" de l'intelligence : si un modèle complexe (IA) ne peut pas battre ça, il est inutile.

**Ses limites** : Il est aveugle aux tendances récentes. Si un produit a explosé en popularité le mois dernier, le Saisonnier Naïf l'ignorera et regardera bêtement l'année dernière (où le produit était peut-être inconnu).

### B. La Moyenne Mobile (`Moving Average`)
**L'intuition** : "La vérité est dans le passé récent."
Ce qui s'est passé il y a un an est vieux. Ce qui compte, c'est ce qui s'est passé ces 4 dernières semaines.

**La Formule** :
$$ \hat{y}_{t} = \frac{1}{k} \sum_{i=1}^{k} y_{t-i} $$
*   $k$ : La fenêtre (ici, 4 semaines).
*   $\sum$ : On fait la somme des 4 dernières semaines.
*   $\frac{1}{k}$ : On divise par 4 pour avoir la moyenne.

**Pourquoi ce choix ?**
C'est l'antidote au Saisonnier Naïf. Il est très réactif. Si les ventes chutent soudainement, la moyenne va baisser rapidement pour s'ajuster. C'est idéal pour les produits "Smooth" (stables) qui changent lentement de niveau.

**Ses limites** : Il déteste les pics. Si vous vendez 1000 unités à Noël, la moyenne va être "polluée" et prédire trop haut en Janvier, puis trop bas en Février.

### C. Croston SBA (Pour les ventes rares)
**L'intuition** : "Ne pas prédire de zéros."
Pour un produit qui se vend une fois tous les 3 mois, prédire "0" chaque semaine est statistiquement juste (on a souvent raison) mais commercialement inutile (on ne stocke jamais rien). Croston change la question : au lieu de demander "Combien je vends demain ?", il demande "Quand est la prochaine vente et de quelle taille ?".

**La Mécanique** :
Il sépare l'histoire en deux séries :
1.  **Intervalle ($p$)** : Combien de temps s'écoule entre deux ventes ?
2.  **Demande ($z$)** : Quand une vente a lieu, quelle est sa quantité ?

La prévision devient un "taux d'écoulement" lissé :
$$ \hat{y} = \frac{\text{Moyenne lissée de la Demande}}{\text{Moyenne lissée de l'Intervalle}} $$

**Pourquoi ce choix ?**
C'est le standard industriel pour les pièces détachées et les produits de luxe (Intermittent Demand). Il évite l'effet "dent de scie" des moyennes mobiles sur des zéros.

---

## 3. Le Juge de Paix : Les Métriques

Comment décider qui gagne ? Nous utilisons deux "thermomètres".

### A. WAPE (La Précision Volumétrique)
**Weighted Absolute Percentage Error**
$$ WAPE = \frac{\sum |Réel - Prévision|}{\sum Réel} $$

*   **En français** : Sur l'ensemble des camions que j'ai envoyés, quel pourcentage de la marchandise était une erreur (en trop ou en moins) ?
*   **Pourquoi le WAPE ?** Contrairement au MAPE (pourcentage d'erreur classique), le WAPE ne "explose" pas quand les ventes sont proches de zéro. Il est pondéré par le volume. Une erreur de 10 unités sur un produit qui en vend 1000 (1%) compte moins qu'une erreur de 10 sur un produit qui en vend 10 (100%). C'est ce qui intéresse le directeur logistique.

### B. Le Biais (La Direction de l'Erreur)
$$ Biais = \frac{\sum (Prévision - Réel)}{\sum Réel} $$

*   **En français** : Est-ce que mon modèle est un optimiste pathologique (toujours trop haut) ou un pessimiste (toujours trop bas) ?
*   **Pourquoi vérifier ça ?** Un WAPE excellent (0.05) peut cacher une catastrophe. Si vous sous-estimez systématiquement de 5%, vous allez vider vos stocks et perdre des clients. On cherche un Biais proche de 0.

---

## 4. Notre Stratégie Finale : "L'Hybride Optimisé" (Et son Cerveau Automatique)

Après avoir fait combattre les modèles, nous avons construit le modèle **F_HybridOpt**.
La grande force de ce modèle est qu'il est **100% AUTOMATIQUE**. Personne ne décide "à la main" pour les 3000 produits. C'est un algorithme de classification (basé sur la recherche Syntetos & Boylan) qui agit comme un chef de gare.

### Le Cerveau du Système : ADI et CV² (Les Formules Exactes)
Ces formules sont implémentées ligne 88 dans `src/baselines/optimized.py`.

**1. ADI (Average Demand Interval)**
$$ ADI = \frac{N}{Nz} $$
*   **Dans le code** : `adi = n / nz`
*   **$N$** : Nombre total de semaines d'historique.
*   **$Nz$** : Nombre de semaines où les ventes > 0.
*   *Interprétation* : Un ADI de 1.0 signifie une vente chaque semaine. Un ADI de 4.0 signifie une vente par mois en moyenne.

**2. CV² (Coefficient of Variation Squared)**
$$ CV^2 = \frac{\text{Variance}}{\text{Moyenne}^2} $$
*   **Dans le code** : `cv2 = ynz.var(ddof=0) / (mu ** 2)`
*   Calculé uniquement sur les semaines non-nulles (`ynz`).
*   *Interprétation* : Plus le CV² est haut, plus la volatilité des quantités est extrême.

### La Matrice de Décision (Le "Switch")
Voici comment le script `optimized.py` route *actuellement* les prévisions.
*(Note : Bien que le modèle Croston soit disponible dans `src/baselines/models.py`, nous utilisons ici une **Moyenne Mobile** pour les produits intermittents dans cette version robuste pour garantir la stabilité et la rapidité d'exécution sur 3000 produits).*

| Classe | Définition (Code) | Modèle Appliqué (src/baselines/optimized.py) |
| :--- | :--- | :--- |
| **Smooth** (Stable) | `ADI < 1.32` & `CV² < 0.49` | **0.7 x Moyenne + 0.3 x Saisonnier** (Mix Pondéré) |
| **Erratic** (Nerveux) | `ADI < 1.32` & `CV² >= 0.49` | **0.5 x Moyenne + 0.5 x Saisonnier** (Mix Équilibré) |
| **Intermittent** | `ADI >= 1.32` & `CV² < 0.49` | **Moyenne Mobile (4 sem)** (Approximation Robuste) |
| **Lumpy** (Grumuleux) | `ADI >= 1.32` & `CV² >= 0.49` | **Moyenne Mobile (4 sem)** (Approximation Robuste) |

**Réponse à votre question** :
> *Est-ce vraiment ce qui est dans les fichiers python ?*
> **OUI.** J'ai vérifié le fichier `src/baselines/optimized.py`.
> *   Lignes 103-106 : Le "Switch" `if adi < 1.32 ...` est codé mot pour mot.
> *   Lignes 67-68 : `if dtype in ["intermittent", "lumpy"]: final = pred_ma` confirme que pour l'instant, c'est la Moyenne Mobile qui assure le travail pour les produits intermittents dans la version de production.

**Le Résultat** :
Cette approche nous donne un **WAPE de 0.08**.
Cela signifie que globalement, nous ne nous trompons que de **8%** sur les volumes à expédier. C'est un score excellent pour une "Baseline" sans Intelligence Artificielle complexe.

C'est cette fondation solide qui va nous permettre de construire sereinement la suite (Machine Learning).

---

## 5. Justification : D'où sortent ces chiffres ?

Vous avez raison de demander. Ces seuils (1.32 et 0.49) ne sont pas sortis d'un chapeau.

**1. La Source Scientifique (Théorie)**
Ils proviennent de la publication de référence de **Syntetos & Boylan (2005)**.
*   *Titre* : "The accuracy of intermittent demand estimates".
*   *Découverte* : Leurs recherches ont prouvé mathématiquement que :
    *   Si $ADI < 1.32$, l'erreur de la Moyenne Mobile est inférieure à celle de Croston.
    *   Si $ADI > 1.32$, Croston devient (théoriquement) meilleur.
    *   Le seuil de $CV^2 = 0.49$ distingue ce qui est "prévisible" de ce qui est "bruit pur".

**2. Notre Validation Terrain (Pratique)**
Nous n'avons pas cru la théorie sur parole. Nous l'avons testée sur VOTRE donnée dans le "Master Tournament" (Notebook 04).
*   **Test A** : Seasonal Naive partout -> WAPE = 0.16 (Échec).
*   **Test B** : Moyenne Mobile partout -> WAPE = 0.09 (Mieux).
*   **Test C (Hybride)** : En utilisant ces seuils pour trier -> **WAPE = 0.0838 (Le GAGNANT)**.

**Conclusion** :
Le choix de cette matrice est donc une double sécurité : validée par la recherche académique ET confirmée par la performance réelle sur vos ventes.
