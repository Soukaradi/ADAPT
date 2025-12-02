import numpy as np
from pulp import *
from . import data_manager

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def optimize_network(hist_df, annual_demand):
    """
    Network Simulation: Should we open a Regional Hub?
    Analyzes demand gravity.
    """
    # 1. Analyze where demand comes from
    region_counts = hist_df['region'].value_counts(normalize=True)
    
    scenarios = {}
    
    # Scenario A: 1 Hub (Delhi Main)
    # Own Site Logic: Ship from Delhi -> All India (High Distance)
    # Marketplace Logic: Ship Bulk Delhi -> FC (Low Cost)
    avg_dist_1 = 0
    for reg, share in region_counts.items():
        d = haversine(28.6, 77.2, data_manager.ZONES[reg]['lat'], data_manager.ZONES[reg]['lon'])
        avg_dist_1 += d * share
    
    cost_1 = 35 * 5000 * 12 # Rent
    ship_1 = annual_demand * (50 + avg_dist_1 * 0.02) # Own Site shipping is pricey
    
    scenarios['1 Hub (Delhi)'] = {"rent": int(cost_1), "shipping": int(ship_1), "total": int(cost_1+ship_1)}
    
    # Scenario B: 2 Hubs (Delhi + Bangalore)
    # If demand in South is > 30%, this should trigger
    south_share = region_counts.get('South', 0)
    
    avg_dist_2 = 0
    for reg, share in region_counts.items():
        # Ship from nearest
        d1 = haversine(28.6, 77.2, data_manager.ZONES[reg]['lat'], data_manager.ZONES[reg]['lon']) # Delhi
        d2 = haversine(12.9, 77.6, data_manager.ZONES[reg]['lat'], data_manager.ZONES[reg]['lon']) # BLR
        avg_dist_2 += min(d1, d2) * share
        
    cost_2 = (35 * 5000 * 12) + (40 * 4000 * 12) # Rent for both
    ship_2 = annual_demand * (50 + avg_dist_2 * 0.02) # Lower shipping
    
    scenarios['2 Hubs (Delhi + BLR)'] = {"rent": int(cost_2), "shipping": int(ship_2), "total": int(cost_2+ship_2)}
    
    best = min(scenarios, key=lambda k: scenarios[k]['total'])
    return scenarios, best

def solve_channel_mix(inventory, price, strategy="balanced"):
    channels = data_manager.CHANNELS
    prob = LpProblem("Mix", LpMaximize)
    vars = LpVariable.dicts("Q", channels.keys(), 0, None, LpInteger)
    
    financials = {}
    margins = {}
    
    for ch, f in channels.items():
        # --- THE HYBRID COST LOGIC ---
        if f['type'] == "Marketplace":
            # Amazon/Flipkart: Bulk ship to FC + Platform Fees
            logistics = f['ship_to_fc'] + f['fba_fee']
            marketing = price * f['cac_load']
            fees = price * f['referral'] + f['closing']
        else:
            # Own Site: Last Mile Shipping + High Marketing
            logistics = f['shipping_base'] 
            marketing = price * f['cac_load']
            fees = price * f['referral'] # Just gateway
            
        cost = fees + logistics + marketing
        profit = price - cost
        
        margins[ch] = profit
        financials[ch] = {"Revenue": price, "Fees": fees, "Logistics": logistics, "Marketing": marketing, "Net Profit": profit}
        
    # Objective: Profit Max
    if strategy == "brand":
        # Weighted Objective: Value D2C sales 1.5x (Customer Data Value)
        prob += lpSum([vars[ch] * margins[ch] * f.get('brand_equity', 1.0) for ch in channels])
    else:
        prob += lpSum([vars[ch] * margins[ch] for ch in channels])

    # Constraints
    prob += lpSum([vars[ch] for ch in channels]) <= inventory
    
    # Demand Caps
    for ch, f in channels.items():
        prob += vars[ch] <= inventory * f['traffic_score']
        
    prob.solve(PULP_CBC_CMD(msg=0))
    
    alloc = {ch: int(vars[ch].varValue) for ch in channels}
    total_profit = sum([alloc[ch] * margins[ch] for ch in channels])
    
    return {"allocation": alloc, "profit": int(total_profit), "financials": financials}