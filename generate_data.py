import pandas as pd
import numpy as np
import datetime

def generate_file(filename, days, products):
    """
    Generates realistic e-commerce sales data aligned with analytics.py expectations.
    """
    print(f"Generating {filename} ({days} days, {len(products)} products)...")
    start_date = datetime.date(2023, 1, 1)
    date_list = [start_date + datetime.timedelta(days=x) for x in range(days)]
    
    all_data = []
    
    # REALISTIC Historical Channel Mix (Inefficient - Heavy Marketplace Dependency)
    channels = ["Amazon", "Flipkart", "Own_Website"]
    channel_weights = [0.55, 0.35, 0.10]  # Heavy Amazon, low D2C
    
    # Regional Distribution (North-heavy due to single warehouse)
    regions = ["North", "West", "South", "East"]
    region_weights = [0.35, 0.30, 0.20, 0.15]
    
    for date in date_list:
        day_of_year = date.timetuple().tm_yday
        day_of_week = date.weekday()
        
        # Seasonal Patterns
        # Q1 (Jan-Mar): Standard
        # Q2 (Apr-Jun): Summer peak (cricket season, fitness)
        # Q3 (Jul-Sep): Monsoon dip + back-to-school
        # Q4 (Oct-Dec): FESTIVE PEAK (Diwali, New Year)
        
        if 274 <= day_of_year <= 365:  # Q4 (Oct-Dec) - FESTIVE PEAK
            seasonal_multiplier = 2.8
        elif 90 <= day_of_year <= 180:  # Q2 (Apr-Jun) - Summer
            seasonal_multiplier = 1.4
        elif 180 <= day_of_year <= 273:  # Q3 (Jul-Sep) - Monsoon
            seasonal_multiplier = 0.9
        else:  # Q1 (Jan-Mar) - Standard
            seasonal_multiplier = 1.0
        
        # Weekend boost (Sat-Sun)
        weekend_boost = 1.3 if day_of_week >= 5 else 1.0
        
        # Year-over-year growth (realistic 15-20% annual growth)
        years_elapsed = (date - start_date).days / 365.0
        growth_trend = 1.0 + (years_elapsed * 0.18)  # 18% annual growth
        
        for prod_id, prod_info in products.items():
            # Base daily volume
            base_volume = prod_info['base_vol']
            
            # Product-specific seasonality
            if prod_info.get('season') == 'summer' and 90 <= day_of_year <= 180:
                product_season = 1.5
            elif prod_info.get('season') == 'festive' and 274 <= day_of_year <= 365:
                product_season = 2.0
            elif prod_info.get('season') == 'cricket' and 30 <= day_of_year <= 150:
                product_season = 1.8
            else:
                product_season = 1.0
            
            # Random daily variation (±25%)
            daily_noise = np.random.normal(1.0, 0.25)
            
            # Calculate total daily demand
            daily_demand = base_volume * growth_trend * seasonal_multiplier * weekend_boost * product_season * daily_noise
            daily_demand = int(max(0, daily_demand))
            
            if daily_demand > 0:
                # Split demand across channels
                channel_splits = np.random.multinomial(daily_demand, channel_weights)
                
                for ch_idx, qty in enumerate(channel_splits):
                    if qty > 0:
                        channel = channels[ch_idx]
                        
                        # REALISTIC Ad Spend (Historical = Inefficient)
                        # Own Website: Very high CAC (20-25% of revenue) - paid acquisition
                        # Amazon: Medium CAC (5-8% of revenue) - sponsored products
                        # Flipkart: Medium CAC (6-9% of revenue) - ads
                        
                        if channel == "Own_Website":
                            ad_cac_pct = np.random.uniform(0.20, 0.25)  # 20-25% - EXPENSIVE
                        elif channel == "Amazon":
                            ad_cac_pct = np.random.uniform(0.05, 0.08)  # 5-8%
                        else:  # Flipkart
                            ad_cac_pct = np.random.uniform(0.06, 0.09)  # 6-9%
                        
                        ad_spend = qty * prod_info['price'] * ad_cac_pct
                        
                        # Regional distribution
                        region = np.random.choice(regions, p=region_weights)
                        
                        # Price variation (±5% for promotions/discounts)
                        actual_price = prod_info['price'] * np.random.uniform(0.95, 1.05)
                        
                        all_data.append([
                            date,
                            prod_id,
                            round(actual_price, 2),
                            qty,
                            channel,
                            region,
                            round(ad_spend, 2)
                        ])
    
    # Create DataFrame
    df = pd.DataFrame(all_data, columns=[
        'date', 
        'product_id', 
        'price', 
        'quantity_sold', 
        'channel', 
        'region', 
        'ad_spend'
    ])
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Save
    df.to_csv(filename, index=False)
    
    # Print statistics
    print(f"[OK] Created {filename}")
    print(f"   - Records: {len(df):,}")
    print(f"   - Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"   - Total Revenue: Rs.{(df['price'] * df['quantity_sold']).sum():,.0f}")
    print(f"   - Channel Mix: {df.groupby('channel')['quantity_sold'].sum().to_dict()}")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("GENERATING REALISTIC E-COMMERCE SALES DATA")
    print("=" * 70)
    print()
    
    # Test Dataset (60 days - for quick testing)
    print("1. TEST DATASET")
    print("-" * 70)
    generate_file(
        "sales_data_small.csv", 
        60, 
        {
            "TEST_SHOE": {
                "base_vol": 15, 
                "price": 2000, 
                "season": "flat"
            }
        }
    )
    
    # Realistic Multi-Product Dataset (2 years)
    print("2. PRODUCTION DATASET")
    print("-" * 70)
    realistic_products = {
        "PRO_RUN_SHOES": {
            "base_vol": 50,      # 50 units/day baseline
            "price": 2500,       # Rs.2,500
            "season": "summer"   # Peak in summer months
        },
        "CRICKET_JERSEY": {
            "base_vol": 25,
            "price": 1200,
            "season": "cricket"  # Peak during cricket season (Jan-May)
        },
        "SMART_WATCH": {
            "base_vol": 35,
            "price": 4500,
            "season": "festive"  # Peak during Diwali/New Year
        },
        "YOGA_MAT": {
            "base_vol": 40,
            "price": 1500,
            "season": "flat"     # Consistent year-round
        },
        "FITNESS_BAND": {
            "base_vol": 45,
            "price": 3000,
            "season": "festive"
        }
    }
    
    generate_file("sales_data_realistic.csv", 730, realistic_products)
    
    print("=" * 70)
    print("[OK] DATA GENERATION COMPLETE!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Upload 'sales_data_realistic.csv' to the web interface")
    print("2. Select product or 'All Products'")
    print("3. Run strategy optimization")
    print()