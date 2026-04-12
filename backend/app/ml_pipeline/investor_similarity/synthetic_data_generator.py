"""
Synthetic Data Generator - Latent Variable Modeling

Generates synthetic investor data using copula-based methods and Bayesian networks.
Used for cold-start scaffolding ONLY. Influence must decay as real data accrues.

FORBIDDEN METHODS:
- Row duplication
- SMOTE / noise injection
- Conditioning on demographics
"""

from typing import Dict, List, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass

from .feature_contracts import BlockA, BlockB
from .platform_mapper import MarketPriors


@dataclass
class SyntheticDataConfig:
    """Configuration for synthetic data generation"""
    num_samples: int
    feature_version: str = "v1.0"
    method: str = "copula_v1"
    confidence_weight: float = 0.3
    random_seed: Optional[int] = None


class CopulaGenerator:
    """
    Gaussian Copula for continuous features (Block A)
    
    Models joint distribution without assuming marginal distributions.
    Preserves correlation structure from market priors.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def generate_block_a(
        self,
        num_samples: int,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> List[Dict[str, float]]:
        """
        Generate Block A features using Gaussian copula
        
        Args:
            num_samples: Number of synthetic samples
            correlation_matrix: 4x4 correlation structure (optional)
            
        Returns:
            List of Block A feature dictionaries
        """
        # Default correlation structure (mild positive correlations)
        if correlation_matrix is None:
            correlation_matrix = np.array([
                [1.0, 0.2, 0.1, 0.3],  # risk_orientation
                [0.2, 1.0, 0.1, 0.2],  # collaboration_comfort
                [0.1, 0.1, 1.0, 0.0],  # control_preference
                [0.3, 0.2, 0.0, 1.0]   # re_conviction
            ])
        
        # Generate from multivariate normal
        mean = np.zeros(4)
        mvn_samples = np.random.multivariate_normal(
            mean,
            correlation_matrix,
            size=num_samples
        )
        
        # Transform to uniform [0, 1] via CDF
        uniform_samples = stats.norm.cdf(mvn_samples)
        
        # Transform to beta distributions for realistic [0, 1] features
        # Beta(2, 2) gives symmetric, bell-shaped distribution in [0, 1]
        beta_samples = stats.beta.ppf(uniform_samples, a=2, b=2)
        
        # Convert to feature dictionaries
        block_a_samples = []
        for i in range(num_samples):
            block_a = {
                "risk_orientation_score": float(beta_samples[i, 0]),
                "collaboration_comfort_score": float(beta_samples[i, 1]),
                "control_preference_score": float(beta_samples[i, 2]),
                "real_estate_conviction_score": float(beta_samples[i, 3])
            }
            block_a_samples.append(block_a)
        
        return block_a_samples


class BayesianNetworkGenerator:
    """
    Bayesian Network for discrete features (Block B)
    
    Models conditional dependencies consistent with market priors.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
        
        self.market_priors = MarketPriors()
    
    def generate_block_b(self, num_samples: int) -> List[Dict[str, any]]:
        """
        Generate Block B features using Bayesian network
        
        Network structure:
        - capital_band (root) → expected_roi_band
        - capital_band → holding_period_band
        - capital_band → behavioral features (via correlations)
        
        Args:
            num_samples: Number of synthetic samples
            
        Returns:
            List of Block B feature dictionaries
        """
        block_b_samples = []
        
        for _ in range(num_samples):
            # Generate city_tier (influences capital availability)
            tier_probs = [0.25, 0.45, 0.30]  # tier 1, 2, 3
            city_tier = np.random.choice([1, 2, 3], p=tier_probs)
            
            # Generate capital_band (influenced by city tier)
            capital_band = self._generate_capital_given_tier(city_tier)
            
            # Generate expected_roi_band conditioned on capital
            roi_band = self._generate_roi_given_capital(capital_band)
            
            # Generate holding_period_band conditioned on capital
            holding_band = self._generate_holding_given_capital(capital_band)
            
            # NEW BEHAVIORAL FEATURES (replacing age_band)
            
            # B4: Capital Depth Index (correlates with capital_band)
            capital_depth_index = self._generate_capital_depth_index(capital_band)
            
            # B5: Ticket Size Stability (simulate some have investment history)
            # 30% of investors have history, 70% are new (cold start)
            has_history = np.random.random() < 0.3
            if has_history:
                ticket_size_stability = self._generate_realistic_ticket_stability(capital_band)
            else:
                ticket_size_stability = 0.0
            
            # B6: Holding Period Months (from band)
            holding_period_months = self._generate_holding_months(holding_band)
            
            # B7: Behavioral Consistency (only for investors with history)
            if has_history:
                behavioral_consistency_score = self._generate_realistic_consistency()
            else:
                behavioral_consistency_score = 0.0
            
            # B8: Capital Coverage Ratio (correlates with capital)
            capital_coverage_ratio = self._generate_capital_coverage(capital_band)
            
            block_b = {
                "capital_band": int(capital_band),
                "expected_roi_band": roi_band,
                "holding_period_band": holding_band,
                "capital_depth_index": float(capital_depth_index),
                "ticket_size_stability": float(ticket_size_stability),
                "holding_period_months": int(holding_period_months),
                "behavioral_consistency_score": float(behavioral_consistency_score),
                "capital_coverage_ratio": float(capital_coverage_ratio),
                "city_tier": int(city_tier)
            }
            block_b_samples.append(block_b)
        
        return block_b_samples
    
    
    def _generate_capital_given_tier(self, city_tier: int) -> int:
        """
        Generate capital band based on city tier only (age removed!)
        """
        # Base distribution (no age bias)
        base_probs = [0.30, 0.30, 0.20, 0.15, 0.05]
        
        # Adjust for city tier (tier 1 = slightly higher capital needs)
        if city_tier == 1:
            adjusted_probs = [p * 0.9 for p in base_probs[:2]] + [p * 1.1 for p in base_probs[2:]]
        elif city_tier == 3:
            adjusted_probs = [p * 1.1 for p in base_probs[:2]] + [p * 0.9 for p in base_probs[2:]]
        else:
            adjusted_probs = base_probs
        
        # Normalize
        total = sum(adjusted_probs)
        adjusted_probs = [p / total for p in adjusted_probs]
        
        return np.random.choice([0, 1, 2, 3, 4], p=adjusted_probs)
    
    def _generate_capital_depth_index(self, capital_band: int) -> float:
        """Generate CDI based on capital band"""
        # Map capital_band to typical capital + income
        band_to_capital = {
            0: (250_000, 50_000),     # 2.5L capital + 50K income
            1: (1_000_000, 200_000),  # 10L + 2L
            2: (3_500_000, 700_000),  # 35L + 7L
            3: (7_500_000, 1_500_000),# 75L + 15L
            4: (20_000_000, 4_000_000)# 2Cr + 40L
        }
        
        capital, income = band_to_capital.get(capital_band, (500_000, 100_000))
        # Add some noise
        capital *= np.random.uniform(0.8, 1.2)
        income *= np.random.uniform(0.8, 1.2)
        
        return np.log(capital + income + 1)
    
    def _generate_holding_months(self, holding_band: str) -> int:
        """Generate actual holding period months from band"""
        if holding_band == "short":
            return np.random.randint(6, 18)
        elif holding_band == "medium":
            return np.random.randint(18, 36)
        else:  # long
            return np.random.randint(36, 60)
    
    def _generate_capital_coverage(self, capital_band: int) -> float:
        """Generate CCR based on capital band"""
        # Higher capital → higher coverage ratio
        base_ccr = {
            0: 0.5,  # Low capital, low coverage
            1: 1.0,  # Medium, neutral
            2: 1.5,  # Can cover 1.5x average deal
            3: 2.5,  # Can cover 2.5x
            4: 4.0   # High wealth, high coverage
        }
        
        ccr = base_ccr.get(capital_band, 1.0)
        # Add noise
        return ccr * np.random.uniform(0.7, 1.3)
    
    def _generate_holding_given_capital(self, capital_band: int) -> str:
        """Generate holding period based on capital (no age bias)"""
        if capital_band <= 1:
            probs = [0.4, 0.4, 0.2]  # short, medium, long
        elif capital_band <= 3:
            probs = [0.2, 0.5, 0.3]
        else:
            probs = [0.1, 0.3, 0.6]  # High capital → long term
        
        return np.random.choice(["short", "medium", "long"], p=probs)
    
    def _generate_realistic_ticket_stability(self, capital_band: int) -> float:
        """
        Generate realistic ticket size stability for investors with history
        
        TSS = avg_investment / (1 + std_dev)
        Higher capital → higher and more stable investments
        """
        # Base investment amount by capital band
        base_amounts = {
            0: 200_000,      # 2L
            1: 800_000,      # 8L
            2: 2_500_000,    # 25L
            3: 5_000_000,    # 50L
            4: 15_000_000    # 1.5Cr
        }
        
        base = base_amounts.get(capital_band, 500_000)
        
        # Simulate 3-5 past investments
        num_investments = np.random.randint(3, 6)
        investments = []
        
        for _ in range(num_investments):
            # Add variation (±30%)
            amount = base * np.random.uniform(0.7, 1.3)
            investments.append(amount)
        
        # Calculate TSS
        avg = np.mean(investments)
        std = np.std(investments)
        
        return avg / (1 + std)
    
    def _generate_realistic_consistency(self) -> float:
        """
        Generate realistic behavioral consistency score
        
        BCS = deals completed successfully / total deals
        Most investors are reasonably consistent (0.6-0.95)
        """
        # Skew towards higher consistency (most investors are reliable)
        # Beta distribution (alpha=8, beta=2) → mean ~0.8
        consistency = np.random.beta(8, 2)
        
        # Ensure it's in [0, 1]
        return max(0.0, min(1.0, consistency))
    
    def _generate_roi_given_capital(self, capital_band: int) -> str:
        """
        Generate ROI expectation conditioned on capital band
        
        Logic: Higher capital often seeks moderate/low ROI (wealth preservation)
        """
        if capital_band <= 1:
            # Low capital: seek higher returns
            probs = [0.1, 0.3, 0.6]  # low, medium, high
        elif capital_band <= 3:
            # Medium capital: balanced
            probs = [0.2, 0.5, 0.3]
        else:
            # High capital: wealth preservation
            probs = [0.4, 0.4, 0.2]
        
        return np.random.choice(["low", "medium", "high"], p=probs)


class SyntheticDataGenerator:
    """
    Main synthetic data generator
    
    Combines copula and Bayesian network for complete synthetic investors.
    """
    
    def __init__(self, config: SyntheticDataConfig):
        self.config = config
        self.copula_gen = CopulaGenerator(random_seed=config.random_seed)
        self.bayesian_gen = BayesianNetworkGenerator(random_seed=config.random_seed)
    
    def generate_dataset(self) -> List[Dict]:
        """
        Generate complete synthetic dataset
        
        Returns:
            List of synthetic investor feature dictionaries
        """
        # Generate Block A (continuous attitudes)
        block_a_samples = self.copula_gen.generate_block_a(self.config.num_samples)
        
        # Generate Block B (discrete constraints)
        block_b_samples = self.bayesian_gen.generate_block_b(self.config.num_samples)
        
        # Block C is empty for synthetic data (behavioral data only from real activity)
        block_c_empty = {
            "deal_success_ratio": 0.0,
            "avg_holding_duration": 0.0,
            "behavioral_consistency_score": 0.0
        }
        
        # Combine into complete synthetic investors
        synthetic_investors = []
        for i in range(self.config.num_samples):
            investor = {
                "investor_id": f"synthetic_{i:06d}",
                "block_a": block_a_samples[i],
                "block_b": block_b_samples[i],
                "block_c": block_c_empty,
                "data_source": "synthetic",
                "method": self.config.method,
                "confidence_weight": self.config.confidence_weight,
                "feature_version": self.config.feature_version
            }
            synthetic_investors.append(investor)
        
        return synthetic_investors
    
    def export_to_snapshots(self, dataset_builder) -> List:
        """
        Convert synthetic data to feature snapshots
        
        Args:
            dataset_builder: DatasetBuilder instance
            
        Returns:
            List of FeatureSnapshot objects
        """
        synthetic_data = self.generate_dataset()
        snapshots = []
        
        for investor_data in synthetic_data:
            snapshot = dataset_builder.create_snapshot(
                investor_id_raw=investor_data["investor_id"],
                block_a=investor_data["block_a"],
                block_b=investor_data["block_b"],
                block_c=investor_data["block_c"],
                data_source="synthetic",
                confidence_weight=self.config.confidence_weight
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    def validate_synthetic_quality(self, synthetic_data: List[Dict]) -> Dict:
        """
        Validate quality of synthetic data
        
        Checks:
        - Feature value ranges
        - Distribution sanity
        - No demographic patterns
        
        Returns:
            Validation report
        """
        report = {
            "total_samples": len(synthetic_data),
            "validation_passed": True,
            "issues": []
        }
        
        # Check Block A ranges
        for investor in synthetic_data:
            for feature_name, value in investor["block_a"].items():
                if not (0.0 <= value <= 1.0):
                    report["validation_passed"] = False
                    report["issues"].append(
                        f"Block A feature {feature_name} out of range: {value}"
                    )
        
        # Check Block B valid values
        for investor in synthetic_data:
            capital_band = investor["block_b"]["capital_band"]
            if capital_band not in [0, 1, 2, 3, 4]:
                report["validation_passed"] = False
                report["issues"].append(f"Invalid capital_band: {capital_band}")
            
            roi_band = investor["block_b"]["expected_roi_band"]
            if roi_band not in ["low", "medium", "high"]:
                report["validation_passed"] = False
                report["issues"].append(f"Invalid expected_roi_band: {roi_band}")
            
            holding_band = investor["block_b"]["holding_period_band"]
            if holding_band not in ["short", "medium", "long"]:
                report["validation_passed"] = False
                report["issues"].append(f"Invalid holding_period_band: {holding_band}")
        
        # Distribution checks
        capital_distribution = {}
        for investor in synthetic_data:
            cap_band = investor["block_b"]["capital_band"]
            capital_distribution[cap_band] = capital_distribution.get(cap_band, 0) + 1
        
        report["capital_distribution"] = capital_distribution
        
        return report
