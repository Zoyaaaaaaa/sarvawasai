"""
MongoDB to Feature Mapper

Maps InvestorProfile from MongoDB to Block B features.
Computes behavioral metrics from historical data.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass  
class InvestorProfileMongo:
    """Mirror of MongoDB InvestorProfile schema"""
    available_capital: float
    annual_income: float
    min_investment_per_deal: float
    max_investment_per_deal: float
    max_holding_period_months: int
    co_investments: list  # List of past investments
    risk_appetite: str  # low, medium, high
    expected_roi: float
    preferred_locations: list
    
    # From populated User
    city: str  # For city_tier mapping


class MongoFeatureMapper:
    """
    Extracts Block B features from MongoDB InvestorProfile
    
    Computes behavioral features without demographics
    """
    
    # City tier mapping (same as CSV processor)
    TIER_1_CITIES = [
        "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", 
        "chennai", "kolkata", "pune", "ahmedabad"
    ]
    
    TIER_2_CITIES = [
        "jaipur", "lucknow", "kanpur", "nagpur", "indore", "thane",
        "bhopal", "visakhapatnam", "pimpri", "patna", "vadodara",
        "ghaziabad", "ludhiana", "agra", "nashik", "faridabad",
        "meerut", "rajkot", "kalyan", "vasai", "varanasi",
        "srinagar", "aurangabad", "dhanbad", "amritsar", "navi mumbai",
        "allahabad", "ranchi", "howrah", "coimbatore", "jabalpur"
    ]
    
    def extract_block_b(self, profile: InvestorProfileMongo) -> Dict:
        """
        Extract all Block B features from investor profile
        
        Returns:
            Dictionary of Block B features
        """
        
        # B1: Capital Band (existing)
        capital_band = self._assign_capital_band(profile.available_capital)
        
        # B2: ROI Band (existing)
        roi_band = self._assign_roi_band(profile.expected_roi)
        
        # B3: Holding Period Band (existing)
        holding_band = self._assign_holding_band(profile.max_holding_period_months)
        
        # B4: Capital Depth Index (NEW - replaces age!)
        capital_depth_index = self._compute_capital_depth_index(
            profile.available_capital,
            profile.annual_income
        )
        
        # B5: Ticket Size Stability (NEW)
        ticket_size_stability = self._compute_ticket_size_stability(profile.co_investments)
        
        # B6: Holding Period Months (NEW - raw value)
        holding_period_months = profile.max_holding_period_months
        
        # B7: Behavioral Consistency Score (NEW)
        behavioral_consistency = self._compute_behavioral_consistency(profile.co_investments)
        
        # B8: Capital Coverage Ratio (NEW)
        capital_coverage_ratio = self._compute_capital_coverage_ratio(
            profile.available_capital,
            profile.co_investments
        )
        
        # B9: City Tier (existing)
        city_tier = self._extract_city_tier(profile.city)
        
        return {
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
    
    def _compute_capital_depth_index(self, capital: float, annual_income: float) -> float:
        """
        CDI = log(availableCapital + annualIncome)
        
        Measures financial accumulation maturity WITHOUT age.
        """
        return np.log(capital + annual_income + 1)  # +1 to avoid log(0)
    
    def _compute_ticket_size_stability(self, co_investments: list) -> float:
        """
        TSS = avg_investment / (1 + std_dev)
        
        Measures investment consistency. High = stable investor.
        """
        if not co_investments or len(co_investments) == 0:
            return 0.0  # No history
        
        amounts = [inv.get("investedAmount", 0) for inv in co_investments]
        
        if len(amounts) < 2:
            return amounts[0] if amounts else 0.0
        
        avg = np.mean(amounts)
        std = np.std(amounts)
        
        return avg / (1 + std)
    
    def _compute_behavioral_consistency(self, co_investments: list) -> float:
        """
        BCS = 1 - normalized(variance in deal outcomes)
        
        Measures reliability. High = mature investor behavior.
        """
        if not co_investments or len(co_investments) == 0:
            return 0.0  # No history
        
        # Count outcomes
        active = sum(1 for inv in co_investments if inv.get("status") == "active")
        closed = sum(1 for inv in co_investments if inv.get("status") == "closed")
        defaulted = sum(1 for inv in co_investments if inv.get("status") == "defaulted")
        
        total = len(co_investments)
        
        # Score: high if mostly active/closed, low if many defaults
        success_rate = (active + closed) / total if total > 0 else 0
        
        # Penalize variance in holding periods (if available)
        # For now, use simple success rate
        return success_rate
    
    def _compute_capital_coverage_ratio(self, capital: float, co_investments: list) -> float:
        """
        CCR = availableCapital / avg_deal_size
        
        High CCR = can solo deals (fewer co-investors needed)
        """
        if not co_investments or len(co_investments) == 0:
            # Use min/max investment as proxy
            return 1.0  # Neutral default
        
        amounts = [inv.get("investedAmount", 0) for inv in co_investments]
        avg_deal = np.mean(amounts) if amounts else 1
        
        return capital / avg_deal if avg_deal > 0 else 0
    
    def _assign_capital_band(self, capital: float) -> int:
        """Assign capital to band 0-4"""
        if capital < 500_000:
            return 0
        elif capital < 2_000_000:
            return 1
        elif capital < 5_000_000:
            return 2
        elif capital < 10_000_000:
            return 3
        else:
            return 4
    
    def _assign_roi_band(self, roi: float) -> str:
        """Assign ROI to low/medium/high"""
        if roi < 10:
            return "low"
        elif roi < 15:
            return "medium"
        else:
            return "high"
    
    def _assign_holding_band(self, months: int) -> str:
        """Assign holding period to short/medium/long"""
        if months < 18:
            return "short"
        elif months < 36:
            return "medium"
        else:
            return "long"
    
    def _extract_city_tier(self, city: str) -> int:
        """Extract city tier from city name"""
        city_lower = city.lower().strip()
        
        for tier1 in self.TIER_1_CITIES:
            if tier1 in city_lower:
                return 1
        
        for tier2 in self.TIER_2_CITIES:
            if tier2 in city_lower:
                return 2
        
        return 3
