import joblib
import pandas as pd
from pipeline.allocation import allocate_portfolio

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "model1_lwv.pkl")

model1 = joblib.load(model_path)

features_model1 = [
    'AGE', 'EDUC', 'MARRIED', 'KIDS', 'SAVED',
    'STOCKS', 'WEALTH_RATIO', 'LIQUIDITY_RATIO'
]

def predict(user_input):

    df = pd.DataFrame([user_input])

    # --- Derived features ---
    df['WEALTH_RATIO'] = df['ASSET'] / (df['INCOME'] + 1e-6)
    df['LIQUIDITY_RATIO'] = df['LIQ'] / (df['ASSET'] + 1e-6)
    df['DEBT_RATIO'] = df['DEBT'] / (df['INCOME'] + 1e-6)

    # --- Model 1 ---
    investor_type = model1.predict(df[features_model1])[0]

    # --- Allocation ---
    allocation = allocate_portfolio(
        investor_type=investor_type,
        age=df['AGE'].iloc[0],
        wealth_ratio=df['WEALTH_RATIO'].iloc[0],
        debt_ratio=df['DEBT_RATIO'].iloc[0],
        liquidity_ratio=df['LIQUIDITY_RATIO'].iloc[0],
        emergency_savings=df['EMERGSAV'].iloc[0]
    )

    return {
        "investor_type": int(investor_type),
        "allocation": allocation
    }