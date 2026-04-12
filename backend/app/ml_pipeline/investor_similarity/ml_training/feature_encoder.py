"""
Feature Encoder for ML Training

Converts investor features to ML-ready format with one-hot encoding.
"""

import numpy as np
import pandas as pd
from typing import Dict, List


class InvestorFeatureEncoder:
    """
    Encodes investor features for ML training
    
    Handles:
    - One-hot encoding for categorical features
    - Continuous feature normalization
    - Feature vector generation
    """
    
    def __init__(self):
        # Define categorical features for one-hot encoding
        self.categorical_features = {
            'expected_roi_band': ['low', 'medium', 'high'],
            'holding_period_band': ['short', 'medium', 'long'],
            'city_tier': [1, 2, 3]
        }
        
        # Continuous features (use as-is)
        self.continuous_features = [
            # Block A
            'risk_orientation_score',
            'collaboration_comfort_score',
            'control_preference_score',
            'real_estate_conviction_score',
            # Block B
            'capital_band',  # Treat as ordinal continuous
            'capital_depth_index',
            'ticket_size_stability',
            'holding_period_months',
            'behavioral_consistency_score',
            'capital_coverage_ratio'
        ]
        
        # Feature names after encoding
        self.feature_names = None
        self._build_feature_names()
    
    def _build_feature_names(self):
        """Build ordered feature names list"""
        names = []
        
        # Continuous features first
        names.extend(self.continuous_features)
        
        # One-hot encoded features
        for feat_name, values in self.categorical_features.items():
            for val in values:
                names.append(f"{feat_name}_{val}")
        
        self.feature_names = names
    
    def encode_snapshot(self, snapshot) -> np.ndarray:
        """
        Encode a single investor snapshot to feature vector
        
        Args:
            snapshot: FeatureSnapshot object
            
        Returns:
            numpy array of shape (n_features,)
        """
        features = []
        
        # Extract continuous features
        for feat_name in self.continuous_features:
            if feat_name in snapshot.block_a:
                value = snapshot.block_a[feat_name]
            elif feat_name in snapshot.block_b:
                value = snapshot.block_b[feat_name]
            else:
                value = 0.0
            features.append(float(value))
        
        # One-hot encode categorical features
        for feat_name, possible_values in self.categorical_features.items():
            actual_value = snapshot.block_b.get(feat_name)
            
            # Create one-hot vector
            one_hot = [1.0 if val == actual_value else 0.0 for val in possible_values]
            features.extend(one_hot)
        
        return np.array(features)
    
    def encode_pair(self, snapshot1, snapshot2) -> np.ndarray:
        """
        Encode an investor pair for ranking
        
        CRITICAL FIX: Use ONLY raw features, no diff/product!
        - OLD (label leakage): [i1, i2, diff, product] ← encoded similarity
        - NEW (correct): [i1, i2] ← let model learn interactions
        
        Args:
            snapshot1: First investor snapshot
            snapshot2: Second investor snapshot
            
        Returns:
            numpy array of shape (n_features * 2,) - raw features only
        """
        vec1 = self.encode_snapshot(snapshot1)
        vec2 = self.encode_snapshot(snapshot2)
        
        # ONLY concatenate raw features
        # Model must learn what makes investors similar
        pair_features = np.concatenate([vec1, vec2])
        
        return pair_features
    
    def encode_batch(self, snapshots: List) -> np.ndarray:
        """
        Encode multiple snapshots to matrix
        
        Args:
            snapshots: List of FeatureSnapshot objects
            
        Returns:
            numpy array of shape (n_samples, n_features)
        """
        vectors = [self.encode_snapshot(s) for s in snapshots]
        return np.array(vectors)
    
    def get_feature_names(self) -> List[str]:
        """Return ordered list of feature names"""
        return self.feature_names
    
    def get_num_features(self) -> int:
        """Return total number of features after encoding"""
        return len(self.feature_names)


if __name__ == "__main__":
    print("Feature Encoder Test")
    print("=" * 60)
    
    encoder = InvestorFeatureEncoder()
    
    print(f"Total base features: {encoder.get_num_features()}")
    print(f"\nFeature names:")
    for i, name in enumerate(encoder.get_feature_names(), 1):
        print(f"  {i}. {name}")
    
    print(f"\n✅ FIX APPLIED: Pair encoding now uses ONLY raw features")
    print(f"   Pair feature count: {encoder.get_num_features() * 2}")
    print(f"   Format: [investor1_features, investor2_features]")
    print(f"\n   NO diff, NO product → Model must LEARN similarity!")
    print(f"   This prevents label leakage.")
