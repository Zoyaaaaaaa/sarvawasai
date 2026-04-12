"""
Similarity Engine - Pre-ML Similarity Computation

Implements rule-based similarity logic with hard filters and soft scoring.
Models are explicitly replaceable - this is the baseline similarity system.

Similarity Formula:
  Similarity = 0.35 * attitude_similarity(Block A)
             + 0.40 * constraint_similarity(Block B)
             + 0.25 * behavioral_similarity(Block C, defaults to 0)
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass

from .dataset_builder import FeatureSnapshot


@dataclass
class SimilarityResult:
    """Result of similarity computation"""
    investor1_id: str
    investor2_id: str
    total_similarity: float
    attitude_similarity: float
    constraint_similarity: float
    behavioral_similarity: float
    failed_hard_filters: List[str]
    
    def to_dict(self) -> dict:
        return {
            "investor1_id": self.investor1_id,
            "investor2_id": self.investor2_id,
            "total_similarity": self.total_similarity,
            "breakdown": {
                "attitude": self.attitude_similarity,
                "constraint": self.constraint_similarity,
                "behavioral": self.behavioral_similarity
            },
            "failed_filters": self.failed_hard_filters
        }


class SimilarityEngine:
    """
    Pre-ML similarity engine
    
    Uses hard filters and weighted soft scoring to compute investor similarity.
    Designed to be interpretable and bias-free.
    """
    
    # Similarity weights (per PRD)
    WEIGHT_ATTITUDE = 0.35
    WEIGHT_CONSTRAINT = 0.40
    WEIGHT_BEHAVIORAL = 0.25
    
    def __init__(
        self,
        capital_band_tolerance: int = 1,
        holding_period_tolerance: int = 1
    ):
        """
        Initialize similarity engine
        
        Args:
            capital_band_tolerance: Max allowed |capital_band difference|
            holding_period_tolerance: Max allowed |holding_period difference|
        """
        self.capital_band_tolerance = capital_band_tolerance
        self.holding_period_tolerance = holding_period_tolerance
    
    def compute_similarity(
        self,
        snapshot1: FeatureSnapshot,
        snapshot2: FeatureSnapshot
    ) -> SimilarityResult:
        """
        Compute similarity between two investors
        
        Args:
            snapshot1: First investor snapshot
            snapshot2: Second investor snapshot
            
        Returns:
            SimilarityResult with scores and filter status
        """
        # Apply hard filters
        failed_filters = self._apply_hard_filters(snapshot1, snapshot2)
        
        # Compute soft similarities
        attitude_sim = self._compute_attitude_similarity(snapshot1, snapshot2)
        constraint_sim = self._compute_constraint_similarity(snapshot1, snapshot2)
        behavioral_sim = self._compute_behavioral_similarity(snapshot1, snapshot2)
        
        # Weighted total
        total_sim = (
            self.WEIGHT_ATTITUDE * attitude_sim +
            self.WEIGHT_CONSTRAINT * constraint_sim +
            self.WEIGHT_BEHAVIORAL * behavioral_sim
        )
        
        # If hard filters failed, set similarity to 0
        if failed_filters:
            total_sim = 0.0
        
        result = SimilarityResult(
            investor1_id=snapshot1.investor_id,
            investor2_id=snapshot2.investor_id,
            total_similarity=float(total_sim),
            attitude_similarity=float(attitude_sim),
            constraint_similarity=float(constraint_sim),
            behavioral_similarity=float(behavioral_sim),
            failed_hard_filters=failed_filters
        )
        
        return result
    
    def _apply_hard_filters(
        self,
        snapshot1: FeatureSnapshot,
        snapshot2: FeatureSnapshot
    ) -> List[str]:
        """
        Apply hard filters for compatibility
        
        Returns:
            List of failed filter names (empty if all pass)
        """
        failed = []
        
        # Hard Filter 1: Capital band difference
        capital1 = snapshot1.block_b.get("capital_band", 0)
        capital2 = snapshot2.block_b.get("capital_band", 0)
        
        if abs(capital1 - capital2) > self.capital_band_tolerance:
            failed.append("capital_band_mismatch")
        
        # Hard Filter 2: Holding period compatibility
        holding_map = {"short": 0, "medium": 1, "long": 2}
        holding1 = holding_map.get(snapshot1.block_b.get("holding_period_band", "medium"), 1)
        holding2 = holding_map.get(snapshot2.block_b.get("holding_period_band", "medium"), 1)
        
        if abs(holding1 - holding2) > self.holding_period_tolerance:
            failed.append("holding_period_mismatch")
        
        return failed
    
    def _compute_attitude_similarity(
        self,
        snapshot1: FeatureSnapshot,
        snapshot2: FeatureSnapshot
    ) -> float:
        """
        Compute Block A (attitude) similarity using cosine similarity
        
        Returns:
            Similarity score [0, 1]
        """
        # Extract Block A vectors
        vec1 = self._block_a_to_vector(snapshot1.block_a)
        vec2 = self._block_a_to_vector(snapshot2.block_a)
        
        # Cosine similarity
        similarity = self._cosine_similarity(vec1, vec2)
        
        # Weight by confidence
        avg_confidence = (snapshot1.confidence_weight + snapshot2.confidence_weight) / 2
        weighted_similarity = similarity * avg_confidence
        
        return weighted_similarity
    
    def _compute_constraint_similarity(
        self,
        snapshot1: FeatureSnapshot,
        snapshot2: FeatureSnapshot
    ) -> float:
        """
        Compute Block B (constraint) similarity using ordinal distance
        
        Returns:
            Similarity score [0, 1]
        """
        # Capital band similarity (already checked in hard filter, so normalized)
        capital1 = snapshot1.block_b.get("capital_band", 0)
        capital2 = snapshot2.block_b.get("capital_band", 0)
        capital_sim = 1.0 - abs(capital1 - capital2) / 4.0  # Normalized by max difference
        
        # ROI band similarity
        roi_map = {"low": 0, "medium": 1, "high": 2}
        roi1 = roi_map.get(snapshot1.block_b.get("expected_roi_band", "medium"), 1)
        roi2 = roi_map.get(snapshot2.block_b.get("expected_roi_band", "medium"), 1)
        roi_sim = 1.0 - abs(roi1 - roi2) / 2.0
        
        # Holding period similarity (already checked in hard filter)
        holding_map = {"short": 0, "medium": 1, "long": 2}
        holding1 = holding_map.get(snapshot1.block_b.get("holding_period_band", "medium"), 1)
        holding2 = holding_map.get(snapshot2.block_b.get("holding_period_band", "medium"), 1)
        holding_sim = 1.0 - abs(holding1 - holding2) / 2.0
        
        # Weighted average
        constraint_sim = 0.4 * capital_sim + 0.3 * roi_sim + 0.3 * holding_sim
        
        return constraint_sim
    
    def _compute_behavioral_similarity(
        self,
        snapshot1: FeatureSnapshot,
        snapshot2: FeatureSnapshot
    ) -> float:
        """
        Compute Block C (behavioral) similarity
        
        NOTE: Defaults to 0 until behavioral data accrues.
        
        Returns:
            Similarity score [0, 1]
        """
        # Check if behavioral data exists
        has_data1 = snapshot1.block_c.get("deal_success_ratio", 0) > 0
        has_data2 = snapshot2.block_c.get("deal_success_ratio", 0) > 0
        
        if not (has_data1 and has_data2):
            return 0.0  # Default to 0 (no behavioral data)
        
        # Extract behavioral vectors
        vec1 = self._block_c_to_vector(snapshot1.block_c)
        vec2 = self._block_c_to_vector(snapshot2.block_c)
        
        # Cosine similarity
        return self._cosine_similarity(vec1, vec2)
    
    def _block_a_to_vector(self, block_a: Dict[str, float]) -> np.ndarray:
        """Convert Block A to numpy vector"""
        return np.array([
            block_a.get("risk_orientation_score", 0.0),
            block_a.get("collaboration_comfort_score", 0.0),
            block_a.get("control_preference_score", 0.0),
            block_a.get("real_estate_conviction_score", 0.0)
        ])
    
    def _block_c_to_vector(self, block_c: Dict[str, float]) -> np.ndarray:
        """Convert Block C to numpy vector"""
        return np.array([
            block_c.get("deal_success_ratio", 0.0),
            block_c.get("avg_holding_duration", 0.0) / 365.0,  # Normalize days to years
            block_c.get("behavioral_consistency_score", 0.0)
        ])
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors
        
        Returns:
            Similarity [0, 1]
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity in [-1, 1]
        cos_sim = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Transform to [0, 1]
        return (cos_sim + 1) / 2
    
    def find_similar_investors(
        self,
        target_snapshot: FeatureSnapshot,
        candidate_snapshots: List[FeatureSnapshot],
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[SimilarityResult]:
        """
        Find most similar investors to target
        
        Args:
            target_snapshot: Target investor
            candidate_snapshots: Pool of candidate investors
            top_k: Number of top matches to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of SimilarityResults, sorted by similarity (descending)
        """
        # Compute similarity with all candidates
        similarities = []
        for candidate in candidate_snapshots:
            # Skip self-comparison
            if candidate.investor_id == target_snapshot.investor_id:
                continue
            
            result = self.compute_similarity(target_snapshot, candidate)
            
            # Filter by minimum similarity
            if result.total_similarity >= min_similarity:
                similarities.append(result)
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x.total_similarity, reverse=True)
        
        # Return top K
        return similarities[:top_k]
    
    def compute_similarity_matrix(
        self,
        snapshots: List[FeatureSnapshot]
    ) -> np.ndarray:
        """
        Compute pairwise similarity matrix for all investors
        
        Args:
            snapshots: List of investor snapshots
            
        Returns:
            NxN similarity matrix
        """
        n = len(snapshots)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    matrix[i, j] = 1.0
                else:
                    result = self.compute_similarity(snapshots[i], snapshots[j])
                    matrix[i, j] = result.total_similarity
                    matrix[j, i] = result.total_similarity
        
        return matrix
