"""
Trains a Random Forest model for Mumbai house prices.
"""

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)

# LOAD DATA
df = pd.read_csv("backend/app/ml_pipeline/data/mumbai-house-price-data-cleaned.csv")

# drop unused columns
df = df.drop(["title", "price_per_sqft"], axis=1)

X = df.drop("price", axis=1)
y = df["price"]

# COLUMN TYPES
cat_cols = X.select_dtypes(include="object").columns
num_cols = X.select_dtypes(exclude="object").columns

# PREPROCESSING PIPELINE
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", "passthrough", num_cols),
    ]
)

# TRAIN / TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# MODEL
model = Pipeline(
    steps=[
        ("prep", preprocessor),
        (
            "rf",
            RandomForestRegressor(
                n_estimators=120,
                max_depth=20,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)

# TRAIN
model.fit(X_train, y_train)

# EVALUATION
preds = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, preds))
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print("\nModel Performance")
print("--------------------")
print("R2   :", round(r2, 4))
print("MAE  :", round(mae))
print("RMSE :", round(rmse))

# SAVE MODEL
joblib.dump(model, "/Users/urjabahad/SarvAwas-Ai-1/backend/app/ml_pipeline/stepup/models/spatial_random_forest2.pkl", compress=3)

print("\nModel saved to models/spatial_random_forest.pkl")