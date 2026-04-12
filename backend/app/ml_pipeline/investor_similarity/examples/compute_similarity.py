"""
Example: Compute Similarity

Demonstrates how to use the similarity engine to find similar investors.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine


def main():
    print("=" * 60)
    print("Investor Similarity System - Similarity Computation")
    print("=" * 60)
    
    # Load dataset
    print("\n[1/3] Loading dataset...")
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",  # Updated to match scale_to_10k output
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots)} snapshots")
    
    # Initialize similarity engine
    print("\n[2/3] Initializing similarity engine...")
    similarity_engine = SimilarityEngine(
        capital_band_tolerance=1,
        holding_period_tolerance=1
    )
    print("  ✓ Similarity engine ready")
    
    # Select a target investor
    if len(snapshots) < 2:
        print("\n❌ Need at least 2 investors to compute similarity")
        return
    
    target_investor = snapshots[0]
    candidates = snapshots[1:]
    
    print(f"\n[3/3] Finding similar investors for target...")
    print(f"Target investor ID: {target_investor.investor_id}")
    print(f"Target features:")
    print(f"  Block A: {target_investor.block_a}")
    print(f"  Block B: {target_investor.block_b}")
    
    # Find top similar investors
    similar_investors = similarity_engine.find_similar_investors(
        target_snapshot=target_investor,
        candidate_snapshots=candidates,
        top_k=5,
        min_similarity=0.3
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("Top Similar Investors")
    print("=" * 60)
    
    if not similar_investors:
        print("\n❌ No similar investors found above threshold")
    else:
        print(f"\nFound {len(similar_investors)} similar investors:\n")
        
        for i, result in enumerate(similar_investors, 1):
            print(f"{i}. Investor: {result.investor2_id}")
            print(f"   Total Similarity: {result.total_similarity:.3f}")
            print(f"   Breakdown:")
            print(f"     - Attitude:    {result.attitude_similarity:.3f} (weight: 0.35)")
            print(f"     - Constraint:  {result.constraint_similarity:.3f} (weight: 0.40)")
            print(f"     - Behavioral:  {result.behavioral_similarity:.3f} (weight: 0.25)")
            
            if result.failed_hard_filters:
                print(f"   ⚠️  Failed filters: {', '.join(result.failed_hard_filters)}")
            
            print()
    
    # Compute pairwise similarity for first 10 investors
    if len(snapshots) >= 10:
        print("\n" + "=" * 60)
        print("Pairwise Similarity Matrix (first 10 investors)")
        print("=" * 60)
        
        matrix = similarity_engine.compute_similarity_matrix(snapshots[:10])
        
        print("\nSimilarity matrix (values in [0, 1]):")
        print("Rows/Cols represent investor indices\n")
        
        # Format and print matrix
        print("     ", end="")
        for i in range(len(matrix)):
            print(f"  {i:2d}", end="")
        print()
        
        for i in range(len(matrix)):
            print(f"{i:2d}  ", end="")
            for j in range(len(matrix[i])):
                print(f" {matrix[i][j]:.2f}", end="")
            print()
        
        print("\nNote: Diagonal = 1.0 (self-similarity)")


if __name__ == "__main__":
    main()
