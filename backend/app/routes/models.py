# from pathlib import Path
# import pickle
# import re
# from typing import Any, Dict, List, Optional
# import logging

# from fastapi import HTTPException
# import pandas as pd
# from pydantic import BaseModel, Field, validator

# # Set up logger
# logger = logging.getLogger(__name__)


# class ProjectInput(BaseModel):
#     """Input model for project prediction"""
#     # Basic Information
#     rera_id: Optional[str] = Field(None, description="RERA registration ID")
#     project_name: Optional[str] = Field(None, description="Name of the project")
#     promoter_name: Optional[str] = Field(None, description="Builder/promoter name")
#     district: Optional[str] = Field(None, description="District or area")
    
#     # Location Details
#     location_pin_code: Optional[int] = Field(None, ge=100000, le=999999, description="6-digit PIN code")
#     latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
#     longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
#     location_lat_long: Optional[str] = Field(None, description="Location string format")
    
#     # Project Specifications
#     project_type: Optional[str] = Field(None, description="Type of project")
#     project_status: Optional[str] = Field(None, description="Current project status")
#     project_area_sqmts: Optional[float] = Field(None, ge=0, description="Project area in square meters")
#     number_of_appartments: Optional[int] = Field(None, ge=0, description="Total number of apartments")
#     number_of_booked_appartments: Optional[int] = Field(None, ge=0, description="Number of booked apartments")
#     number_of_sanctioned_floors: Optional[int] = Field(None, ge=0, description="Number of sanctioned floors")
    
#     # Dates and Delays
#     proposed_date_of_completion: Optional[str] = Field(None, description="Original completion date (MM/DD/YYYY)")
#     revised_proposed_date_of_completion: Optional[str] = Field(None, description="Revised completion date (MM/DD/YYYY)")
#     delay_days: Optional[int] = Field(None, ge=0, description="Delay in days")
    
#     # Legal Information
#     cases_count: Optional[int] = Field(0, ge=0, description="Number of legal cases")
#     complaints_count: Optional[int] = Field(0, ge=0, description="Number of complaints")

#     @validator('number_of_booked_appartments')
#     def validate_booked_apartments(cls, v, values):
#         """Ensure booked apartments don't exceed total apartments"""
#         if v is not None and 'number_of_appartments' in values and values['number_of_appartments'] is not None:
#             if v > values['number_of_appartments']:
#                 raise ValueError("Booked apartments cannot exceed total apartments")
#         return v

# class PredictionResponse(BaseModel):
#     """Response model for predictions"""
#     prediction: int = Field(description="Prediction result (0: Not Completed, 1: Completed)")
#     confidence: float = Field(description="Confidence score (0-1)")
#     probability_completed: float = Field(description="Probability of completion")
#     probability_not_completed: float = Field(description="Probability of non-completion")
#     risk_assessment: List[str] = Field(description="Risk factors and insights")
#     project_analysis: List[str] = Field(description="Project analysis points")
#     input_validation: Dict[str, Any] = Field(description="Information about input processing")

# class ModelManager:
#     """Handles model loading and prediction logic"""
    
#     def __init__(self):
#         self.model = None
#         self.feature_columns = None
#         self.feature_medians = None
#         self.label_encoders = None
#         self.is_loaded = False
        
#     def load_models(self):
#         """Load all required model artifacts"""
#         try:
#             # Use Path to get the directory where this file is located
#             base_dir = Path(__file__).parent 
            
#             model_files = {
#                 "model": base_dir / "rera_project_pipeline_refined.pkl",
#                 "features": base_dir / "feature_columns.pkl", 
#                 "medians": base_dir / "feature_medians.pkl",
#                 "encoders": base_dir / "label_encoders.pkl"
#             }
            
#             missing_files = []
#             for name, filepath in model_files.items():
#                 if not filepath.exists():
#                     missing_files.append(str(filepath))
            
#             if missing_files:
#                 raise FileNotFoundError(f"Missing model files: {', '.join(missing_files)}")
            
#             with open(model_files["model"], "rb") as f:
#                 self.model = pickle.load(f)
            
#             with open(model_files["features"], "rb") as f:
#                 self.feature_columns = pickle.load(f)
                
#             with open(model_files["medians"], "rb") as f:
#                 self.feature_medians = pickle.load(f)
                
#             with open(model_files["encoders"], "rb") as f:
#                 self.label_encoders = pickle.load(f)
#         except Exception as e:
#             logger.error(f"Error loading model files: {str(e)}")
#             raise

#     def parse_coordinates(self, lat_long_str: str) -> tuple:
#         """Parse latitude/longitude from various string formats"""
#         if not lat_long_str or pd.isna(lat_long_str):
#             return None, None
        
#         try:
#             # Pattern for ('18.995630', '72.820807')
#             pattern1 = r"\('([\d\.-]+)',\s*'([\d\.-]+)'\)"
#             match = re.search(pattern1, str(lat_long_str))
#             if match:
#                 return float(match.group(1)), float(match.group(2))
            
#             # Pattern for 18.995630,72.820807
#             if ',' in str(lat_long_str):
#                 parts = str(lat_long_str).split(',')
#                 if len(parts) == 2:
#                     return float(parts[0].strip()), float(parts[1].strip())
            
#             return None, None
#         except (ValueError, AttributeError):
#             return None, None
    
#     def preprocess_input(self, project_data: ProjectInput) -> tuple:
#         """Preprocess input data for prediction"""
#         # Convert to dictionary and handle None values
#         data_dict = project_data.dict()
        
#         # Parse coordinates if needed
#         if data_dict.get('location_lat_long') and not (data_dict.get('latitude') and data_dict.get('longitude')):
#             lat, lng = self.parse_coordinates(data_dict['location_lat_long'])
#             if lat is not None and lng is not None:
#                 data_dict['latitude'] = lat
#                 data_dict['longitude'] = lng
        
#         # Create DataFrame
#         df = pd.DataFrame([data_dict])
        
#         # Handle missing values with defaults
#         for col, default_value in {
#             'district': '',
#             'rera_id': '',
#             'project_name': '',
#             'promoter_name': '',
#             'location_pin_code': 0,
#             'project_status': '',
#             'project_type': '',
#             'latitude': 0.0,
#             'longitude': 0.0,
#             'project_area_sqmts': 0.0,
#             'number_of_appartments': 0,
#             'number_of_booked_appartments': 0,
#             'number_of_sanctioned_floors': 0,
#             'delay_days': 0,
#             'cases_count': 0,
#             'complaints_count': 0
#         }.items():
#             if col not in df.columns or df[col].isna().all():
#                 df[col] = default_value
#             else:
#                 df[col] = df[col].fillna(default_value)
        
#         # Handle special column name mapping
#         if 'project_area_sqmts' in df.columns and 'project_area_(sqmts)' not in df.columns:
#             df['project_area_(sqmts)'] = df['project_area_sqmts']
        
#         # Encode categorical variables
#         encoding_info = {}
#         for col in df.columns:
#             if col in self.label_encoders and df[col].dtype == 'object':
#                 try:
#                     original_values = df[col].copy()
#                     df[col] = df[col].astype(str).fillna('Unknown')
                    
#                     # Handle unseen values
#                     unseen_values = set(df[col]) - set(self.label_encoders[col].classes_)
#                     if unseen_values:
#                         # Use most frequent class for unseen values
#                         most_frequent_class = self.label_encoders[col].classes_[0]
#                         df[col] = df[col].replace(list(unseen_values), most_frequent_class)
#                         encoding_info[col] = {
#                             'unseen_values': list(unseen_values),
#                             'replaced_with': most_frequent_class
#                         }
                    
#                     df[col] = self.label_encoders[col].transform(df[col])
                    
#                 except Exception as e:
#                     logger.warning(f"Error encoding column {col}: {str(e)}")
#                     df[col] = 0  # Default fallback
#                     encoding_info[col] = {'error': str(e), 'default_value': 0}
        
#         # Add missing columns with median values
#         missing_cols = set(self.feature_columns) - set(df.columns)
#         for col in missing_cols:
#             df[col] = self.feature_medians.get(col, 0)
        
#         # Reorder columns to match training
#         try:
#             df_final = df[self.feature_columns]
#         except KeyError as e:
#             missing_in_input = set(self.feature_columns) - set(df.columns)
#             logger.error(f"Missing columns in processed input: {missing_in_input}")
#             raise ValueError(f"Failed to align features. Missing: {missing_in_input}")
        
#         # Validation info
#         validation_info = {
#             'input_columns': list(df.columns),
#             'model_expected_columns': len(self.feature_columns),
#             'final_columns': len(df_final.columns),
#             'encoding_info': encoding_info,
#             'missing_columns_added': list(missing_cols)
#         }
        
#         return df_final, validation_info
    
#     def generate_risk_assessment(self, project_data: ProjectInput) -> List[str]:
#         """Generate risk assessment based on input data"""
#         risks = []
        
#         # Delay risk
#         if project_data.delay_days and project_data.delay_days > 365:
#             risks.append(f"High Risk: Significant delays ({project_data.delay_days} days)")
#         elif project_data.delay_days and project_data.delay_days > 90:
#             risks.append(f"Medium Risk: Notable delays ({project_data.delay_days} days)")
        
#         # Legal risk
#         if project_data.cases_count and project_data.cases_count > 0:
#             risks.append(f"Legal Risk: {project_data.cases_count} active cases")
        
#         # Booking risk
#         if (project_data.number_of_appartments and project_data.number_of_booked_appartments and 
#             project_data.number_of_appartments > 0):
#             booking_pct = (project_data.number_of_booked_appartments / project_data.number_of_appartments) * 100
#             if booking_pct < 30:
#                 risks.append(f"High Risk: Very low booking rate ({booking_pct:.1f}%)")
#             elif booking_pct < 50:
#                 risks.append(f"Medium Risk: Low booking rate ({booking_pct:.1f}%)")
#             elif booking_pct > 80:
#                 risks.append(f"Positive: Strong booking rate ({booking_pct:.1f}%)")
        
#         # RERA compliance
#         if not project_data.rera_id:
#             risks.append("Medium Risk: No RERA ID provided")
        
#         # High-rise risk
#         if project_data.number_of_sanctioned_floors and project_data.number_of_sanctioned_floors > 30:
#             risks.append("Note: High-rise project requires careful monitoring")
        
#         if not risks:
#             risks.append("No significant risks identified from provided data")
            
#         return risks
    
#     def generate_project_analysis(self, project_data: ProjectInput) -> List[str]:
#         """Generate project analysis points"""
#         analysis = []
        
#         # Basic validation
#         if project_data.rera_id:
#             analysis.append("RERA registered project")
        
#         # Location analysis
#         if project_data.latitude and project_data.longitude:
#             analysis.append("GPS coordinates available for precise location")
#         elif project_data.location_pin_code:
#             analysis.append(f"Located in PIN code area: {project_data.location_pin_code}")
        
#         # Size analysis
#         if project_data.number_of_appartments:
#             if project_data.number_of_appartments > 100:
#                 analysis.append("Large-scale project (>100 units)")
#             elif project_data.number_of_appartments > 50:
#                 analysis.append("Medium-scale project (50-100 units)")
#             else:
#                 analysis.append("Small-scale project (<50 units)")
        
#         # Project area
#         if project_data.project_area_sqmts and project_data.project_area_sqmts > 10000:
#             analysis.append(f"Large project area: {project_data.project_area_sqmts:,.0f} sq.mts")
        
#         # Status analysis
#         if project_data.project_status:
#             analysis.append(f"Current status: {project_data.project_status}")
        
#         if not analysis:
#             analysis.append("Limited project information available for detailed analysis")
            
#         return analysis
    
#     def predict(self, project_data: ProjectInput) -> PredictionResponse:
#         """Make prediction for project completion"""
#         if not self.is_loaded:
#             self.load_models()
        
#         try:
#             # Preprocess input
#             df_processed, validation_info = self.preprocess_input(project_data)
            
#             # Make prediction
#             prediction = self.model.predict(df_processed)[0]
            
#             # Get probabilities
#             try:
#                 probabilities = self.model.predict_proba(df_processed)[0]
#                 if len(probabilities) == 2:
#                     prob_not_completed, prob_completed = probabilities
#                 else:
#                     # Handle single class case
#                     if prediction == 1:
#                         prob_completed, prob_not_completed = 0.9, 0.1
#                     else:
#                         prob_completed, prob_not_completed = 0.1, 0.9
#             except:
#                 # Fallback if predict_proba fails
#                 if prediction == 1:
#                     prob_completed, prob_not_completed = 0.8, 0.2
#                 else:
#                     prob_completed, prob_not_completed = 0.2, 0.8
            
#             # Calculate confidence (distance from 0.5)
#             confidence = abs(prob_completed - 0.5) * 2
            
#             # Generate assessments
#             risk_assessment = self.generate_risk_assessment(project_data)
#             project_analysis = self.generate_project_analysis(project_data)
            
#             return PredictionResponse(
#                 prediction=int(prediction),
#                 confidence=float(confidence),
#                 probability_completed=float(prob_completed),
#                 probability_not_completed=float(prob_not_completed),
#                 risk_assessment=risk_assessment,
#                 project_analysis=project_analysis,
#                 input_validation=validation_info
#             )
            
#         except Exception as e:
#             logger.error(f"Prediction error: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

import pandas as pd
import numpy as np
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re

try:
    from ..core.paths import resolve_artifact  # type: ignore
except Exception:
    try:
        from app.core.paths import resolve_artifact  # type: ignore
    except Exception:
        from core.paths import resolve_artifact  # type: ignore

logger = logging.getLogger(__name__)

class ProjectInput(BaseModel):
    """Input model for project prediction"""
    project_name: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    location_pin_code: Optional[str] = None
    location_lat_long: Optional[str] = None
    number_of_appartments: Optional[float] = None
    number_of_booked_appartments: Optional[float] = None
    project_area_sqmts: Optional[float] = None
    proposed_date_of_completion: Optional[str] = None
    revised_proposed_date_of_completion: Optional[str] = None
    extended_date_of_completion: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "project_name": "Sample Project",
                "district": "Mumbai Suburban",
                "number_of_appartments": 150,
                "number_of_booked_appartments": 120,
                "project_area_sqmts": 15000,
                "location_pin_code": "400018",
                "proposed_date_of_completion": "2024-12-31",
                "revised_proposed_date_of_completion": "2025-06-30"
            }
        }

class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: str
    confidence: float
    probabilities: Dict[str, float]
    risk_level: str
    risk_assessment: str
    project_analysis: str

class ModelManager:
    """Manages model loading and predictions with proper feature engineering"""

    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.feature_medians = None
        self.label_encoders = None
        self.is_loaded = False
        
    def load_models(self):
        """Load all required model artifacts"""
        try:
            # Use Path to get the directory where this file is located
            base_dir = Path(__file__).parent 
            
            model_files = {
                "model": resolve_artifact("rera_project_pipeline_refined.pkl", base_dir / "rera_project_pipeline_refined.pkl"),
                "features": resolve_artifact("feature_columns.pkl", base_dir / "feature_columns.pkl"),
                "medians": resolve_artifact("feature_medians.pkl", base_dir / "feature_medians.pkl"),
                "encoders": resolve_artifact("label_encoders.pkl", base_dir / "label_encoders.pkl"),
            }
            
            missing_files = []
            for name, filepath in model_files.items():
                if not filepath.exists():
                    missing_files.append(str(filepath))
            
            if missing_files:
                raise FileNotFoundError(f"Missing model files: {', '.join(missing_files)}")
            
            with open(model_files["model"], "rb") as f:
                self.model = pickle.load(f)
            
            with open(model_files["features"], "rb") as f:
                self.feature_columns = pickle.load(f)
                
            with open(model_files["medians"], "rb") as f:
                self.feature_medians = pickle.load(f)
                
            with open(model_files["encoders"], "rb") as f:
                self.label_encoders = pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading model files: {str(e)}")
            raise

    def _apply_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the same feature engineering as in training"""
        logger.info("Applying feature engineering...")
        
        # Date processing
        date_columns = [
            'proposed_date_of_completion',
            'revised_proposed_date_of_completion',
            'extended_date_of_completion'
        ]
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Delay calculation
        if 'proposed_date_of_completion' in df.columns and 'revised_proposed_date_of_completion' in df.columns:
            df['delay_days'] = (
                df['revised_proposed_date_of_completion'] - 
                df['proposed_date_of_completion']
            ).dt.days
            df['delay_days'] = df['delay_days'].fillna(0).clip(lower=0, upper=3650)
            
            # Delay categories
            df['delay_category'] = pd.cut(
                df['delay_days'],
                bins=[-1, 0, 90, 365, 3650],
                labels=['No_Delay', 'Short_Delay', 'Medium_Delay', 'Long_Delay']
            )
            logger.info(f"Delay days calculated: {df['delay_days'].values[0]}")
        
        # Days until proposed completion
        if 'proposed_date_of_completion' in df.columns:
            df['days_until_completion'] = (
                df['proposed_date_of_completion'] - pd.Timestamp.now()
            ).dt.days
            df['days_until_completion'] = df['days_until_completion'].fillna(0)
            
            # Is overdue?
            df['is_overdue'] = (df['days_until_completion'] < 0).astype(int)
            logger.info(f"Days until completion: {df['days_until_completion'].values[0]}, Overdue: {df['is_overdue'].values[0]}")
        
        # Parse coordinates
        if 'location_lat_long' in df.columns:
            coords = df['location_lat_long'].apply(self._parse_coordinates)
            df['latitude'] = [coord[0] for coord in coords]
            df['longitude'] = [coord[1] for coord in coords]
            logger.info(f"Coordinates parsed: lat={df['latitude'].values[0]}, lng={df['longitude'].values[0]}")
        
        # Booking metrics
        if 'number_of_appartments' in df.columns and 'number_of_booked_appartments' in df.columns:
            df['booking_percentage'] = (
                df['number_of_booked_appartments'] / 
                df['number_of_appartments'].replace(0, 1)
            ) * 100
            df['booking_percentage'] = df['booking_percentage'].fillna(0).clip(0, 100)
            
            df['booking_category'] = pd.cut(
                df['booking_percentage'],
                bins=[0, 25, 50, 75, 100],
                labels=['Low', 'Medium', 'High', 'Very_High'],
                include_lowest=True
            )
            
            # Number of unbooked apartments
            df['unbooked_apartments'] = (
                df['number_of_appartments'] - df['number_of_booked_appartments']
            ).fillna(0)
            
            logger.info(f"Booking percentage: {df['booking_percentage'].values[0]:.2f}%")
        
        # Area per apartment
        if 'project_area_sqmts' in df.columns and 'number_of_appartments' in df.columns:
            df['area_per_apartment'] = (
                df['project_area_sqmts'] / 
                df['number_of_appartments'].replace(0, 1)
            )
            df['area_per_apartment'] = df['area_per_apartment'].fillna(0)
            logger.info(f"Area per apartment: {df['area_per_apartment'].values[0]:.2f}")
        
        # Location cluster
        if 'district' in df.columns and 'location_pin_code' in df.columns:
            df['location_cluster'] = (
                df['district'].astype(str) + "_" + 
                df['location_pin_code'].astype(str)
            )
        
        # Project size categories
        if 'number_of_appartments' in df.columns:
            df['project_size'] = pd.cut(
                df['number_of_appartments'].fillna(0),
                bins=[0, 10, 50, 100, 500, float('inf')],
                labels=['Very_Small', 'Small', 'Medium', 'Large', 'Very_Large'],
                include_lowest=True
            )
            logger.info(f"Project size: {df['project_size'].values[0]}")
        
        # Has extension flag
        if 'extended_date_of_completion' in df.columns:
            df['has_extension'] = df['extended_date_of_completion'].notna().astype(int)
            logger.info(f"Has extension: {df['has_extension'].values[0]}")
        
        return df
    
    def _parse_coordinates(self, coord_str):
        """Parse coordinate string"""
        if pd.isna(coord_str):
            return np.nan, np.nan
        try:
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
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features to match training format"""
        logger.info("Preparing features for prediction...")
        
        # Create a new DataFrame with all required features
        feature_df = pd.DataFrame(index=df.index)
        
        for col in self.feature_columns:
            if col in df.columns:
                feature_df[col] = df[col]
            else:
                # Feature doesn't exist, fill with default value
                if col in self.feature_medians:
                    feature_df[col] = self.feature_medians[col]
                else:
                    feature_df[col] = 0
                logger.debug(f"Missing feature {col}, using default value")
        
        # Handle categorical features with label encoders
        for col in self.label_encoders.keys():
            if col in feature_df.columns:
                # Convert to string and handle unknown categories
                feature_df[col] = feature_df[col].astype(str).replace('nan', 'Unknown')
                
                # Encode using the saved encoder
                le = self.label_encoders[col]
                try:
                    # Try to transform
                    feature_df[col] = le.transform(feature_df[col])
                except ValueError:
                    # Unknown category - use most frequent category (usually 'Other' or 'Unknown')
                    logger.warning(f"Unknown category in {col}, using default encoding")
                    feature_df[col] = 0  # Default to first class
        
        # Handle numeric features
        for col in feature_df.columns:
            if col not in self.label_encoders:
                # This is numeric, fill NaN with median
                if col in self.feature_medians:
                    feature_df[col] = feature_df[col].fillna(self.feature_medians[col])
                else:
                    feature_df[col] = feature_df[col].fillna(0)
        
        logger.info(f"Features prepared: {feature_df.shape}")
        logger.info(f"Sample values: {feature_df.iloc[0].head(10).to_dict()}")
        
        return feature_df
    
    def predict(self, project_data: ProjectInput) -> PredictionResponse:
        """Make prediction for a project"""
        if not self.is_loaded:
            logger.info("Models not loaded, loading now...")
            self.load_models()
        
        try:
            # Convert input to dictionary
            input_dict = project_data.dict()
            logger.info(f"Input data: {input_dict}")
            
            # Create DataFrame
            df = pd.DataFrame([input_dict])
            
            # Apply feature engineering
            df = self._apply_feature_engineering(df)
            
            # Prepare features to match training
            feature_df = self._prepare_features(df)
            
            # Make prediction
            prediction = self.model.predict(feature_df)[0]
            probabilities = self.model.predict_proba(feature_df)[0]
            
            # Log model info for debugging
            logger.info(f"Model classes: {self.model.named_steps['classifier'].classes_}")
            logger.info(f"Prediction raw: {prediction}")
            logger.info(f"Probabilities shape: {probabilities.shape}")
            logger.info(f"Probabilities: {probabilities}")
            
            # Handle single-class or multi-class predictions
            # Model predicts: 0=Low Risk, 1=High Risk
            if len(probabilities) == 1:
                # Model only has one class - handle gracefully
                logger.warning("Model only predicting one class!")
                pred_label = "High Risk" if prediction == 1 else "Low Risk"
                confidence = 100.0
                prob_dict = {
                    "Low Risk": 0.0 if prediction == 1 else 100.0,
                    "High Risk": 100.0 if prediction == 1 else 0.0
                }
            elif len(probabilities) == 2:
                # Normal binary classification
                pred_label = "High Risk" if prediction == 1 else "Low Risk"
                confidence = float(max(probabilities) * 100)
                prob_dict = {
                    "Low Risk": float(probabilities[0] * 100),
                    "High Risk": float(probabilities[1] * 100)
                }
            else:
                # Unexpected number of classes
                logger.error(f"Unexpected probability shape: {probabilities.shape}")
                pred_label = "High Risk" if prediction == 1 else "Low Risk"
                confidence = float(max(probabilities) * 100)
                prob_dict = {
                    "Low Risk": float(probabilities[0] * 100) if len(probabilities) > 0 else 50.0,
                    "High Risk": float(probabilities[1] * 100) if len(probabilities) > 1 else 50.0
                }
            
            # Risk assessment
            risk_level = self._assess_risk(probabilities, df)
            risk_assessment = self._generate_risk_assessment(df, probabilities)
            project_analysis = self._generate_project_analysis(df, input_dict)
            
            logger.info(f"Prediction: {pred_label}, Confidence: {confidence:.2f}%")
            
            return PredictionResponse(
                prediction=pred_label,
                confidence=confidence,
                probabilities=prob_dict,
                risk_level=risk_level,
                risk_assessment=risk_assessment,
                project_analysis=project_analysis
            )
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _assess_risk(self, probabilities, df) -> str:
        """Assess project risk level"""
        # Handle different probability shapes
        if len(probabilities) == 2:
            high_risk_prob = probabilities[1]  # Index 1 is High Risk
        elif len(probabilities) == 1:
            # Single class - infer from the prediction
            high_risk_prob = 1.0 if probabilities[0] > 0.5 else 0.0
        else:
            high_risk_prob = 0.5  # Default to medium risk
        
        # Check for delay
        has_delay = df['delay_days'].values[0] > 180 if 'delay_days' in df.columns else False
        
        # Check booking rate
        booking_pct = df['booking_percentage'].values[0] if 'booking_percentage' in df.columns else 50
        
        if high_risk_prob > 0.7 or (has_delay and booking_pct < 30):
            return "High"
        elif high_risk_prob > 0.5 or has_delay:
            return "Medium"
        else:
            return "Low"
    
    def _generate_risk_assessment(self, df, probabilities) -> str:
        """Generate detailed risk assessment"""
        risks = []
        
        if 'delay_days' in df.columns and df['delay_days'].values[0] > 0:
            delay = int(df['delay_days'].values[0])
            if delay > 180:
                risks.append(f"Significant delay: {delay} days")
            else:
                risks.append(f"Minor delay: {delay} days")
        
        if 'booking_percentage' in df.columns:
            booking_pct = df['booking_percentage'].values[0]
            if booking_pct < 30:
                risks.append(f"Very low booking rate ({booking_pct:.1f}%)")
            elif booking_pct < 50:
                risks.append(f"Low booking rate ({booking_pct:.1f}%)")
            elif booking_pct > 80:
                risks.append(f"Strong booking rate ({booking_pct:.1f}%) - positive")
        
        if 'has_extension' in df.columns and df['has_extension'].values[0] == 1:
            risks.append("Deadline has been extended")
        
        if 'is_overdue' in df.columns and df['is_overdue'].values[0] == 1:
            risks.append("Project is currently overdue")
        
        if not risks:
            return "No significant risk indicators identified"
        
        return " | ".join(risks)
        
        return " | ".join(risks)
    
    def _generate_project_analysis(self, df, input_dict) -> str:
        """Generate project analysis summary"""
        analysis = []
        
        # Project status
        if input_dict.get('project_status'):
            status = input_dict['project_status']
            analysis.append(f"Status: {status}")
        else:
            analysis.append("RERA registered project")
        
        # Location
        if input_dict.get('district') and input_dict.get('location_pin_code'):
            analysis.append(f"Location: {input_dict['district']}, PIN {input_dict['location_pin_code']}")
        elif input_dict.get('location_pin_code'):
            analysis.append(f"PIN code: {input_dict['location_pin_code']}")
        
        # Timeline analysis
        if 'delay_days' in df.columns:
            delay = df['delay_days'].values[0]
            if delay > 180:
                analysis.append(f"Timeline: Delayed by {int(delay)} days")
            elif delay > 0:
                analysis.append(f"Timeline: Minor delay of {int(delay)} days")
            else:
                analysis.append("Timeline: On schedule")
        
        # Project scale
        if input_dict.get('number_of_appartments'):
            units = input_dict['number_of_appartments']
            if 'project_size' in df.columns:
                size = df['project_size'].values[0]
                analysis.append(f"Scale: {size} ({int(units)} units)")
            else:
                analysis.append(f"Scale: {int(units)} units")
        
        # Booking status
        if 'booking_percentage' in df.columns:
            booking_pct = df['booking_percentage'].values[0]
            analysis.append(f"Bookings: {booking_pct:.1f}%")
        
        return " | ".join(analysis)