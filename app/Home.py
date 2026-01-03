import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Retail Forecasting Assistant", page_icon="🛒", layout="wide")

st.title("🛒 Retail Forecasting & Inventory Assistant")

DB_PATH = "data/retail.sqlite"

@st.cache_data
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    try:
        n_stores = pd.read_sql("SELECT COUNT(*) FROM dim_store", conn).iloc[0,0]
        n_families = pd.read_sql("SELECT COUNT(*) FROM dim_family", conn).iloc[0,0]
        n_weeks = pd.read_sql("SELECT COUNT(*) FROM dim_week", conn).iloc[0,0]
        return n_stores, n_families, n_weeks
    except Exception as e:
        return 0, 0, 0
    finally:
        conn.close()

stores, families, weeks = get_stats()

col1, col2, col3 = st.columns(3)
col1.metric("Magasins", stores)
col2.metric("Familles Produits", families)
col3.metric("Semaines Historiques", weeks)

st.divider()

st.markdown("""
### Bienvenue !
Cette application est l'interface de pilotage de votre assistant Retail.

**État du système :**
- ✅ **Data Warehouse** : Connecté (`retail.sqlite`)
- 🏗️ **Modèles** : En attente d'entraînement
- 📉 **Prévisions** : Non disponibles

Utilisez le menu latéral pour naviguer (Fonctionnalités à venir).
""")
