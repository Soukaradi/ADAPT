import numpy as np

def run_eoq_advanced(annual_demand, price, holding_pct, ordering_cost):
    EPSILON = 1e-9
    if annual_demand <= 0: annual_demand = EPSILON
    
    H = price * (holding_pct / 100.0)
    if H <= 0: H = 0.01
    
    EOQ = int(np.sqrt((2 * annual_demand * ordering_cost) / H))
    if EOQ == 0: EOQ = 1
    
    avg_inv = EOQ / 2
    holding_cost = avg_inv * H
    ord_cost = (annual_demand / EOQ) * ordering_cost
    total_cost = holding_cost + ord_cost
    
    q_splits = [0.15, 0.25, 0.20, 0.40] # Q4 Peak
    q_names = ["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]
    q_plan = []
    
    for i, split in enumerate(q_splits):
        dem = int(annual_demand * split)
        batches = int(np.ceil(dem/EOQ))
        q_plan.append({
            "Quarter": q_names[i],
            "Seasonality": "Peak" if split > 0.25 else "Standard", # THIS KEY IS CRITICAL
            "Demand": dem,
            "Batches": batches,
            "Capital": int(batches * EOQ * price)
        })
    
    return {
        "EOQ": EOQ,
        "metrics": {
            "Holding": int(holding_cost), 
            "Ordering": int(ord_cost), 
            "Total": int(total_cost),
            "Capital": int(avg_inv * price)
        },
        "quarterly_plan": q_plan
    }