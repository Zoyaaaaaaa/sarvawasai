import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.compose import ColumnTransformer
import pickle
import warnings
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

class RealEstateModelTrainer:
    """Robust trainer for real estate project completion prediction"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.feature_columns = None
        self.feature_medians = None
        self.label_encoders = {}
        self.model = None
        self.preprocessor = None
        
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
    
    def create_target_variable(self):
        """Create target variable from project status"""
        if 'project_status' not in self.df.columns:
            raise ValueError("project_status column not found in data")
        
        # Create binary target
        self.df['target'] = self.df['project_status'].apply(
            lambda x: 1 if 'completed' in str(x).lower() else 0
        )
        
        target_counts = self.df['target'].value_counts()
        logger.info(f"Target distribution: {target_counts.to_dict()}")
        
        # Check for class imbalance
        if min(target_counts) / max(target_counts) < 0.1:
            logger.warning("Severe class imbalance detected. Consider sampling strategies.")
    
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
        
        # Delay calculation (avoid data leakage)
        if 'proposed_date_of_completion' in self.df.columns and 'revised_proposed_date_of_completion' in self.df.columns:
            # Only use revision vs proposed (available at project start)
            self.df['delay_days'] = (
                self.df['revised_proposed_date_of_completion'] - 
                self.df['proposed_date_of_completion']
            ).dt.days
            self.df['delay_days'] = self.df['delay_days'].fillna(0)
            
            # Cap extreme delays (10 years max)
            self.df['delay_days'] = self.df['delay_days'].clip(lower=0, upper=3650)
            
            # Create delay categories
            self.df['delay_category'] = pd.cut(
                self.df['delay_days'],
                bins=[-1, 0, 90, 365, 3650],
                labels=['No_Delay', 'Short_Delay', 'Medium_Delay', 'Long_Delay']
            )
        
        # Parse coordinates
        if 'location_lat_long' in self.df.columns:
            def parse_coordinates(coord_str):
                if pd.isna(coord_str):
                    return np.nan, np.nan
                try:
                    # Pattern for ('lat', 'lng')
                    import re
                    pattern = r"\('([\d\.-]+)',\s*'([\d\.-]+)'\)"
                    match = re.search(pattern, str(coord_str))
                    if match:
                        return float(match.group(1)), float(match.group(2))
                    
                    # Pattern for lat,lng
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
            # Avoid division by zero
            self.df['booking_percentage'] = (
                self.df['number_of_booked_appartments'] / 
                self.df['number_of_appartments'].replace(0, 1)
            ) * 100
            self.df['booking_percentage'] = self.df['booking_percentage'].fillna(0).clip(0, 100)
            
            # Booking category
            self.df['booking_category'] = pd.cut(
                self.df['booking_percentage'],
                bins=[0, 25, 50, 75, 100],
                labels=['Low', 'Medium', 'High', 'Very_High'],
                include_lowest=True
            )
        
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
        
        logger.info("Feature engineering completed")
    
    def prepare_features(self):
        """Prepare features for modeling"""
        logger.info("Preparing features for modeling...")
        
        # Columns to exclude from features
        exclude_columns = [
            'target',
            'project_status',
            'proposed_date_of_completion',
            'revised_proposed_date_of_completion', 
            'extended_date_of_completion',
            'date_last_modified',
            'location_lat_long'  # Keep parsed coordinates
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
            # Cap outliers at 1st and 99th percentiles
            if self.df[col].notna().sum() > 0:
                lower_bound = self.df[col].quantile(0.01)
                upper_bound = self.df[col].quantile(0.99)
                self.df[col] = self.df[col].clip(lower=lower_bound, upper=upper_bound)
        
        # Handle categorical features
        for col in categorical_cols:
            # Fill nulls and convert to string
            self.df[col] = self.df[col].astype(str).replace('nan', 'Unknown')
            
            # Combine rare categories
            value_counts = self.df[col].value_counts()
            rare_categories = value_counts[value_counts < 10].index
            self.df[col] = self.df[col].replace(rare_categories, 'Other')
            
            # Create and fit label encoder
            le = LabelEncoder()
            self.df[col] = le.fit_transform(self.df[col])
            self.label_encoders[col] = le
        
        # Store feature information
        self.feature_columns = feature_cols
        self.feature_medians = self.df[numeric_cols].median().to_dict()
        
        # Fill remaining nulls in numeric columns
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
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        # Create pipeline with robust scaling
        self.model = Pipeline([
            ('scaler', RobustScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1
            ))
        ])
        
        # Train model
        logger.info("Training Random Forest model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='accuracy')
        logger.info(f"Cross-validation accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Feature importance
        feature_importance = self.model.named_steps['classifier'].feature_importances_
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 10 Most Important Features:")
        for idx, row in importance_df.head(10).iterrows():
            logger.info(f"{row['feature']}: {row['importance']:.4f}")
        
        return {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': importance_df
        }
    
    def hyperparameter_tuning(self, X_train, y_train):
        """Perform hyperparameter tuning"""
        logger.info("Starting hyperparameter tuning...")
        
        param_grid = {
            'classifier__n_estimators': [100, 200, 300],
            'classifier__max_depth': [10, 15, 20, None],
            'classifier__min_samples_split': [2, 5, 10],
            'classifier__min_samples_leaf': [1, 2, 4]
        }
        
        base_pipeline = Pipeline([
            ('scaler', RobustScaler()),
            ('classifier', RandomForestClassifier(random_state=42, n_jobs=-1))
        ])
        
        grid_search = GridSearchCV(
            base_pipeline,
            param_grid,
            cv=3,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best cross-validation score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def save_model_artifacts(self, output_dir="."):
        """Save all model artifacts"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
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
        
        # Save feature importance if available
        if hasattr(self.model.named_steps['classifier'], 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.named_steps['classifier'].feature_importances_
            }).sort_values('importance', ascending=False)
            
            importance_df.to_csv(output_path / "feature_importance.csv", index=False)
            logger.info("Saved feature_importance.csv")
        
        logger.info(f"All artifacts saved to {output_path}")
    
    def validate_model(self, sample_data=None):
        """Validate model with sample predictions"""
        logger.info("Validating model...")
        
        if sample_data is None and len(self.df) > 0:
            # Use a few samples from training data
            sample_data = self.df[self.feature_columns].head(3)
        
        if sample_data is not None:
            try:
                predictions = self.model.predict(sample_data)
                probabilities = self.model.predict_proba(sample_data)
                
                logger.info("Sample predictions successful:")
                for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                    logger.info(f"Sample {i+1}: Prediction={pred}, Probabilities={prob}")
                
                return True
            except Exception as e:
                logger.error(f"Model validation failed: {e}")
                return False
        
        return True

def main():
    """Main training pipeline"""
    logger.info("Starting Real Estate Project Completion Model Training")
    
    # Initialize trainer
    trainer = RealEstateModelTrainer("mumbai_rera.csv")
    
    try:
        # Load and clean data
        trainer.load_and_clean_data()
        
        # Create target variable
        trainer.create_target_variable()
        
        # Feature engineering
        trainer.feature_engineering()
        
        # Train model
        results = trainer.train_model()
        
        # Validate model
        if trainer.validate_model():
            logger.info("Model validation passed")
        else:
            logger.warning("Model validation failed")
        
        # Save artifacts
        trainer.save_model_artifacts()
        
        logger.info("Training pipeline completed successfully!")
        logger.info(f"Final model accuracy: {results['accuracy']:.4f}")
        
        return trainer, results
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    trainer, results = main()