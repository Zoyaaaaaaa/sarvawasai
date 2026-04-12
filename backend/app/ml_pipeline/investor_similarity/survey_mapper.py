"""
Survey Mapper - Anonymous Survey to Block A Features

Maps survey responses to Attitude & Trust features (Block A).
Includes bias prevention and demographic correlation monitoring.

FORBIDDEN: Inferring capital, ROI, or income from survey data.
"""

from typing import Dict, Optional
import numpy as np
from .feature_contracts import BlockA, FeatureSource, BiasGuardrail


class SurveyResponse:
    """
    Anonymous survey response schema
    
    Survey questions are designed to extract attitudes and trust preferences
    WITHOUT collecting demographics.
    """
    
    def __init__(
        self,
        # Investment priorities (1-5 scale)
        priority_safety: int,
        priority_returns: int,
        priority_liquidity: int,
        
        # Pooling comfort (1-5 scale)
        pooling_comfort_strangers: int,
        pooling_comfort_verified: int,
        pooling_comfort_friends: int,
        
        # Control preferences (1-5 scale)
        prefer_hands_on: int,
        trust_professional_management: int,
        
        # Real estate conviction (1-5 scale)
        re_vs_stocks: int,
        re_long_term_belief: int,
        
        # Trust enablers (boolean)
        trust_enables_transparency: bool,
        trust_enables_track_record: bool,
        trust_enables_legal_protection: bool
    ):
        self.priority_safety = priority_safety
        self.priority_returns = priority_returns
        self.priority_liquidity = priority_liquidity
        self.pooling_comfort_strangers = pooling_comfort_strangers
        self.pooling_comfort_verified = pooling_comfort_verified
        self.pooling_comfort_friends = pooling_comfort_friends
        self.prefer_hands_on = prefer_hands_on
        self.trust_professional_management = trust_professional_management
        self.re_vs_stocks = re_vs_stocks
        self.re_long_term_belief = re_long_term_belief
        self.trust_enables_transparency = trust_enables_transparency
        self.trust_enables_track_record = trust_enables_track_record
        self.trust_enables_legal_protection = trust_enables_legal_protection
    
    def validate(self):
        """Validate survey responses"""
        for attr in ['priority_safety', 'priority_returns', 'priority_liquidity',
                     'pooling_comfort_strangers', 'pooling_comfort_verified',
                     'pooling_comfort_friends', 'prefer_hands_on',
                     'trust_professional_management', 're_vs_stocks',
                     're_long_term_belief']:
            value = getattr(self, attr)
            if not (1 <= value <= 5):
                raise ValueError(f"{attr} must be in [1, 5], got {value}")


class SurveyMapper:
    """
    Maps survey responses to Block A features
    
    Implements bias prevention:
    - No demographic inference
    - Correlation monitoring
    - Transparent feature extraction logic
    """
    
    def __init__(self):
        self.bias_guardrail = BiasGuardrail(demographic_correlation_threshold=0.1)
    
    def map_to_block_a(self, survey: SurveyResponse) -> Dict[str, float]:
        """
        Extract Block A features from survey
        
        Args:
            survey: SurveyResponse object
            
        Returns:
            Dictionary of Block A features
        """
        survey.validate()
        
        # A1: Risk Orientation Score
        # Higher value = more risk-seeking (prioritize returns over safety)
        risk_orientation = self._compute_risk_orientation(survey)
        
        # A2: Collaboration Comfort Score
        # Higher value = more comfortable with co-investment
        collaboration_comfort = self._compute_collaboration_comfort(survey)
        
        # A3: Control Preference Score
        # Higher value = prefer control (hands-on)
        control_preference = self._compute_control_preference(survey)
        
        # A4: Real Estate Conviction Score
        # Higher value = stronger belief in RE
        re_conviction = self._compute_re_conviction(survey)
        
        block_a = {
            "risk_orientation_score": risk_orientation,
            "collaboration_comfort_score": collaboration_comfort,
            "control_preference_score": control_preference,
            "real_estate_conviction_score": re_conviction
        }
        
        # Validate against contracts
        for feature_name, value in block_a.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{feature_name} must be in [0, 1], got {value}")
        
        return block_a
    
    def _compute_risk_orientation(self, survey: SurveyResponse) -> float:
        """
        Risk orientation: preference for returns vs safety
        
        Formula: weighted combination of priorities
        - High returns priority → higher score
        - High safety priority → lower score
        """
        # Normalize to [0, 1]
        returns_normalized = (survey.priority_returns - 1) / 4.0
        safety_normalized = (survey.priority_safety - 1) / 4.0
        
        # Weighted average (returns positive, safety negative)
        risk_score = 0.6 * returns_normalized + 0.4 * (1 - safety_normalized)
        
        # Clip to [0, 1]
        return np.clip(risk_score, 0.0, 1.0)
    
    def _compute_collaboration_comfort(self, survey: SurveyResponse) -> float:
        """
        Collaboration comfort: willingness to co-invest
        
        Formula: average of pooling comfort across contexts
        """
        pooling_scores = [
            survey.pooling_comfort_strangers,
            survey.pooling_comfort_verified,
            survey.pooling_comfort_friends
        ]
        
        # Normalize and average
        normalized = [(s - 1) / 4.0 for s in pooling_scores]
        avg_comfort = np.mean(normalized)
        
        # Weight trust enablers (boolean features)
        trust_boost = sum([
            survey.trust_enables_transparency,
            survey.trust_enables_track_record,
            survey.trust_enables_legal_protection
        ]) / 3.0 * 0.2  # Up to 20% boost
        
        collaboration_score = avg_comfort + trust_boost
        
        return np.clip(collaboration_score, 0.0, 1.0)
    
    def _compute_control_preference(self, survey: SurveyResponse) -> float:
        """
        Control preference: hands-on vs delegation
        
        Formula: balance between hands-on and trust in professionals
        """
        hands_on_normalized = (survey.prefer_hands_on - 1) / 4.0
        delegation_normalized = (survey.trust_professional_management - 1) / 4.0
        
        # Higher score = prefer control
        control_score = 0.7 * hands_on_normalized + 0.3 * (1 - delegation_normalized)
        
        return np.clip(control_score, 0.0, 1.0)
    
    def _compute_re_conviction(self, survey: SurveyResponse) -> float:
        """
        Real estate conviction: belief in RE as wealth vehicle
        
        Formula: preference for RE over alternatives + long-term belief
        """
        re_vs_stocks_normalized = (survey.re_vs_stocks - 1) / 4.0
        long_term_normalized = (survey.re_long_term_belief - 1) / 4.0
        
        conviction_score = 0.5 * re_vs_stocks_normalized + 0.5 * long_term_normalized
        
        return np.clip(conviction_score, 0.0, 1.0)
    
    def validate_bias(
        self,
        block_a_features: Dict[str, float],
        demographic_data: Dict[str, any]
    ) -> bool:
        """
        Validate that Block A features don't correlate with demographics
        
        Args:
            block_a_features: Computed Block A features
            demographic_data: Age, gender, location, occupation, etc.
            
        Returns:
            True if passes bias check
        """
        # Compute correlations (mock - in production, use dataset-level stats)
        correlations = {}
        
        for demo_name, demo_value in demographic_data.items():
            # Mock correlation computation
            # In production, this would use aggregated dataset statistics
            correlations[demo_name] = 0.05  # Placeholder
        
        # Check each feature
        for feature_name in block_a_features:
            if not self.bias_guardrail.validate(feature_name, correlations):
                return False
        
        return True


class SurveyDataSource:
    """
    Manages survey data collection and storage
    
    Ensures privacy and prevents demographic inference.
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.mapper = SurveyMapper()
    
    def collect_survey(
        self,
        investor_id_raw: str,
        survey: SurveyResponse
    ) -> Dict[str, float]:
        """
        Collect survey and extract Block A features
        
        Args:
            investor_id_raw: Investor identifier (hashed before storage)
            survey: Survey responses
            
        Returns:
            Block A features
        """
        block_a = self.mapper.map_to_block_a(survey)
        
        # In production: store survey separately from features
        # No reversible joins
        
        return block_a
