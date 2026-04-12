"""
Platform Mapper - Platform Data to Block B Features

Maps platform investor profile data to Economic Constraint features (Block B).
Uses market priors for ordinal band assignment.

FORBIDDEN: Using demographics or PII for feature extraction.
"""

from typing import Dict, Optional
from enum import Enum

from .feature_contracts import BlockB, FeatureSource


class MarketPriors:
    """
    Market priors from public reports
    
    Used to contextualize investor constraints against market norms.
    These are obtained from industry reports, not user data.
    """
    
    # Capital band thresholds (in INR)
    CAPITAL_BANDS = {
        0: (0, 500_000),           # < 5L
        1: (500_000, 2_000_000),    # 5L - 20L
        2: (2_000_000, 5_000_000),  # 20L - 50L
        3: (5_000_000, 10_000_000), # 50L - 1Cr
        4: (10_000_000, float('inf'))  # > 1Cr
    }
    
    # ROI expectations (annual %)
    ROI_BANDS = {
        "low": (0, 8),       # < 8% annual
        "medium": (8, 15),   # 8-15% annual
        "high": (15, 100)    # > 15% annual
    }
    
    # Holding period (months)
    HOLDING_BANDS = {
        "short": (0, 12),    # < 1 year
        "medium": (12, 36),  # 1-3 years
        "long": (36, 1000)   # > 3 years
    }


class PlatformInvestorProfile:
    """
    Platform investor profile schema
    
    Contains economic constraints declared by investor on platform.
    NO demographics included.
    """
    
    def __init__(
        self,
        # Economic constraints
        available_capital: float,  # INR
        target_roi_annual: float,  # Percentage
        preferred_holding_months: int,
        
        # Optional metadata
        profile_verified: bool = False,
        kyc_completed: bool = False
    ):
        self.available_capital = available_capital
        self.target_roi_annual = target_roi_annual
        self.preferred_holding_months = preferred_holding_months
        self.profile_verified = profile_verified
        self.kyc_completed = kyc_completed
    
    def validate(self):
        """Validate profile data"""
        if self.available_capital < 0:
            raise ValueError("available_capital must be >= 0")
        if self.target_roi_annual < 0:
            raise ValueError("target_roi_annual must be >= 0")
        if self.preferred_holding_months < 0:
            raise ValueError("preferred_holding_months must be >= 0")


class PlatformMapper:
    """
    Maps platform data to Block B features
    
    Uses market priors to assign ordinal bands.
    """
    
    def __init__(self):
        self.market_priors = MarketPriors()
    
    def map_to_block_b(
        self,
        profile: PlatformInvestorProfile,
        city_tier: int = 2,
        co_investments: list = None
    ) -> Dict[str, any]:
        """
        Extract Block B features from platform profile
        
        Args:
            profile: PlatformInvestorProfile object
            city_tier: City tier (1/2/3)
            co_investments: Optional past investment history
            
        Returns:
            Dictionary of Block B features
        """
        profile.validate()
        
        # B1: Capital Band
        capital_band = self._assign_capital_band(profile.available_capital)
        
        # B2: Expected ROI Band
        roi_band = self._assign_roi_band(profile.target_roi_annual)
        
        # B3: Holding Period Band
        holding_band = self._assign_holding_band(profile.preferred_holding_months)
        
        # NEW BEHAVIORAL FEATURES (replacing age_band)
        
        # B4: Capital Depth Index
        capital_depth_index = self._compute_capital_depth_index(
            profile.available_capital,
            annual_income=profile.available_capital * 0.2  # Estimate 20% of capital as income
        )
        
        # B5: Ticket Size Stability (defaults for new investors)
        ticket_size_stability = 0.0 if not co_investments else self._compute_ticket_size_stability(co_investments)
        
        # B6: Holding Period Months (direct value)
        holding_period_months = profile.preferred_holding_months
        
        # B7: Behavioral Consistency Score (defaults for new investors)
        behavioral_consistency = 0.0 if not co_investments else self._compute_behavioral_consistency(co_investments)
        
        # B8: Capital Coverage Ratio
        capital_coverage_ratio = self._compute_capital_coverage_ratio(
            profile.available_capital,
            co_investments
        )
        
        block_b = {
            "capital_band": capital_band,
            "expected_roi_band": roi_band,
            "holding_period_band": holding_band,
            "capital_depth_index": capital_depth_index,
            "ticket_size_stability": ticket_size_stability,
            "holding_period_months": holding_period_months,
            "behavioral_consistency_score": behavioral_consistency,
            "capital_coverage_ratio": capital_coverage_ratio,
            "city_tier": city_tier
        }
        
        return block_b
    
    def _compute_capital_depth_index(self, capital: float, annual_income: float) -> float:
        """CDI = log(capital + income)"""
        import numpy as np
        return float(np.log(capital + annual_income + 1))
    
    def _compute_ticket_size_stability(self, co_investments: list) -> float:
        """TSS = avg / (1 + std)"""
        import numpy as np
        if not co_investments:
            return 0.0
        amounts = [inv.get("amount", 0) for inv in co_investments]
        if len(amounts) < 2:
            return float(amounts[0]) if amounts else 0.0
        return float(np.mean(amounts) / (1 + np.std(amounts)))
    
    def _compute_behavioral_consistency(self, co_investments: list) -> float:
        """Success rate"""
        if not co_investments:
            return 0.0
        total = len(co_investments)
        successful = sum(1 for inv in co_investments if inv.get("status") != "defaulted")
        return successful / total if total > 0 else 0.0
    
    def _compute_capital_coverage_ratio(self, capital: float, co_investments: list) -> float:
        """CCR = capital / avg_deal_size"""
        import numpy as np
        if not co_investments or len(co_investments) == 0:
            return 1.0  # Neutral default
        amounts = [inv.get("amount", 0) for inv in co_investments]
        avg_deal = np.mean(amounts) if amounts else capital * 0.3
        return float(capital / avg_deal) if avg_deal > 0 else 1.0
    
    def _assign_capital_band(self, capital: float) -> int:
        """
        Assign capital to ordinal band
        
        Args:
            capital: Available capital in INR
            
        Returns:
            Band number (0-4)
        """
        for band, (lower, upper) in self.market_priors.CAPITAL_BANDS.items():
            if lower <= capital < upper:
                return band
        
        return 4  # Highest band
    
    def _assign_roi_band(self, roi_annual: float) -> str:
        """
        Assign ROI expectation to band
        
        Args:
            roi_annual: Target annual ROI %
            
        Returns:
            Band name ('low', 'medium', 'high')
        """
        for band, (lower, upper) in self.market_priors.ROI_BANDS.items():
            if lower <= roi_annual < upper:
                return band
        
        return "high"  # Highest band
    
    def _assign_holding_band(self, holding_months: int) -> str:
        """
        Assign holding period to band
        
        Args:
            holding_months: Preferred holding period in months
            
        Returns:
            Band name ('short', 'medium', 'long')
        """
        for band, (lower, upper) in self.market_priors.HOLDING_BANDS.items():
            if lower <= holding_months < upper:
                return band
        
        return "long"  # Longest band
    
    def adjust_for_verification(
        self,
        block_b: Dict[str, any],
        profile: PlatformInvestorProfile
    ) -> float:
        """
        Compute confidence weight based on verification status
        
        Args:
            block_b: Extracted Block B features
            profile: Platform profile
            
        Returns:
            Confidence weight (0.0-1.0)
        """
        base_confidence = 1.0
        
        # Reduce confidence if not verified
        if not profile.profile_verified:
            base_confidence *= 0.7
        
        if not profile.kyc_completed:
            base_confidence *= 0.8
        
        return base_confidence


class PlatformDataSource:
    """
    Manages platform investor data
    
    Ensures privacy and prevents PII exposure.
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.mapper = PlatformMapper()
    
    def extract_block_b(
        self,
        investor_id_raw: str,
        profile: PlatformInvestorProfile
    ) -> tuple[Dict[str, any], float]:
        """
        Extract Block B features from platform profile
        
        Args:
            investor_id_raw: Investor identifier
            profile: Platform profile
            
        Returns:
            Tuple of (Block B features, confidence weight)
        """
        block_b = self.mapper.map_to_block_b(profile)
        confidence = self.mapper.adjust_for_verification(block_b, profile)
        
        return block_b, confidence
