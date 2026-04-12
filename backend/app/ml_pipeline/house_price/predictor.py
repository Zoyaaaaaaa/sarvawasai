import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path

try:
    from ...core.paths import resolve_artifact  # type: ignore
except Exception:
    try:
        from app.core.paths import resolve_artifact  # type: ignore
    except Exception:
        from core.paths import resolve_artifact  # type: ignore

class HousePredictor:
    def __init__(self, artifact_path=None):
        if artifact_path is None:
            artifact_path = resolve_artifact(
                "house_prediction_v1.pkl",
                Path(__file__).resolve().parent / "artifacts" / "house_prediction_v1.pkl",
            )
        
        with open(artifact_path, 'rb') as f:
            artifacts = pickle.load(f)
            
        self.model = artifacts['model']
        self.encoder = artifacts['encoder']
        self.features = artifacts['features']
        self.amenity_cols = [
            'Gymnasium', 'Lift Available', 'Car Parking', 'Maintenance Staff', 
            '24x7 Security', "Children's Play Area", 'Clubhouse', 'Intercom', 
            'Landscaped Gardens', 'Indoor Games', 'Gas Connection', 'Jogging Track', 'Swimming Pool'
        ]

    def predict(self, input_data: dict):
        """
        input_data: {
            'Area': 1000,
            'Location': 'Kharghar',
            'No. of Bedrooms': 2,
            'New/Resale': 0,
            'Gymnasium': 1,
            ... (other amenities)
        }
        """
        df = pd.DataFrame([input_data])
        
        # Preprocessing: Amenity Score
        # Ensure all amenity columns exist in input_data, default to 0
        for col in self.amenity_cols:
            if col not in df.columns:
                df[col] = 0
                
        df['Amenity_Score'] = df[self.amenity_cols].sum(axis=1)
        
        # 3.2 Bedroom density (Area per bedroom)
        # Avoid division by zero
        df['Area_per_Bedroom'] = df['Area'] / df['No. of Bedrooms'].replace(0, 1)
        
        # Location normalization
        df['Location'] = df['Location'].str.strip().str.title()
        
        # Target Encoding
        df_encoded = self.encoder.transform(df)
        
        # Reorder columns to match training
        df_final = df_encoded[self.features]
        
        # Ensure all columns are numeric (TargetEncoder should have handled this)
        # but just in case, ensure no objects remain
        for col in df_final.columns:
            if df_final[col].dtype == 'object':
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

        # XGBoost can be picky about feature names when loaded from cross-versions
        try:
            # First try predicting with DataFrame
            prediction = self.model.predict(df_final)[0]
        except Exception as e:
            msg = str(e)
            if "feature names" in msg or "expected" in msg:
                # Fallback: Use the booster directly if sklearn interface is failing
                try:
                    import xgboost as xgb
                    dmatrix = xgb.DMatrix(df_final.values, feature_names=self.features)
                    prediction = self.model.get_booster().predict(dmatrix)[0]
                except:
                    # Final fallback: just use values
                    prediction = self.model.predict(df_final.values)[0]
            else:
                raise e
        
        # Generate raw insights for LLM
        insights = {
            'predicted_price': float(prediction),
            'amenity_score': int(df['Amenity_Score'].iloc[0]),
            'location': input_data['Location'],
            'area': input_data['Area'],
            'bedrooms': input_data['No. of Bedrooms']
        }
        
        return insights

if __name__ == "__main__":
    # Test prediction
    predictor = HousePredictor()
    test_input = {
        'Area': 980,
        'Location': 'Kharghar',
        'No. of Bedrooms': 2,
        'New/Resale': 0,
        'Gymnasium': 1,
        'Lift Available': 1,
        'Car Parking': 1,
        'Maintenance Staff': 1,
        '24x7 Security': 1,
        'Children\'s Play Area': 0,
        'Clubhouse': 1,
        'Intercom': 1,
        'Landscaped Gardens': 0,
        'Indoor Games': 1,
        'Gas Connection': 0,
        'Jogging Track': 1,
        'Swimming Pool': 1
    }
    print(predictor.predict(test_input))
