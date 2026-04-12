"""
Feature Contracts - Immutable Data Specifications

Defines the three permanent feature blocks:
- Block A: Attitude & Trust Features
- Block B: Economic Constraint Features  
- Block C: Behavioral Reality Features

Each feature includes type validation, source restrictions, bias guardrails,
and governance metadata.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List
from enum import Enum
import warnings


class FeatureSource(Enum):
    """Allowed data sources for features"""
    SURVEY = "survey"
    PLATFORM = "platform"
    BEHAVIORAL = "behavioral"
    SYNTHETIC = "synthetic"


class BiasGuardrail:
    """Bias monitoring for features"""
    
    def __init__(self, demographic_correlation_threshold: float = 0.1):
        self.threshold = demographic_correlation_threshold
        
    def validate(self, feature_name: str, correlations: dict) -> bool:
        """
        Check if feature correlates with demographics above threshold
        
        Args:
            feature_name: Name of feature being validated
            correlations: Dict of {demographic: correlation_value}
            
        Returns:
            True if passes, False if violates guardrail
        """
        violations = []
        for demo, corr in correlations.items():
            if abs(corr) > self.threshold:
                violations.append(f"{demo}: {corr:.3f}")
        
        if violations:
            warnings.warn(
                f"Feature '{feature_name}' violates bias guardrail. "
                f"Correlations: {', '.join(violations)}"
            )
            return False
        return True


@dataclass
class FeatureContract:
    """Base contract for all features"""
    name: str
    meaning: str
    feature_type: str
    value_range: str
    allowed_sources: List[FeatureSource]
    forbidden_sources: List[FeatureSource]
    confidence_weight: float
    refresh_cadence: str
    bias_guardrail: BiasGuardrail = field(default_factory=BiasGuardrail)
    
    def validate_value(self, value) -> bool:
        """Override in subclasses for type-specific validation"""
        raise NotImplementedError
        
    def validate_source(self, source: FeatureSource) -> bool:
        """Validate data source is allowed"""
        if source in self.forbidden_sources:
            raise ValueError(
                f"Feature '{self.name}' cannot use {source.value} as source"
            )
        if source not in self.allowed_sources:
            warnings.warn(
                f"Feature '{self.name}' using non-standard source {source.value}"
            )
        return True


# ==================== BLOCK A: Attitude & Trust Features ====================

@dataclass
class FloatFeatureContract(FeatureContract):
    """Contract for float features in [0, 1]"""
    
    def validate_value(self, value: float) -> bool:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} must be numeric, got {type(value)}")
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{self.name} must be in [0, 1], got {value}")
        return True


class BlockA:
    """
    BLOCK A — Attitude & Trust Features
    
    Source: Anonymous Survey / Platform Survey
    Confidence Weight: 0.4
    Purpose: Cold-start similarity, philosophy alignment
    """
    
    A1_RISK_ORIENTATION = FloatFeatureContract(
        name="risk_orientation_score",
        meaning="Preference for return vs safety",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.SURVEY],
        forbidden_sources=[FeatureSource.PLATFORM],
        confidence_weight=0.4,
        refresh_cadence="on_survey_update",
        bias_guardrail=BiasGuardrail(demographic_correlation_threshold=0.1)
    )
    
    A2_COLLABORATION_COMFORT = FloatFeatureContract(
        name="collaboration_comfort_score",
        meaning="Willingness to co-invest with others",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.SURVEY],
        forbidden_sources=[FeatureSource.PLATFORM],
        confidence_weight=0.4,
        refresh_cadence="on_survey_update"
    )
    
    A3_CONTROL_PREFERENCE = FloatFeatureContract(
        name="control_preference_score",
        meaning="Control vs delegation tendency",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.SURVEY],
        forbidden_sources=[],
        confidence_weight=0.4,
        refresh_cadence="on_survey_update"
    )
    
    A4_RE_CONVICTION = FloatFeatureContract(
        name="real_estate_conviction_score",
        meaning="Belief in real estate as wealth vehicle",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.SURVEY],
        forbidden_sources=[],
        confidence_weight=0.4,
        refresh_cadence="on_survey_update"
    )
    
    @classmethod
    def get_all_features(cls) -> List[FeatureContract]:
        """Return all Block A feature contracts"""
        return [
            cls.A1_RISK_ORIENTATION,
            cls.A2_COLLABORATION_COMFORT,
            cls.A3_CONTROL_PREFERENCE,
            cls.A4_RE_CONVICTION
        ]


# ==================== BLOCK B: Economic Constraint Features ====================

@dataclass
class OrdinalFeatureContract(FeatureContract):
    """Contract for ordinal features"""
    allowed_values: List = field(default_factory=list)
    
    def validate_value(self, value) -> bool:
        if value not in self.allowed_values:
            raise ValueError(
                f"{self.name} must be one of {self.allowed_values}, got {value}"
            )
        return True


@dataclass
class ContinuousFeatureContract(FeatureContract):
    """Contract for continuous numeric features"""
    bias_guardrails: str = ""  # Optional bias constraint description
    
    def validate_value(self, value) -> bool:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} must be numeric, got {type(value)}")
        return True


class BlockB:
    """
    BLOCK B — Economic Constraint Features
    
    Source: Platform data + market priors
    Confidence Weight: 1.0 (platform), 0.3 (synthetic)
    """
    
    B1_CAPITAL_BAND = OrdinalFeatureContract(
        name="capital_band",
        meaning="Investment capacity bucket",
        feature_type="ordinal",
        value_range="{0, 1, 2, 3, 4}",
        allowed_values=[0, 1, 2, 3, 4],
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SYNTHETIC],
        forbidden_sources=[FeatureSource.SURVEY],
        confidence_weight=1.0,  # 0.3 for synthetic
        refresh_cadence="on_profile_update"
    )
    
    B2_EXPECTED_ROI_BAND = OrdinalFeatureContract(
        name="expected_roi_band",
        meaning="Target return expectation",
        feature_type="ordinal",
        value_range="{'low', 'medium', 'high'}",
        allowed_values=["low", "medium", "high"],
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SYNTHETIC],
        forbidden_sources=[],
        confidence_weight=1.0,
        refresh_cadence="on_profile_update"
    )
    
    B3_HOLDING_PERIOD_BAND = OrdinalFeatureContract(
        name="holding_period_band",
        meaning="Liquidity alignment",
        feature_type="ordinal",
        value_range="{'short', 'medium', 'long'}",
        allowed_values=["short", "medium", "long"],
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SYNTHETIC],
        forbidden_sources=[],
        confidence_weight=1.0,
        refresh_cadence="on_profile_update"
    )
    
    B4_CAPITAL_DEPTH_INDEX = ContinuousFeatureContract(
        name="capital_depth_index",
        meaning="Financial accumulation maturity (replaces age)",
        feature_type="continuous",
        value_range="[0, ∞)",
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SYNTHETIC],
        forbidden_sources=[],
        bias_guardrails="|correlation with demographics| < 0.1",
        confidence_weight=1.0,
        refresh_cadence="quarterly"
    )
    
    B5_TICKET_SIZE_STABILITY = ContinuousFeatureContract(
        name="ticket_size_stability",
        meaning="Investment consistency (avg / volatility)",
        feature_type="continuous",
        value_range="[0, ∞)",
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.BEHAVIORAL],
        forbidden_sources=[FeatureSource.SURVEY],
        bias_guardrails="|correlation with demographics| < 0.1",
        confidence_weight=1.0,
        refresh_cadence="on_deal_completion"
    )
    
    B6_HOLDING_PERIOD_MONTHS = ContinuousFeatureContract(
        name="holding_period_months",
        meaning="Actual max holding period preference",
        feature_type="continuous",
        value_range="[1, 600]",  # 1 month to 50 years
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SYNTHETIC],
        forbidden_sources=[],
        confidence_weight=1.0,
        refresh_cadence="quarterly"
    )
    
    B7_BEHAVIORAL_CONSISTENCY_SCORE = ContinuousFeatureContract(
        name="behavioral_consistency_score",
        meaning="Reliability proxy (1 - variance in outcomes)",
        feature_type="continuous",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.BEHAVIORAL],
        forbidden_sources=[FeatureSource.SURVEY, FeatureSource.SYNTHETIC],
        confidence_weight=1.0,
        refresh_cadence="on_deal_completion"
    )
    
    B8_CAPITAL_COVERAGE_RATIO = ContinuousFeatureContract(
        name="capital_coverage_ratio",
        meaning="Ability to solo deals (capital / avg_deal_size)",
        feature_type="continuous",
        value_range="[0, ∞)",
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.BEHAVIORAL],
        forbidden_sources=[],
        confidence_weight=1.0,
        refresh_cadence="on_deal_completion"
    )
    
    B9_CITY_TIER = OrdinalFeatureContract(
        name="city_tier",
        meaning="Real estate price context",
        feature_type="ordinal",
        value_range="{1, 2, 3}",
        allowed_values=[1, 2, 3],
        allowed_sources=[FeatureSource.PLATFORM, FeatureSource.SURVEY],
        forbidden_sources=[],
        confidence_weight=1.0,
        refresh_cadence="on_profile_update"
    )
    
    @classmethod
    def get_all_features(cls) -> List[FeatureContract]:
        """Return all Block B feature contracts"""
        return [
            cls.B1_CAPITAL_BAND,
            cls.B2_EXPECTED_ROI_BAND,
            cls.B3_HOLDING_PERIOD_BAND,
            cls.B4_CAPITAL_DEPTH_INDEX,
            cls.B5_TICKET_SIZE_STABILITY,
            cls.B6_HOLDING_PERIOD_MONTHS,
            cls.B7_BEHAVIORAL_CONSISTENCY_SCORE,
            cls.B8_CAPITAL_COVERAGE_RATIO,
            cls.B9_CITY_TIER
        ]


# ==================== BLOCK C: Behavioral Reality Features ====================

class BlockC:
    """
    BLOCK C — Behavioral Reality Features (Future, Locked Now)
    
    Source: Platform co-investment outcomes
    Confidence Weight: increases over time
    
    NOTE: These features are currently placeholders. They will be populated
    as behavioral data accrues from actual co-investment activity.
    """
    
    C1_DEAL_SUCCESS_RATIO = FloatFeatureContract(
        name="deal_success_ratio",
        meaning="Closed vs defaulted deals",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.BEHAVIORAL],
        forbidden_sources=[FeatureSource.SURVEY, FeatureSource.SYNTHETIC],
        confidence_weight=0.0,  # Increases with data
        refresh_cadence="weekly"
    )
    
    C2_AVG_HOLDING_DURATION = FloatFeatureContract(
        name="avg_holding_duration",
        meaning="Average days held per investment",
        feature_type="float",
        value_range="[0, inf]",
        allowed_sources=[FeatureSource.BEHAVIORAL],
        forbidden_sources=[FeatureSource.SURVEY, FeatureSource.SYNTHETIC],
        confidence_weight=0.0,
        refresh_cadence="weekly"
    )
    
    C3_BEHAVIORAL_CONSISTENCY = FloatFeatureContract(
        name="behavioral_consistency_score",
        meaning="Declared vs actual behavior alignment",
        feature_type="float",
        value_range="[0, 1]",
        allowed_sources=[FeatureSource.BEHAVIORAL],
        forbidden_sources=[FeatureSource.SURVEY, FeatureSource.SYNTHETIC],
        confidence_weight=0.0,
        refresh_cadence="monthly"
    )
    
    @classmethod
    def get_all_features(cls) -> List[FeatureContract]:
        """Return all Block C feature contracts"""
        return [
            cls.C1_DEAL_SUCCESS_RATIO,
            cls.C2_AVG_HOLDING_DURATION,
            cls.C3_BEHAVIORAL_CONSISTENCY
        ]


# ==================== Feature Block Registry ====================

class FeatureBlock:
    """Registry of all feature blocks"""
    
    A = BlockA
    B = BlockB
    C = BlockC
    
    @classmethod
    def get_all_contracts(cls) -> dict:
        """Return all feature contracts organized by block"""
        return {
            "block_a": BlockA.get_all_features(),
            "block_b": BlockB.get_all_features(),
            "block_c": BlockC.get_all_features()
        }
    
    @classmethod
    def validate_feature_values(cls, block_name: str, values: dict) -> bool:
        """Validate all feature values for a block"""
        if block_name == "block_a":
            contracts = BlockA.get_all_features()
        elif block_name == "block_b":
            contracts = BlockB.get_all_features()
        elif block_name == "block_c":
            contracts = BlockC.get_all_features()
        else:
            raise ValueError(f"Unknown block: {block_name}")
        
        for contract in contracts:
            if contract.name in values:
                contract.validate_value(values[contract.name])
        
        return True
