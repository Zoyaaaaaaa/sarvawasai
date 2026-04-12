import pandas as pd
import numpy as np
import os
import logging
from sklearn.preprocessing import StandardScaler
from category_encoders import TargetEncoder
import pickle

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("preprocessing.log"),
        logging.StreamHandler()
    ]
)

def run_pre_processing(input_path, output_dir):
    logging.info(f"Starting preprocessing for {input_path}")
    
    # Stage 1: Data sanity check
    df = pd.read_csv(input_path)
    
    # Drop index column if it exists (first column often unnamed in CSV exports)
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    elif df.columns[0] == '':
        df = df.drop(columns=[df.columns[0]])

    logging.info(f"Initial shape: {df.shape}")
    
    # 1.1 Duplicate listings
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        logging.info(f"Found {duplicates} duplicate listings. Dropping them.")
        df = df.drop_duplicates()
    
    # 1.2 Missing values
    missing = df.isnull().sum()
    logging.info(f"Missing values per column:\n{missing[missing > 0]}")
    
    # Drop rows where critical info is missing
    critical_cols = ['Price', 'Area', 'Location', 'No. of Bedrooms']
    df = df.dropna(subset=critical_cols)
    
    # 1.3 Outlier checks (Price and Area)
    # Mumbai prices can be high, but let's check for impossible values
    # e.g. Price < 1 Lakh or Area < 100 sq ft or No. of Bedrooms > 10 (unless area is massive)
    initial_len = len(df)
    df = df[df['Price'] > 100000] # > 1 Lakh
    df = df[df['Area'] > 100] # > 100 sq ft
    df = df[df['No. of Bedrooms'] < 10]
    logging.info(f"Dropped {initial_len - len(df)} rows due to outlier/impossible values.")
    
    # 1.4 Binary consistency
    binary_cols = ['New/Resale', 'Gymnasium', 'Lift Available', 'Car Parking', 'Maintenance Staff', 
                   '24x7 Security', 'Children\'s Play Area', 'Clubhouse', 'Intercom', 
                   'Landscaped Gardens', 'Indoor Games', 'Gas Connection', 'Jogging Track', 'Swimming Pool']
    
    for col in binary_cols:
        if col in df.columns:
            invalid = df[~df[col].isin([0, 1])]
            if len(invalid) > 0:
                logging.warning(f"Column {col} has non-binary values. Imputing with mode.")
                df.loc[~df[col].isin([0, 1]), col] = df[col].mode()[0]
    
    # 1.5 Location Normalization
    # Strip whitespace, title case, and remove redundant "Sector" prefix if it just complicates
    df['Location'] = df['Location'].str.strip()
    # Basic normalization: "Kharghar" is often the base.
    # We'll keep it simple for now, but ensure consistency.
    logging.info(f"Number of unique locations before normalization: {df['Location'].nunique()}")
    # Example: "Kharghar" vs "Sector-13 Kharghar"
    # For now, let's just make sure casing is consistent
    df['Location'] = df['Location'].str.title()
    logging.info(f"Number of unique locations after normalization: {df['Location'].nunique()}")

    # Stage 2: Cleaning and normalization
    # Missing values handled above via dropping critical ones.
    # For amenities, if missing, we'll assume 0.
    df[binary_cols] = df[binary_cols].fillna(0).astype(int)

    # Stage 3: Feature engineering
    logging.info("Starting feature engineering")
    
    # 3.1 Price per square foot
    df['Price_per_SqFt'] = df['Price'] / df['Area']
    
    # 3.2 Bedroom density (Area per bedroom)
    # Avoid division by zero
    df['Area_per_Bedroom'] = df['Area'] / df['No. of Bedrooms'].replace(0, 1)
    
    # 3.3 Amenity Score
    amenity_cols = ['Gymnasium', 'Lift Available', 'Car Parking', 'Maintenance Staff', 
                    '24x7 Security', 'Children\'s Play Area', 'Clubhouse', 'Intercom', 
                    'Landscaped Gardens', 'Indoor Games', 'Gas Connection', 'Jogging Track', 'Swimming Pool']
    df['Amenity_Score'] = df[amenity_cols].sum(axis=1)
    
    # Stage 2 (cont): Target Encoding for Location
    # We do NOT do this here as it requires a train-test split to avoid leakage.
    # We will save the cleaning logic and the engineered (raw) features.
    
    # Save the processed data
    os.makedirs(output_dir, exist_ok=True)
    processed_path = os.path.join(output_dir, "mumbai_data_processed.csv")
    df.to_csv(processed_path, index=False)
    logging.info(f"Saved processed data to {processed_path}")
    
    return df

if __name__ == "__main__":
    input_file = r"c:\Users\ASUS\Documents\MPR FINAL\backend\app\ml_pipeline\data\mumbai_data_raw.csv"
    output_folder = r"c:\Users\ASUS\Documents\MPR FINAL\backend\app\ml_pipeline\data"
    run_pre_processing(input_file, output_folder)
