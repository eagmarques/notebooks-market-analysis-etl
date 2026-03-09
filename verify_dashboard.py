import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.dashboard.data_loader import load_data, prepare_data, calculate_kpis, generate_insights
from src.dashboard.charts import build_demand_distribution_chart

def verify():
    # Setup paths
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "data" / "analytics" / "mercadolivre.db"
    table_name = "notebooks"
    
    print(f"--- Verifying Data Layer ---")
    try:
        df = load_data(db_path, table_name)
        print(f"Loaded {len(df)} rows from DB.")
        
        prep_df = prepare_data(df)
        print("Data preparation successful.")
        print(f"Columns: {prep_df.columns.tolist()}")
        print(f"Price buckets: {prep_df['price_bucket'].unique().tolist()}")
        print(f"Demand levels: {prep_df['demand_level'].unique().tolist()}")
        
        kpis = calculate_kpis(prep_df)
        print(f"KPIs: {kpis}")
        
        insights = generate_insights(prep_df)
        print("Insights generated:")
        for i in insights:
            print(f"- {i}")
            
        print("\n--- Verifying Visualization Layer (Sample) ---")
        fig = build_demand_distribution_chart(prep_df)
        print("Chart figure created successfully.")
        
    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
