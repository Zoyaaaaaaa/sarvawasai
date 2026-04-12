"""
CSV Survey Processor

Processes real survey CSV data and maps to SurveyResponse schema.
CRITICAL: Strips demographics (age, location, occupation) to prevent bias.
"""

import csv
from typing import List, Dict, Tuple
import re

from .survey_mapper import SurveyResponse


class CSVSurveyProcessor:
    """
    Processes CSV survey data and maps to SurveyResponse objects.
    
    Extracts economic context features (age_band, city_tier) while
    avoiding raw demographic data.
    """
    
    # City tier mapping (Indian cities)
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
    
    def __init__(self):
        # Mapping of CSV responses to numeric scales
        self.investment_approach_map = {
            "Research extensively before deciding": 5,
            "Consult with financial advisors": 4,
            "Seek advice from family or friends": 3,
            "Go with gut feeling": 2,
            "Follow trends/recommendations": 1
        }
        
        self.pooling_comfort_map = {
            "Very comfortable": 5,
            "Comfortable": 4,
            "Neutral": 3,
            "Uncomfortable": 2,
            "Very uncomfortable": 1
        }
        
        self.re_belief_map = {
            "Yes, it's one of the best": 5,
            "Yes, it's a good option": 4,
            "Somewhat": 3,
            "Not really": 2,
            "No": 1
        }
    
    def process_csv(self, filepath: str) -> List[Tuple[str, SurveyResponse, Dict]]:
        """
        Process CSV file and extract SurveyResponse objects + economic context
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of (investor_id, SurveyResponse, economic_context) tuples
            economic_context = {"age_band": str, "city_tier": int}
        """
        survey_responses = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                try:
                    # Generate investor ID (anonymized)
                    investor_id = f"survey_respondent_{i+1:04d}"
                    
                    # Extract economic context (city tier only - age removed!)
                    city_tier = self._extract_city_tier(row.get("City / Location (India)", ""))
                    
                    economic_context = {
                        "city_tier": city_tier
                    }
                    
                    # Extract survey features (NO raw demographics!)
                    survey = self._map_row_to_survey(row)
                    
                    survey_responses.append((investor_id, survey, economic_context))
                    
                except Exception as e:
                    print(f"Warning: Skipping row {i+1} due to error: {e}")
                    continue
        
        return survey_responses
    
    def _map_row_to_survey(self, row: Dict) -> SurveyResponse:
        """
        Map CSV row to SurveyResponse object
        
        CRITICAL: This method MUST NOT use demographic columns!
        """
        
        # Extract investment priorities from "which factors matter most"
        factors_matter = row.get("When investing, which factors matter most?", "")
        priority_safety, priority_returns, priority_liquidity = self._parse_investment_factors(factors_matter)
        
        # Extract pooling comfort from direct question
        pooling_question = row.get(
            "How comfortable are you with pooling money with others for high-value purchases or investments?",
            ""
        )
        pooling_comfort = self._map_pooling_comfort(pooling_question)
        
        # Extract trust enablers from collaboration question
        collaboration_factors = row.get(
            "Which of the following would make you more confident when collaborating financially with others?",
            ""
        )
        trust_transparency, trust_track_record, trust_legal = self._parse_trust_enablers(collaboration_factors)
        
        # Extract control preference from investment approach
        approach = row.get("How do you usually approach high-value investments?", "")
        prefer_hands_on, trust_professional = self._parse_investment_approach(approach)
        
        # Extract RE conviction
        re_belief = row.get("Do you consider real estate a good way to build wealth?", "")
        re_vs_stocks = self._map_re_belief(re_belief)
        
        # Home buying plans indicate long-term belief
        home_plans = row.get("Do you plan to buy a home in the next 1–5 years?", "")
        re_long_term = 4 if "Yes" in home_plans else 3
        
        # Create SurveyResponse
        survey = SurveyResponse(
            priority_safety=priority_safety,
            priority_returns=priority_returns,
            priority_liquidity=priority_liquidity,
            pooling_comfort_strangers=max(1, pooling_comfort - 1),  # Lower for strangers
            pooling_comfort_verified=pooling_comfort,
            pooling_comfort_friends=min(5, pooling_comfort + 1),  # Higher for friends
            prefer_hands_on=prefer_hands_on,
            trust_professional_management=trust_professional,
            re_vs_stocks=re_vs_stocks,
            re_long_term_belief=re_long_term,
            trust_enables_transparency=trust_transparency,
            trust_enables_track_record=trust_track_record,
            trust_enables_legal_protection=trust_legal
        )
        
        return survey
    
    def _parse_investment_factors(self, factors_text: str) -> Tuple[int, int, int]:
        """Parse investment factors into safety, returns, liquidity priorities"""
        factors_lower = factors_text.lower()
        
        # Default balanced
        safety = 3
        returns = 3
        liquidity = 3
        
        # Adjust based on mentions
        if "safety" in factors_lower or "secure" in factors_lower or "risk" in factors_lower:
            safety = 5
            returns = 2
        
        if "return" in factors_lower or "profit" in factors_lower or "gain" in factors_lower:
            returns = 5
            safety = 2
        
        if "liquid" in factors_lower or "withdraw" in factors_lower:
            liquidity = 4
        
        return safety, returns, liquidity
    
    def _map_pooling_comfort(self, pooling_text: str) -> int:
        """Map pooling comfort text to 1-5 scale"""
        pooling_lower = pooling_text.lower()
        
        if "very comfortable" in pooling_lower:
            return 5
        elif "comfortable" in pooling_lower:
            return 4
        elif "neutral" in pooling_lower:
            return 3
        elif "uncomfortable" in pooling_lower and "very" not in pooling_lower:
            return 2
        else:
            return 1
    
    def _parse_trust_enablers(self, trust_text: str) -> Tuple[bool, bool, bool]:
        """Parse trust enablers from text"""
        trust_lower = trust_text.lower()
        
        transparency = "transparen" in trust_lower or "clear" in trust_lower
        track_record = "track record" in trust_lower or "history" in trust_lower or "proven" in trust_lower
        legal = "legal" in trust_lower or "contract" in trust_lower or "protection" in trust_lower
        
        return transparency, track_record, legal
    
    def _parse_investment_approach(self, approach_text: str) -> Tuple[int, int]:
        """Parse investment approach into hands-on vs delegation preference"""
        approach_lower = approach_text.lower()
        
        # Default balanced
        hands_on = 3
        trust_professional = 3
        
        if "research extensively" in approach_lower or "myself" in approach_lower:
            hands_on = 5
            trust_professional = 2
        
        if "advisor" in approach_lower or "professional" in approach_lower:
            hands_on = 2
            trust_professional = 5
        
        if "family" in approach_lower or "friends" in approach_lower:
            hands_on = 3
            trust_professional = 3
        
        return hands_on, trust_professional
    
    def _map_re_belief(self, re_text: str) -> int:
        """Map real estate belief to 1-5 scale"""
        re_lower = re_text.lower()
        
        if "best" in re_lower:
            return 5
        elif "good" in re_lower and "yes" in re_lower:
            return 4
        elif "somewhat" in re_lower:
            return 3
        elif "not really" in re_lower:
            return 2
        else:
            return 1
    
    def _extract_age_band(self, age_text: str) -> str:
        """
        Extract age band from age group text
        
        Maps to: early (<30), mid (30-49), late (50+)
        """
        age_lower = age_text.lower()
        
        # Extract numeric age if present
        import re
        numbers = re.findall(r'\d+', age_text)
        
        if not numbers:
            return "mid"  # Default
        
        age = int(numbers[0])
        
        if age < 30:
            return "early"
        elif age < 50:
            return "mid"
        else:
            return "late"
    
    def _extract_city_tier(self, city_text: str) -> int:
        """
        Extract city tier from city/location text
        
        Returns: 1 (metro), 2 (tier-2), 3 (tier-3)
        """
        city_lower = city_text.lower().strip()
        
        # Check tier 1 cities
        for tier1 in self.TIER_1_CITIES:
            if tier1 in city_lower:
                return 1
        
        # Check tier 2 cities
        for tier2 in self.TIER_2_CITIES:
            if tier2 in city_lower:
                return 2
        
        # Default to tier 3
        return 3
    
    def extract_feature_distributions(
        self,
        survey_responses: List[Tuple[str, SurveyResponse, Dict]],
        survey_mapper
    ) -> Dict:
        """
        Extract feature distributions from real survey data
        
        Used to calibrate synthetic data generation.
        
        Returns:
            Dictionary with means, stds for Block A features
        """
        import numpy as np
        
        # Extract Block A features from all surveys
        all_features = []
        for investor_id, survey, economic_context in survey_responses:
            block_a = survey_mapper.map_to_block_a(survey)
            all_features.append([
                block_a["risk_orientation_score"],
                block_a["collaboration_comfort_score"],
                block_a["control_preference_score"],
                block_a["real_estate_conviction_score"]
            ])
        
        all_features = np.array(all_features)
        
        # Compute statistics
        distributions = {
            "means": all_features.mean(axis=0).tolist(),
            "stds": all_features.std(axis=0).tolist(),
            "correlation_matrix": np.corrcoef(all_features.T).tolist(),
            "num_samples": len(survey_responses)
        }
        
        return distributions
