import pandas as pd
import numpy as np
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from category_encoders import TargetEncoder
import xgboost as xgb
import lightgbm as lgb
import shap
import pickle
import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def train_model(processed_data_path, output_dir):
    logging.info(f"Loading processed data from {processed_data_path}")
    df = pd.read_csv(processed_data_path)
    
    # Define features and target
    # We drop 'Price_per_SqFt' because it leaks the target 'Price'
    target = 'Price'
    drop_cols = ['Price', 'Price_per_SqFt']
    features = [col for col in df.columns if col not in drop_cols]
    
    X = df[features]
    y = df[target]
    
    logging.info(f"Features: {features}")
    
    # Stage 4: Train-test split (70% Train, 15% Val, 15% Test)
    X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=0.1765, random_state=42) # 0.15 / 0.85 approx 0.1765
    
    logging.info(f"Split sizes: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Stage 2 (cont): Converting Location (Target Encoding)
    # We fit only on training data
    encoder = TargetEncoder(cols=['Location'])
    X_train_encoded = encoder.fit_transform(X_train, y_train)
    X_val_encoded = encoder.transform(X_val)
    X_test_encoded = encoder.transform(X_test)
    
    # Stage 5: Baseline Model (XGBoost)
    logging.info("Training XGBoost model...")
    model = xgb.XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )
    
    model.fit(
        X_train_encoded, y_train,
        eval_set=[(X_val_encoded, y_val)],
        verbose=100
    )
    
    # Stage 5: Evaluation
    def evaluate(m, X_eval, y_eval, name):
        preds = m.predict(X_eval)
        mae = mean_absolute_error(y_eval, preds)
        mape = mean_absolute_percentage_error(y_eval, preds)
        r2 = r2_score(y_eval, preds)
        logging.info(f"Performance - {name}: MAE=₹{mae:,.0f}, MAPE={mape:.2%}, R2={r2:.4f}")
        return mae, mape
    
    evaluate(model, X_train_encoded, y_train, "Train")
    evaluate(model, X_val_encoded, y_val, "Validation")
    test_mae, test_mape = evaluate(model, X_test_encoded, y_test, "Test")
    
    # Stage 6: Explainability
    logging.info("Generating SHAP values...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_encoded)
    
    # Save SHAP summary plot (optional, but good for Stage 6)
    # plt.figure(figsize=(10, 6))
    # shap.summary_plot(shap_values, X_test_encoded, show=False)
    # plt.savefig(os.path.join(output_dir, "shap_summary.png"))
    
    # Feature Importance (Standard)
    importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    logging.info(f"Feature Importance:\n{importance}")
    
    # Stage 8: Package the model and preprocessing pipeline
    os.makedirs(output_dir, exist_ok=True)
    
    artifacts = {
        'model': model,
        'encoder': encoder,
        'features': features,
        'test_metrics': {'mae': test_mae, 'mape': test_mape}
    }
    
    artifact_path = os.path.join(output_dir, "house_prediction_v1.pkl")
    with open(artifact_path, 'wb') as f:
        pickle.dump(artifacts, f)
    
    logging.info(f"Artifacts saved to {artifact_path}")
    return artifact_path

if __name__ == "__main__":
    data_path = r"c:\Users\ASUS\Documents\MPR FINAL\backend\app\ml_pipeline\data\mumbai_data_processed.csv"
    output_folder = r"c:\Users\ASUS\Documents\MPR FINAL\backend\app\ml_pipeline\artifacts"
    train_model(data_path, output_folder)
