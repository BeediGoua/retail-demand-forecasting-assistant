import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import sys
from pathlib import Path

st.set_page_config(
    page_title="Retail Forecasting Assistant", 
    layout="wide"
)

DB_PATH = Path("data/retail.sqlite")
RAW_DATA_PATH = Path("data/raw/train.csv")

def check_database_exists():
    """Vérifie si la base de données existe et est valide"""
    if not DB_PATH.exists():
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_sales_weekly")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False

def check_raw_data_exists():
    """Vérifie si les données brutes sont présentes"""
    return RAW_DATA_PATH.exists()

def build_database():
    """Lance le pipeline de construction de la base de données"""
    with st.spinner("Étape 1/2 : Traitement des données (peut prendre 2-3 minutes)..."):
        result = subprocess.run(
            [sys.executable, "scripts/preprocessing.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            st.error(f"Erreur lors du preprocessing : {result.stderr}")
            return False
    
    with st.spinner("Étape 2/2 : Construction de la base de données..."):
        result = subprocess.run(
            [sys.executable, "scripts/build_warehouse.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            st.error(f"Erreur lors du build : {result.stderr}")
            return False
    
    return True

@st.cache_data
def get_stats():
    """Récupère les statistiques de la base de données"""
    conn = sqlite3.connect(DB_PATH)
    try:
        n_stores = pd.read_sql("SELECT COUNT(*) FROM dim_store", conn).iloc[0,0]
        n_families = pd.read_sql("SELECT COUNT(*) FROM dim_family", conn).iloc[0,0]
        n_weeks = pd.read_sql("SELECT COUNT(*) FROM dim_week", conn).iloc[0,0]
        n_sales_records = pd.read_sql("SELECT COUNT(*) FROM fact_sales_weekly", conn).iloc[0,0]
        return n_stores, n_families, n_weeks, n_sales_records
    except Exception as e:
        return 0, 0, 0, 0
    finally:
        conn.close()

# Interface principale
st.title("Retail Forecasting & Inventory Assistant")
st.markdown("**Assistant d'aide à la décision pour l'optimisation des stocks**")

st.divider()

# Vérification de l'état du système
db_exists = check_database_exists()
raw_data_exists = check_raw_data_exists()

if not db_exists:
    st.warning("La base de données n'est pas encore initialisée")
    
    if not raw_data_exists:
        st.error("Données brutes manquantes")
        st.markdown("""
        Les fichiers CSV bruts sont introuvables dans `data/raw/`.
        
        **Pour les obtenir** :
        1. Télécharger depuis Kaggle : https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data
        2. Placer les fichiers dans le dossier `data/raw/`
        """)
    else:
        st.success("Données brutes détectées (119 MB)")
        
        st.markdown("""
        ### Initialisation de la Base de Données
        
        Cliquez sur le bouton ci-dessous pour construire la base de données.
        
        **Ce processus va** :
        1. Nettoyer et transformer les données brutes
        2. Créer les agrégations hebdomadaires
        3. Construire le Data Warehouse SQL (315 MB)
        
        **Durée estimée** : 2-3 minutes
        """)
        
        if st.button("Initialiser la Base de Données", type="primary", use_container_width=True):
            if build_database():
                st.success("Base de données créée avec succès !")
                st.balloons()
                st.rerun()
            else:
                st.error("Échec de la construction. Consultez les logs ci-dessus.")
else:
    st.success("Système opérationnel")
    
    # Affichage des statistiques
    stores, families, weeks, sales_records = get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Magasins", stores)
    col2.metric("Familles Produits", families)
    col3.metric("Semaines Historiques", weeks)
    col4.metric("Enregistrements Ventes", f"{sales_records:,}")
    
    st.divider()
    
    st.markdown("""
    ### État du Système
    
    - **Data Warehouse** : Connecté (`retail.sqlite`)
    - **Modèles** : En attente d'entraînement
    - **Prévisions** : Non disponibles
    
    ### Prochaines Étapes
    
    Utilisez le menu latéral pour naviguer vers :
    - **Exploration des Données** : Visualiser les tendances historiques
    - **Modélisation** : Entraîner les modèles de prévision
    - **Décisions Stock** : Générer les recommandations de commande
    
    *(Fonctionnalités en développement)*
    """)
    
    # Option de reconstruction
    with st.expander("Options Avancées"):
        st.warning("Attention : Cette action va supprimer et reconstruire la base de données")
        if st.button("Reconstruire la Base de Données"):
            if DB_PATH.exists():
                DB_PATH.unlink()
            st.rerun()
