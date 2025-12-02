import pandas as pd
import numpy as np
from prophet import Prophet
from pmdarima import auto_arima
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

def sMAPE(y_true, y_pred):
    return 100 * np.mean(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred) + 1e-9))

def create_features(df):
    df = df.copy()
    df['dayofweek'] = df.index.dayofweek
    df['month'] = df.index.month
    df['lag_30'] = df['y'].shift(30).fillna(0)
    return df

def run_tournament(df, product_id, growth_rate_input):
    """
    UPDATED: Accepts growth_rate_input (percentage).
    """
    if product_id != "ALL_PRODUCTS":
        df = df[df['product_id'] == product_id].copy()
    
    df = df.groupby('date').agg({'quantity_sold': 'sum', 'ad_spend': 'mean'}).reset_index()
    df.columns = ['ds', 'y', 'ad_spend']
    
    train = df.iloc[:-60]
    test = df.iloc[-60:]
    predictions = {}
    errors = {}
    
    growth_multiplier = 1 + (growth_rate_input / 100.0)
    
    # 1. Prophet
    try:
        m = Prophet()
        m.add_regressor('ad_spend')
        m.fit(train)
        fut = test[['ds', 'ad_spend']]
        p = m.predict(fut)['yhat'].values
        predictions['Prophet'] = p.tolist()
        errors['Prophet'] = sMAPE(test['y'], p)
        
        # Future
        future = m.make_future_dataframe(periods=365)
        future['ad_spend'] = df['ad_spend'].mean() * growth_multiplier # Scale ad spend too
        fc = m.predict(future)
        
        # APPLY USER GROWTH HERE
        future_curve = (fc['yhat'].tail(365).clip(lower=0) * growth_multiplier).astype(int).tolist()
        future_dates = fc['ds'].tail(365).dt.strftime('%Y-%m-%d').tolist()
    except: 
        predictions['Prophet'] = [0]*60; errors['Prophet'] = 100.0
        future_curve = [0]*365; future_dates = []

    # 2. XGBoost
    try:
        tr = create_features(train.set_index('ds'))
        te = create_features(test.set_index('ds'))
        cols = ['dayofweek','month','lag_30','ad_spend']
        m = xgb.XGBRegressor(n_estimators=100)
        m.fit(tr[cols], tr['y'])
        p = m.predict(te[cols])
        predictions['XGBoost'] = p.tolist()
        errors['XGBoost'] = sMAPE(test['y'], p)
    except:
        predictions['XGBoost'] = [0]*60; errors['XGBoost'] = 100.0

    # 3. ARIMA
    try:
        m_ar = auto_arima(train['y'], seasonal=False, error_action='ignore')
        p_ar = m_ar.predict(n_periods=60)
        predictions['ARIMA'] = p_ar.tolist()
        errors['ARIMA'] = sMAPE(test['y'], p_ar)
    except: 
        predictions['ARIMA'] = [0]*60; errors['ARIMA'] = 100.0

    winner = min(errors, key=errors.get)
    annual_demand = int(sum(future_curve))
    
    return {
        "test_dates": test['ds'].dt.strftime('%Y-%m-%d').tolist(),
        "test_actuals": test['y'].tolist(),
        "predictions": predictions,
        "errors": errors,
        "winner": winner,
        "annual_demand": annual_demand,
        "future_curve": future_curve,
        "future_dates": future_dates
    }