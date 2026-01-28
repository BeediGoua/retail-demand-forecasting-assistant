import pandas as pd
import numpy as np
import os

def run_analysis():
    print("--- STARTING DASHBOARD RESEARCH ---")
    
    # 1. Load Data
    try:
        # Adjustment for script execution: src/dashboard -> src -> root -> data/raw
        base_path = os.path.join(os.path.dirname(__file__), '../../data/raw')
        
        train = pd.read_csv(os.path.join(base_path, 'train.csv'), parse_dates=['date'])
        oil = pd.read_csv(os.path.join(base_path, 'oil.csv'), parse_dates=['date'])
        
        print("Data Loaded Successfully.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Merge Oil
    df = train.merge(oil, on='date', how='left')
    
    # 2. Payday Effect (Day of Month)
    print("\n[ANALYSIS] Payday Effect (15th and 30th)")
    df['day'] = df['date'].dt.day
    daily_avg = df.groupby('day')['sales'].mean()
    
    # Check spikes
    avg_sales = daily_avg.mean()
    payday_15 = daily_avg.get(15, 0)
    payday_30 = daily_avg.get(30, 0) # Month end can be 30 or 31, let's check 30/31 peak
    payday_31 = daily_avg.get(31, 0)
    payday_end = max(payday_30, payday_31)
    
    print(f"Average Daily Sales: {avg_sales:,.0f}")
    print(f"Sales on 15th: {payday_15:,.0f} (Lift: {(payday_15/avg_sales - 1)*100:.1f}%)")
    print(f"Sales on Month End: {payday_end:,.0f} (Lift: {(payday_end/avg_sales - 1)*100:.1f}%)")
    
    if payday_15 > avg_sales * 1.1:
        print(">> INSIGHT: Strong Payday Effect detected on the 15th.")
    else:
        print(">> INSIGHT: Weak/No Payday Effect on the 15th.")

    # 3. Promotion Impact (Top Families)
    print("\n[ANALYSIS] Promotion Impact (Top 5 Families)")
    top_families = df.groupby('family')['sales'].sum().nlargest(5).index.tolist()
    
    for fam in top_families:
        fam_df = df[df['family'] == fam].copy() # Copy to avoid SettingWithCopy
        # Handle nan in onpromotion
        fam_df['onpromotion'] = fam_df['onpromotion'].fillna(0)
        
        corr = fam_df['sales'].corr(fam_df['onpromotion'])
        
        # Calculate lift: Mean Sales when OnPromo > 0 vs OnPromo == 0
        mean_promo = fam_df[fam_df['onpromotion'] > 0]['sales'].mean()
        mean_no_promo = fam_df[fam_df['onpromotion'] == 0]['sales'].mean()
        # Handle division by zero or NaN
        if pd.isna(mean_no_promo) or mean_no_promo == 0:
             lift = 0
        else:
             lift = (mean_promo / mean_no_promo - 1) * 100
             
        print(f"Family: {fam:<30} | Corr: {corr:.2f} | Promo Uplift: +{lift:.1f}%")

    # 4. Oil Impact (Macro)
    print("\n[ANALYSIS] Oil Price Correlation")
    # Resample to weekly to capture trend
    weekly_df = df.set_index('date').resample('W').agg({'sales': 'sum', 'dcoilwtico': 'mean'}).dropna()
    
    oil_corr = weekly_df['sales'].corr(weekly_df['dcoilwtico'])
    print(f"Weekly Sales vs Oil Price Correlation: {oil_corr:.3f}")
    
    if abs(oil_corr) > 0.5:
        print(">> INSIGHT: Significant correlation with Oil Prices.")
    else:
        print(">> INSIGHT: Oil prices do not directly drive short-term retail sales.")

if __name__ == "__main__":
    run_analysis()
