"""
Script de setup complet du projet
Télécharge les données et construit la base de données
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("SETUP - Retail Forecasting Assistant")
    print("=" * 60)
    
    # Vérifier si les données brutes existent
    raw_data = Path("data/raw")
    train_file = raw_data / "train.csv"
    
    if not train_file.exists():
        print("\n[1/3] Téléchargement des données depuis Kaggle...")
        print("Assurez-vous d'avoir configuré Kaggle CLI (pip install kaggle)")
        print("Commande à exécuter manuellement :")
        print("  kaggle competitions download -c store-sales-time-series-forecasting")
        print("  unzip store-sales-time-series-forecasting.zip -d data/raw/")
        print("\nOu téléchargez manuellement depuis :")
        print("  https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data")
        return
    
    print("\n[2/3] Traitement des données (Preprocessing)...")
    result = subprocess.run([sys.executable, "scripts/preprocessing.py"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERREUR: {result.stderr}")
        return
    print("OK - Fichiers Parquet générés")
    
    print("\n[3/3] Construction de la base de données (Data Warehouse)...")
    result = subprocess.run([sys.executable, "scripts/build_warehouse.py"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERREUR: {result.stderr}")
        return
    print("OK - retail.sqlite créé")
    
    print("\n" + "=" * 60)
    print("SETUP TERMINÉ AVEC SUCCÈS")
    print("=" * 60)
    print("\nVous pouvez maintenant lancer l'application :")
    print("  streamlit run app/Home.py")

if __name__ == "__main__":
    main()
