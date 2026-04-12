import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import pickle
import warnings
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

class RealEstateRiskModelTrainer:
    """Train model to predict project risk (not completion) for ongoing projects"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.feature_columns = None
        self.feature_medians = None
        self.label_encoders = {}
        self.model = None
        
    def load_and_clean_data(self):
        """Load and perform initial cleaning"""
        logger.info(f"Loading data from {self.data_path}")
        
        try:
            self.df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self.df)} rows, {len(self.df.columns)} columns")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        
        # Remove duplicates
        initial_rows = len(self.df)
        self.df.drop_duplicates(inplace=True)
        logger.info(f"Removed {initial_rows - len(self.df)} duplicate rows")
        
        # Replace various null representations
        null_values = ["", "NA", "NaN", "nan", "null", "NULL", None, "N/A", "n/a"]
        self.df.replace(null_values, np.nan, inplace=True)
        
        # Remove columns with too many nulls (>80%)
        null_threshold = 0.8
        high_null_cols = self.df.columns[self.df.isnull().mean() > null_threshold].tolist()
        if high_null_cols:
            logger.info(f"Dropping columns with >{null_threshold*100}% nulls: {high_null_cols}")
            self.df.drop(columns=high_null_cols, inplace=True)
        
        # Handle infinite values
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        logger.info(f"After cleaning: {len(self.df)} rows, {len(self.df.columns)} columns")
        logger.info(f"Project statuses: {self.df['project_status'].value_counts().to_dict()}")
    
    def create_risk_target(self):
        """Create risk-based target variable using multiple indicators"""
        logger.info("Creating risk-based target variable...")
        
        # Initialize risk score
        risk_score = pd.Series(0, index=self.df.index)
        risk_factors = []
        
        # Factor 1: Delay (most important)
        if 'proposed_date_of_completion' in self.df.columns and 'revised_proposed_date_of_completion' in self.df.columns:
            self.df['proposed_date_of_completion'] = pd.to_datetime(self.df['proposed_date_of_completion'], errors='coerce')
            self.df['revised_proposed_date_of_completion'] = pd.to_datetime(self.df['revised_proposed_date_of_completion'], errors='coerce')
            
            delay_days = (self.df['revised_proposed_date_of_completion'] - self.df['proposed_date_of_completion']).dt.days
            
            # High risk if delayed > 180 days (6 months)
            risk_score += (delay_days > 180).fillna(False).astype(int) * 3
            risk_factors.append('delay')
            
            logger.info(f"Projects with delay > 180 days: {(delay_days > 180).sum()}")
        
        # Factor 2: Low booking rate
        if 'number_of_appartments' in self.df.columns and 'number_of_booked_appartments' in self.df.columns:
            booking_rate = (self.df['number_of_booked_appartments'] / self.df['number_of_appartments'].replace(0, 1)) * 100
            
            # High risk if booking < 30%
            risk_score += (booking_rate < 30).fillna(False).astype(int) * 2
            risk_factors.append('low_booking')
            
            logger.info(f"Projects with booking < 30%: {(booking_rate < 30).sum()}")
            logger.info(f"Booking rate stats:\n{booking_rate.describe()}")
        
        # Factor 3: Large project size (harder to complete)
        if 'number_of_appartments' in self.df.columns:
            large_project = self.df['number_of_appartments'] > 100
            risk_score += large_project.fillna(False).astype(int) * 1
            risk_factors.append('large_size')
            
            logger.info(f"Large projects (>100 units): {large_project.sum()}")
        
        # Factor 4: Extended deadlines
        if 'extended_date_of_completion' in self.df.columns:
            self.df['extended_date_of_completion'] = pd.to_datetime(self.df['extended_date_of_completion'], errors='coerce')
            has_extension = self.df['extended_date_of_completion'].notna()
            risk_score += has_extension.astype(int) * 2
            risk_factors.append('has_extension')
            
            logger.info(f"Projects with extended deadlines: {has_extension.sum()}")
        
        # Factor 5: New projects (less predictable)
        if 'project_status' in self.df.columns:
            is_new = self.df['project_status'] == 'New Project'
            risk_score += is_new.astype(int) * 1
            risk_factors.append('new_project')
            
            logger.info(f"New projects: {is_new.sum()}")
        
        logger.info(f"Risk factors considered: {risk_factors}")
        logger.info(f"Risk score distribution:\n{risk_score.value_counts().sort_index()}")
        
        # Create binary target: High risk (1) vs Low risk (0)
        # Use median or threshold-based split
        risk_threshold = risk_score.median()
        self.df['target'] = (risk_score >= risk_threshold).astype(int)
        
        target_counts = self.df['target'].value_counts()
        logger.info(f"\nTarget distribution (0=Low Risk, 1=High Risk):\n{target_counts}")
        logger.info(f"Class balance: {target_counts[1]}/{target_counts[0]} = {target_counts[1]/target_counts[0]:.2f}")
        
        # Verify we have both classes
        if len(target_counts) < 2:
            logger.error("CRITICAL: Still only one class after risk scoring!")
            logger.error("Trying alternative risk threshold...")
            
            # Try quartile-based split
            risk_threshold = risk_score.quantile(0.6)
            self.df['target'] = (risk_score >= risk_threshold).astype(int)
            target_counts = self.df['target'].value_counts()
            logger.info(f"Alternative target distribution:\n{target_counts}")
            
            if len(target_counts) < 2:
                raise ValueError("Cannot create two classes even with risk-based approach")
        
        # Store risk score for analysis
        self.df['risk_score'] = risk_score
    
    def feature_engineering(self):
        """Comprehensive feature engineering"""
        logger.info("Starting feature engineering...")
        
        # Date processing
        date_columns = [
            'proposed_date_of_completion',
            'revised_proposed_date_of_completion',
            'extended_date_of_completion',
            'date_last_modified'
        ]
        
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        # Delay calculation
        if 'proposed_date_of_completion' in self.df.columns and 'revised_proposed_date_of_completion' in self.df.columns:
            self.df['delay_days'] = (
                self.df['revised_proposed_date_of_completion'] - 
                self.df['proposed_date_of_completion']
            ).dt.days
            self.df['delay_days'] = self.df['delay_days'].fillna(0).clip(lower=0, upper=3650)
            
            # Create delay categories
            self.df['delay_category'] = pd.cut(
                self.df['delay_days'],
                bins=[-1, 0, 90, 365, 3650],
                labels=['No_Delay', 'Short_Delay', 'Medium_Delay', 'Long_Delay']
            )
            
            logger.info(f"Delay statistics:\n{self.df['delay_days'].describe()}")
        
        # Days until proposed completion
        if 'proposed_date_of_completion' in self.df.columns:
            self.df['days_until_completion'] = (
                self.df['proposed_date_of_completion'] - pd.Timestamp.now()
            ).dt.days
            self.df['days_until_completion'] = self.df['days_until_completion'].fillna(0)
            
            # Is overdue?
            self.df['is_overdue'] = (self.df['days_until_completion'] < 0).astype(int)
        
        # Parse coordinates
        if 'location_lat_long' in self.df.columns:
            def parse_coordinates(coord_str):
                if pd.isna(coord_str):
                    return np.nan, np.nan
                try:
                    import re
                    pattern = r"\('([\d\.-]+)',\s*'([\d\.-]+)'\)"
                    match = re.search(pattern, str(coord_str))
                    if match:
                        return float(match.group(1)), float(match.group(2))
                    
                    if ',' in str(coord_str):
                        parts = str(coord_str).split(',')
                        if len(parts) == 2:
                            return float(parts[0].strip()), float(parts[1].strip())
                    
                    return np.nan, np.nan
                except:
                    return np.nan, np.nan
            
            coords = self.df['location_lat_long'].apply(parse_coordinates)
            self.df['latitude'] = [coord[0] for coord in coords]
            self.df['longitude'] = [coord[1] for coord in coords]
        
        # Booking metrics
        if 'number_of_appartments' in self.df.columns and 'number_of_booked_appartments' in self.df.columns:
            self.df['booking_percentage'] = (
                self.df['number_of_booked_appartments'] / 
                self.df['number_of_appartments'].replace(0, 1)
            ) * 100
            self.df['booking_percentage'] = self.df['booking_percentage'].fillna(0).clip(0, 100)
            
            self.df['booking_category'] = pd.cut(
                self.df['booking_percentage'],
                bins=[0, 25, 50, 75, 100],
                labels=['Low', 'Medium', 'High', 'Very_High'],
                include_lowest=True
            )
            
            # Number of unboooked apartments
            self.df['unbooked_apartments'] = (
                self.df['number_of_appartments'] - self.df['number_of_booked_appartments']
            ).fillna(0)
            
            logger.info(f"Booking percentage stats:\n{self.df['booking_percentage'].describe()}")
        
        # Area per apartment
        if 'project_area_(sqmts)' in self.df.columns and 'number_of_appartments' in self.df.columns:
            self.df['area_per_apartment'] = (
                self.df['project_area_(sqmts)'] / 
                self.df['number_of_appartments'].replace(0, 1)
            )
            self.df['area_per_apartment'] = self.df['area_per_apartment'].fillna(0)
        
        # Location clustering
        if 'district' in self.df.columns and 'location_pin_code' in self.df.columns:
            self.df['location_cluster'] = (
                self.df['district'].astype(str) + "_" + 
                self.df['location_pin_code'].astype(str)
            )
        
        # Project size categories
        if 'number_of_appartments' in self.df.columns:
            self.df['project_size'] = pd.cut(
                self.df['number_of_appartments'].fillna(0),
                bins=[0, 10, 50, 100, 500, float('inf')],
                labels=['Very_Small', 'Small', 'Medium', 'Large', 'Very_Large'],
                include_lowest=True
            )
        
        # Has extension flag
        if 'extended_date_of_completion' in self.df.columns:
            self.df['has_extension'] = self.df['extended_date_of_completion'].notna().astype(int)
        
        logger.info("Feature engineering completed")
    
    def prepare_features(self):
        """Prepare features for modeling"""
        logger.info("Preparing features for modeling...")
        
        # Columns to exclude from features
        exclude_columns = [
            'target',
            'risk_score',
            'project_status',
            'proposed_date_of_completion',
            'revised_proposed_date_of_completion', 
            'extended_date_of_completion',
            'date_last_modified',
            'location_lat_long'
        ]
        
        # Get feature columns
        feature_cols = [col for col in self.df.columns if col not in exclude_columns]
        
        # Separate numeric and categorical columns
        numeric_cols = self.df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df[feature_cols].select_dtypes(include=['object', 'category']).columns.tolist()
        
        logger.info(f"Numeric features: {len(numeric_cols)}")
        logger.info(f"Categorical features: {len(categorical_cols)}")
        
        # Handle numeric features
        for col in numeric_cols:
            if self.df[col].notna().sum() > 0:
                lower_bound = self.df[col].quantile(0.01)
                upper_bound = self.df[col].quantile(0.99)
                self.df[col] = self.df[col].clip(lower=lower_bound, upper=upper_bound)
        
        # Handle categorical features
        for col in categorical_cols:
            self.df[col] = self.df[col].astype(str).replace('nan', 'Unknown')
            
            value_counts = self.df[col].value_counts()
            rare_categories = value_counts[value_counts < 10].index
            self.df[col] = self.df[col].replace(rare_categories, 'Other')
            
            le = LabelEncoder()
            self.df[col] = le.fit_transform(self.df[col])
            self.label_encoders[col] = le
        
        # Store feature information
        self.feature_columns = feature_cols
        self.feature_medians = self.df[numeric_cols].median().to_dict()
        
        # Fill remaining nulls
        for col in numeric_cols:
            self.df[col] = self.df[col].fillna(self.feature_medians[col])
        
        logger.info(f"Feature preparation completed. Total features: {len(feature_cols)}")
        
        return feature_cols
    
    def train_model(self, test_size=0.2, random_state=42):
        """Train the prediction model"""
        logger.info("Starting model training...")
        
        # Prepare features and target
        feature_cols = self.prepare_features()
        X = self.df[feature_cols]
        y = self.df['target']
        
        logger.info(f"Training with {len(X)} samples and {len(feature_cols)} features")
        logger.info(f"Target distribution (0=Low Risk, 1=High Risk): {y.value_counts().to_dict()}")
        
        # Verify we have both classes
        unique_classes = y.unique()
        logger.info(f"Unique classes in target: {unique_classes}")
        
        if len(unique_classes) < 2:
            raise ValueError(f"ERROR: Only {len(unique_classes)} class(es) found. Cannot train binary classifier.")
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"Train set: {len(X_train)} samples, classes: {y_train.value_counts().to_dict()}")
        logger.info(f"Test set: {len(X_test)} samples, classes: {y_test.value_counts().to_dict()}")
        
        # Create pipeline
        self.model = Pipeline([
            ('scaler', RobustScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=random_state,
                n_jobs=-1
            ))
        ])
        
        # Train model
        logger.info("Training Random Forest model...")
        self.model.fit(X_train, y_train)
        
        # Verify model has both classes
        classifier = self.model.named_steps['classifier']
        logger.info(f"Model classes after training: {classifier.classes_}")
        
        if len(classifier.classes_) < 2:
            raise ValueError(f"ERROR: Model only learned {len(classifier.classes_)} class(es)!")
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)
        
        logger.info(f"Prediction probabilities shape: {y_proba.shape}")
        logger.info(f"Sample probabilities:\n{y_proba[:5]}")
        
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred, target_names=['Low Risk', 'High Risk']))
        
        # Feature importance
        feature_importance = classifier.feature_importances_
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 15 Most Important Features:")
        for idx, row in importance_df.head(15).iterrows():
            logger.info(f"{row['feature']}: {row['importance']:.4f}")
        
        return {
            'accuracy': accuracy,
            'feature_importance': importance_df
        }
    
    def save_model_artifacts(self, output_dir="."):
        """Save all model artifacts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Verify model before saving
        classifier = self.model.named_steps['classifier']
        logger.info(f"Saving model with classes: {classifier.classes_}")
        
        artifacts = {
            "rera_project_pipeline_refined.pkl": self.model,
            "feature_columns.pkl": self.feature_columns,
            "feature_medians.pkl": self.feature_medians,
            "label_encoders.pkl": self.label_encoders
        }
        
        for filename, artifact in artifacts.items():
            filepath = output_path / filename
            with open(filepath, "wb") as f:
                pickle.dump(artifact, f)
            logger.info(f"Saved {filename}")
        
        # Save feature importance
        if hasattr(self.model.named_steps['classifier'], 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.named_steps['classifier'].feature_importances_
            }).sort_values('importance', ascending=False)
            
            importance_df.to_csv(output_path / "feature_importance.csv", index=False)
            logger.info("Saved feature_importance.csv")
        
        logger.info(f"All artifacts saved to {output_path}")

def main():
    """Main training pipeline"""
    logger.info("="*60)
    logger.info("Starting Real Estate Project RISK Prediction Model Training")
    logger.info("(Predicting: High Risk vs Low Risk for ongoing projects)")
    logger.info("="*60)
    
    trainer = RealEstateRiskModelTrainer("mumbai_rera.csv")
    
    try:
        trainer.load_and_clean_data()
        trainer.create_risk_target()  # Changed from create_target_variable
        trainer.feature_engineering()
        results = trainer.train_model()
        trainer.save_model_artifacts()
        
        logger.info("="*60)
        logger.info("Training pipeline completed successfully!")
        logger.info(f"Final model accuracy: {results['accuracy']:.4f}")
        logger.info("Model predicts: 0=Low Risk, 1=High Risk")
        logger.info("="*60)
        
        return trainer, results
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    trainer, results = main()