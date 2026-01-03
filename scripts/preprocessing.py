from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path so we can import from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.make_dataset import generate_sales_dataset
from src.data.make_calendar import generate_calendar_dataset

def main():
    print("---------------------------------------------------")
    print("STARTING PREPROCESSING PIPELINE")
    print("---------------------------------------------------")
    
    # 1. Generate Sales Data (Daily & Weekly)
    print("\n[Step 1/2] Generating Sales Datasets (Daily Grid & Weekly Agg)")
    try:
        generate_sales_dataset()
        print("PASS: Sales datasets generated successfully.")
    except Exception as e:
        print(f"ERROR: generating sales datasets: {e}")
        sys.exit(1)
        
    # 2. Generate Calendar Dimension
    print("\n[Step 2/2] Generating Calendar Dimension")
    try:
        generate_calendar_dataset()
        print("PASS: Calendar dimension generated successfully.")
    except Exception as e:
        print(f"ERROR: generating calendar: {e}")
        sys.exit(1)
        
    print("\n---------------------------------------------------")
    print("PIPELINE COMPLETED SUCCESSFULLY") 
    print("Output Files:")
    print("- data/processed/weekly_canon.parquet (Source of Truth)")
    print("- data/processed/dim_calendar.parquet (Reference)")
    print("- data/processed/daily_canon.parquet (Backup)")
    print("---------------------------------------------------")

if __name__ == "__main__":
    main()
