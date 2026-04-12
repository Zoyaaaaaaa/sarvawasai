"""
Ranking Data Generator

Generates query groups for pairwise ranking training.
Uses pre-ML similarity engine to create relevance labels.
"""

import sys
from pathlib import Path
import numpy as np
import random
from typing import List, Tuple, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine


class RankingDataGenerator:
    """
    Generate query-candidate groups for ranking models
    
    Each query has:
    - One query investor
    - N candidate investors
    - Relevance labels (0-4) for each candidate
    """
    
    def __init__(self, snapshots: List, similarity_engine: SimilarityEngine):
        self.snapshots = snapshots
        self.engine = similarity_engine
        self.n_investors = len(snapshots)
    
    def _compute_relevance_label(self, similarity_score: float) -> int:
        """
        Map similarity score to relevance label (0-4)
        
        Args:
            similarity_score: Continuous score from pre-ML engine
            
        Returns:
            Relevance label: 4 (perfect), 3 (excellent), 2 (good), 1 (fair), 0 (poor)
        """
        if similarity_score >= 0.8:
            return 4
        elif similarity_score >= 0.6:
            return 3
        elif similarity_score >= 0.4:
            return 2
        elif similarity_score >= 0.2:
            return 1
        else:
            return 0
    
    def generate_query_groups(
        self,
        n_queries: int = 1000,
        candidates_per_query: int = 100,
        seed: int = 42
    ) -> Tuple[List, List, List, np.ndarray]:
        """
        Generate ranking training data with HARD NEGATIVE SAMPLING
        
        Strategy:
        - 30% same capital band (confusers - hard to distinguish)
        - 30% adjacent capital bands (hard negatives)
        - 40% random (easy negatives)
        
        This forces model to learn fine-grained differences!
        
        Args:
            n_queries: Number of query investors
            candidates_per_query: Candidates to rank per query
            seed: Random seed
            
        Returns:
            (queries, all_candidates, all_relevances, group_sizes)
        """
        random.seed(seed)
        np.random.seed(seed)
        
        print(f"Generating {n_queries} queries × {candidates_per_query} candidates...")
        print("  Using HARD NEGATIVE SAMPLING for challenging task")
        
        # Build index by capital band
        by_capital_band = self._build_capital_band_index()
        
        # Sample query investors (stratified)
        query_investors = self._sample_stratified_queries(n_queries)
        
        all_candidates = []
        all_relevances = []
        group_sizes = []
        
        for i, query in enumerate(query_investors):
            # Get query's capital band
            query_band = query.block_b.get('capital_band', 0)
            
            # Hard negative sampling
            candidates = self._sample_hard_negatives(
                query,
                query_band,
                by_capital_band,
                n_candidates=candidates_per_query
            )
            
            # Compute relevance labels
            relevances = []
            for candidate in candidates:
                result = self.engine.compute_similarity(query, candidate)
                score = result.total_similarity
                label = self._compute_relevance_label(score)
                relevances.append(label)
            
            # Store
            all_candidates.extend(candidates)
            all_relevances.extend(relevances)
            group_sizes.append(len(candidates))
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i+1}/{n_queries} queries...")
        
        print(f"\n✓ Generated {len(all_candidates):,} total examples")
        print(f"  {n_queries} query groups")
        print(f"  Avg {np.mean(group_sizes):.1f} candidates per query")
        
        # Analyze relevance distribution
        rel_counts = np.bincount(all_relevances, minlength=5)
        print(f"\n  Relevance distribution:")
        for label, count in enumerate(rel_counts):
            pct = count / len(all_relevances) * 100
            bar = "█" * int(pct / 2)
            print(f"    {label}: {bar} {count:,} ({pct:.1f}%)")
        
        # Convert to group array for XGBoost
        group_array = np.array(group_sizes)
        
        return query_investors, all_candidates, all_relevances, group_array
    
    def _build_capital_band_index(self) -> dict:
        """Build index of investors by capital band"""
        by_band = {}
        for snap in self.snapshots:
            band = snap.block_b.get('capital_band', 0)
            if band not in by_band:
                by_band[band] = []
            by_band[band].append(snap)
        return by_band
    
    def _sample_hard_negatives(
        self,
        query,
        query_band: int,
        by_capital_band: dict,
        n_candidates: int
    ) -> List:
        """
        Sample candidates with BALANCED positive + hard negative mining
        
        Strategy:
        - 20% very similar (POSITIVE - same band + similar preferences)
        - 30% same capital band (CONFUSERS)
        - 20% adjacent capital bands (HARD NEGATIVES)
        - 30% random (EASY NEGATIVES)
        
        Args:
            query: Query investor
            query_band: Query's capital band
            by_capital_band: Index of investors by band
            n_candidates: Total candidates to sample
            
        Returns:
            List of candidate snapshots
        """
        candidates = []
        
        # 20% POSITIVE EXAMPLES (same band + similar preferences)
        # This will generate labels 3-4!
        n_positive = int(n_candidates * 0.2)
        positive_samples = self._sample_similar_investors(
            query,
            query_band,
            by_capital_band,
            n_positive
        )
        candidates.extend(positive_samples)
        
        # 30% same capital band but different preferences (CONFUSERS)
        n_same = int(n_candidates * 0.3)
        same_band = by_capital_band.get(query_band, [])
        same_band = [s for s in same_band 
                    if s.investor_id != query.investor_id 
                    and s not in candidates]
        if same_band:
            candidates.extend(random.sample(
                same_band,
                min(n_same, len(same_band))
            ))
        
        # 20% adjacent capital bands (HARD NEGATIVES)
        n_adjacent = int(n_candidates * 0.2)
        adjacent_bands = [query_band - 1, query_band + 1]
        adjacent_investors = []
        for band in adjacent_bands:
            if band in by_capital_band:
                adjacent_investors.extend(by_capital_band[band])
        
        if adjacent_investors:
            candidates.extend(random.sample(
                adjacent_investors,
                min(n_adjacent, len(adjacent_investors))
            ))
        
        # 30% random (EASY NEGATIVES)
        n_random = n_candidates - len(candidates)
        remaining = [s for s in self.snapshots 
                    if s not in candidates and s.investor_id != query.investor_id]
        
        if remaining:
            candidates.extend(random.sample(
                remaining,
                min(n_random, len(remaining))
            ))
        
        # Shuffle to avoid position bias
        random.shuffle(candidates)
        
        return candidates[:n_candidates]
    
    def _sample_similar_investors(
        self,
        query,
        query_band: int,
        by_capital_band: dict,
        n_samples: int
    ) -> List:
        """
        Sample VERY SIMILAR investors for positive examples
        
        Criteria for similarity:
        - Same capital band
        - Similar holding period preference
        - Similar ROI expectation
        
        This creates labels 3-4 (excellent/perfect matches)
        """
        same_band = by_capital_band.get(query_band, [])
        same_band = [s for s in same_band if s.investor_id != query.investor_id]
        
        if not same_band:
            return []
        
        # Get query preferences
        query_roi = query.block_b.get('expected_roi_band', 'medium')
        query_holding = query.block_b.get('holding_period_band', 'medium')
        
        # Score candidates by similarity
        scored_candidates = []
        for candidate in same_band:
            cand_roi = candidate.block_b.get('expected_roi_band', 'medium')
            cand_holding = candidate.block_b.get('holding_period_band', 'medium')
            
            similarity_score = 0
            if cand_roi == query_roi:
                similarity_score += 1
            if cand_holding == query_holding:
                similarity_score += 1
            
            scored_candidates.append((similarity_score, candidate))
        
        # Sort by similarity (descending)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N most similar
        top_similar = [cand for score, cand in scored_candidates[:n_samples]]
        
        return top_similar
    
    def _sample_stratified_queries(self, n_queries: int) -> List:
        """Sample queries stratified by capital band"""
        
        # Group by capital band
        by_capital = {}
        for snap in self.snapshots:
            band = snap.block_b.get('capital_band', 0)
            if band not in by_capital:
                by_capital[band] = []
            by_capital[band].append(snap)
        
        # Sample proportionally
        queries = []
        queries_per_band = n_queries // len(by_capital)
        
        for band, snaps in by_capital.items():
            n_sample = min(queries_per_band, len(snaps))
            queries.extend(random.sample(snaps, n_sample))
        
        # Fill remaining with random samples
        while len(queries) < n_queries:
            queries.append(random.choice(self.snapshots))
        
        return queries[:n_queries]


if __name__ == "__main__":
    print("=" * 70)
    print("Ranking Data Generator Test")
    print("=" * 70)
    
    # Load dataset
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"\n✓ Loaded {len(snapshots)} snapshots")
    
    # Initialize engine
    engine = SimilarityEngine()
    
    # Generate small sample
    generator = RankingDataGenerator(snapshots, engine)
    queries, candidates, relevances, groups = generator.generate_query_groups(
        n_queries=10,
        candidates_per_query=50,
        seed=42
    )
    
    print(f"\nSample query group sizes: {groups[:5]}")
    print(f"Sample relevances: {relevances[:10]}")
