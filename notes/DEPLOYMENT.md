# Guide de Déploiement Cloud

Ce document explique comment déployer l'application Retail Forecasting Assistant sur différentes plateformes cloud.

## Architecture de Déploiement

L'application est conçue pour un déploiement cloud avec les caractéristiques suivantes :
- **Données brutes** : Incluses dans le dépôt GitHub (119 MB)
- **Base de données** : Construite à la demande via l'interface utilisateur
- **Processus** : L'utilisateur clique sur "Initialiser la Base de Données" au premier lancement

## Déploiement sur Streamlit Cloud (Recommandé)

### Prérequis
- Compte GitHub avec le dépôt `retail-demand-forecasting-assistant`
- Compte Streamlit Cloud (gratuit) : https://streamlit.io/cloud

### Étapes

1. **Connecter Streamlit Cloud à GitHub**
   - Aller sur https://share.streamlit.io/
   - Cliquer sur "New app"
   - Autoriser l'accès à votre dépôt GitHub

2. **Configurer l'application**
   - Repository : `BeediGoua/retail-demand-forecasting-assistant`
   - Branch : `main`
   - Main file path : `app/Home.py`

3. **Paramètres avancés (optionnel)**
   - Python version : `3.10`
   - Augmenter la mémoire si nécessaire (Settings > Resources)

4. **Déployer**
   - Cliquer sur "Deploy"
   - Attendre 2-3 minutes pour le déploiement initial

### Premier Lancement

1. L'application affichera : "⚠️ La base de données n'est pas encore initialisée"
2. Cliquer sur le bouton "🚀 Initialiser la Base de Données"
3. Attendre 2-3 minutes pendant la construction
4. L'application se rechargera automatiquement avec les statistiques

### Limitations Streamlit Cloud (Plan Gratuit)
- **Mémoire** : 1 GB RAM (peut être juste pour la construction de la DB)
- **CPU** : Partagé
- **Stockage** : Temporaire (la DB sera reconstruite à chaque redémarrage du conteneur)

**Solution** : Pour éviter de reconstruire à chaque fois, envisager un plan payant ou utiliser une base de données externe (PostgreSQL).

---

## Déploiement sur Heroku

### Prérequis
- Compte Heroku : https://www.heroku.com/
- Heroku CLI installé

### Fichiers nécessaires

Créer un fichier `Procfile` à la racine :
```
web: streamlit run app/Home.py --server.port=$PORT --server.address=0.0.0.0
```

Créer un fichier `runtime.txt` :
```
python-3.10.12
```

### Commandes de déploiement

```bash
# Login Heroku
heroku login

# Créer l'application
heroku create retail-forecasting-assistant

# Pousser le code
git push heroku main

# Ouvrir l'application
heroku open
```

### Configuration Heroku

```bash
# Augmenter la mémoire (Dyno Standard - $25/mois)
heroku ps:resize web=standard-1x

# Voir les logs
heroku logs --tail
```

---

## Déploiement sur Render

### Prérequis
- Compte Render : https://render.com/

### Étapes

1. **Créer un nouveau Web Service**
   - Connecter le dépôt GitHub
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `streamlit run app/Home.py --server.port=$PORT --server.address=0.0.0.0`

2. **Configuration**
   - Environment : `Python 3`
   - Plan : Free (512 MB RAM) ou Starter ($7/mois pour 1 GB)

3. **Variables d'environnement** (optionnel)
   - Aucune nécessaire pour l'instant

---

## Optimisations pour Production

### 1. Base de Données Persistante

Pour éviter de reconstruire la DB à chaque redémarrage, utiliser une base externe :

**Option A : PostgreSQL Cloud**
- Modifier `scripts/build_warehouse.py` pour utiliser PostgreSQL au lieu de SQLite
- Utiliser un service comme Supabase (gratuit) ou Heroku Postgres

**Option B : Stockage Cloud**
- Uploader `retail.sqlite` sur Google Drive / Dropbox
- Télécharger au démarrage de l'app si absent localement

### 2. Cache Streamlit

Ajouter dans `app/Home.py` :
```python
@st.cache_resource
def get_database_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
```

### 3. Monitoring

Ajouter des logs pour suivre l'utilisation :
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

## Dépannage

### Erreur : "Out of Memory"
- Augmenter la RAM du plan (Streamlit Cloud : Settings > Resources)
- Ou optimiser le script de preprocessing pour traiter les données par batch

### Erreur : "Database locked"
- SQLite n'est pas conçu pour le multi-utilisateur
- Solution : Migrer vers PostgreSQL

### L'app redémarre souvent
- Normal sur les plans gratuits (inactivité > 15 min)
- La DB sera reconstruite à chaque fois
- Solution : Plan payant ou DB externe

---

## Résumé des Coûts

| Plateforme | Plan Gratuit | Plan Payant | Recommandation |
|------------|--------------|-------------|----------------|
| **Streamlit Cloud** | 1 GB RAM, DB temporaire | $20/mois (4 GB RAM) | Idéal pour demo |
| **Heroku** | Limité (512 MB) | $7-25/mois | Bon pour prod |
| **Render** | 512 MB RAM | $7/mois (1 GB) | Bon compromis |

**Recommandation** : Commencer avec Streamlit Cloud (gratuit) pour la démo, puis migrer vers Render ou Heroku pour la production.
