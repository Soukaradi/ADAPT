# FIXED: Realistic 2025 E-Commerce Channel Economics

CHANNELS = {
    "Amazon": {
        "type": "Marketplace",
        "referral_fee": 0.15,      # 15% platform commission
        "closing_fee": 30,          # Fixed fee per order
        "shipping_base": 35,        # Bulk ship to Amazon FC
        "traffic_score": 0.50,      # High organic reach - can handle 50% of inventory
        "marketing_cac": 0.05       # 5% of revenue for sponsored ads
    },
    "Flipkart": {
        "type": "Marketplace",
        "referral_fee": 0.13,       # 13% platform commission
        "closing_fee": 20,          # Lower fixed fee
        "shipping_base": 35,        # Similar FC shipping
        "traffic_score": 0.40,      # Medium organic reach - up to 40%
        "marketing_cac": 0.06       # 6% for ads
    },
    "Own_Website": {
        "type": "D2C",
        "referral_fee": 0.03,       # Only payment gateway fees (2-3%)
        "closing_fee": 0,           # No marketplace fees
        "shipping_base": 50,        # Last-mile delivery cost
        "traffic_score": 0.35,      # Lower organic reach - needs heavy marketing
        "marketing_cac": 0.20       # 20% CAC for paid acquisition (Google/Meta ads)
    }
}

# Warehouse candidates for expansion analysis
WAREHOUSE_CANDIDATES = {
    "North_Delhi": {"rent": 35, "lat": 28.61, "lon": 77.23, "type": "Main"},
    "West_Mumbai": {"rent": 45, "lat": 19.07, "lon": 72.87, "type": "Main"},
    "South_Bangalore": {"rent": 40, "lat": 12.97, "lon": 77.59, "type": "Regional"},
    "East_Kolkata": {"rent": 25, "lat": 22.57, "lon": 88.36, "type": "Regional"},
    "Central_Hyderabad": {"rent": 30, "lat": 17.38, "lon": 78.48, "type": "Regional"}
}

# Regional demand zones for shipping calculations
ZONES = {
    "North": {"lat": 28.7, "lon": 77.1}, 
    "West": {"lat": 19.0, "lon": 72.8},
    "South": {"lat": 12.9, "lon": 77.5}, 
    "East": {"lat": 22.5, "lon": 88.3}
}