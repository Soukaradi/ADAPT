import numpy as np
from pulp import *
import data_manager  # Direct import instead of relative

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def optimize_network(df, annual_demand):
    """Simulates Network Expansion with realistic cost modeling."""
    if 'region' not in df.columns:
        region_counts = {"North": 0.3, "West": 0.3, "South": 0.2, "East": 0.2}
    else:
        region_counts = df['region'].value_counts(normalize=True)
        
    zones = data_manager.ZONES
    warehouses = data_manager.WAREHOUSE_CANDIDATES
    
    scores = {}
    for name, specs in warehouses.items():
        dist = 0
        w_lat, w_lon = specs['lat'], specs['lon']
        for reg, share in region_counts.items():
            r_lat = zones.get(reg, zones['North'])['lat']
            r_lon = zones.get(reg, zones['North'])['lon']
            dist += haversine(w_lat, w_lon, r_lat, r_lon) * share
        scores[name] = (specs['rent'] * 1000) + (dist * 50)
        
    ranked = sorted(scores, key=scores.get)
    
    results = {}
    for n in [1, 2, 3]:
        hubs = ranked[:n]
        rent = sum([warehouses[h]['rent']*2000*12 for h in hubs])
        
        if n == 1:
            avg_shipping_per_unit = 50
        elif n == 2:
            avg_shipping_per_unit = 32
        else:
            avg_shipping_per_unit = 28
            
        shipping = annual_demand * avg_shipping_per_unit
        
        results[n] = {
            "hubs": hubs, 
            "rent": int(rent), 
            "shipping": int(shipping), 
            "total": int(rent + shipping)
        }
    
    best_n = min(results, key=lambda k: results[k]['total'])
    return results, best_n

def solve_channel_mix(inventory, price, strategy="profit"):
    """LP Solver that maximizes profit with realistic constraints."""
    if inventory <= 0: 
        inventory = 100
    
    channels = data_manager.CHANNELS
    prob = LpProblem("ChannelMix", LpMaximize)
    vars = LpVariable.dicts("Q", channels.keys(), 0, None, LpInteger)
    
    margins = {}
    financials = {}
    
    for ch, f in channels.items():
        fees = (price * f['referral_fee']) + f['closing_fee']
        
        if f['type'] == 'Marketplace':
            logistics = 32
        else:
            logistics = 40
        
        marketing = price * f['marketing_cac']
        contribution = price - (fees + logistics + marketing)
        margins[ch] = contribution
        
        financials[ch] = {
            "Revenue": price,
            "Fees": fees,
            "Logistics": logistics,
            "Marketing": marketing,
            "Contribution": contribution
        }
    
    if strategy == "brand":
        prob += lpSum([
            vars[ch] * margins[ch] * (1.3 if ch == "Own_Website" else 1.0) 
            for ch in channels
        ])
    elif strategy == "balanced":
        prob += lpSum([
            vars[ch] * margins[ch] * (1.1 if ch == "Own_Website" else 1.0)
            for ch in channels
        ])
    else:
        prob += lpSum([vars[ch] * margins[ch] for ch in channels])
    
    prob += lpSum([vars[ch] for ch in channels]) == inventory, "Total_Inventory"
    prob += vars["Amazon"] <= inventory * 0.55, "Amazon_Cap"
    prob += vars["Flipkart"] <= inventory * 0.45, "Flipkart_Cap"
    prob += vars["Own_Website"] <= inventory * 0.40, "Own_Website_Cap"
    prob += vars["Own_Website"] >= inventory * 0.18, "Own_Website_Min"
    prob += vars["Amazon"] >= inventory * 0.10, "Amazon_Min"
    prob += vars["Flipkart"] >= inventory * 0.10, "Flipkart_Min"
    
    prob.solve(PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        alloc = {ch: int(vars[ch].varValue) for ch in channels}
        total_contribution = value(prob.objective)
    else:
        print(f"[WARNING] LP Solver failed with status {prob.status}. Using fallback allocation.")
        alloc = {
            "Amazon": int(inventory * 0.45),
            "Flipkart": int(inventory * 0.35),
            "Own_Website": int(inventory * 0.20)
        }
        total_contribution = sum([alloc[ch] * margins[ch] for ch in channels])
    
    return {
        "allocation": alloc, 
        "profit": int(total_contribution),
        "financials": financials
    }