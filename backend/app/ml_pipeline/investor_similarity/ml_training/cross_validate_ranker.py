"""
Cross-Validation Generalization Test

Tests if the ranker generalizes or memorizes by running 5-fold CV.
"""

import sys
from pathlib import Path
import numpy as np
from sklearn.model_selection import KFold
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine
from backend.app.ml_pipeline.investor_similarity.ml_training.feature_encoder import InvestorFeatureEncoder
from backend.app.ml_pipeline.investor_similarity.ml_training.ranking_data_generator import RankingDataGenerator
from backend.app.ml_pipeline.investor_similarity.ml_training.ranking_metrics import ndcg_at_k


def cross_validate_ranker(n_splits=5, n_queries=1000, candidates_per_query=100):
    """
    5-fold cross-validation to test generalization
    
    Returns:
        dict with mean, std, and all fold scores
    """
    
    print("=" * 70)
    print("Cross-Validation Generalization Test")
    print("=" * 70)
    
    # Load dataset
    print("\n[1/4] Loading dataset...")
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots):,} investors")
    
    # Generate query groups
    print(f"\n[2/4] Generating {n_queries} query groups...")
    engine = SimilarityEngine()
    generator = RankingDataGenerator(snapshots, engine)
    
    queries, candidates, relevances, groups = generator.generate_query_groups(
        n_queries=n_queries,
        candidates_per_query=candidates_per_query,
        seed=42
    )
    
    # Encode features
    print("\n[3/4] Encoding features...")
    encoder = InvestorFeatureEncoder()
    
    X = []
    for query, candidate in zip(
        [q for q, g in zip(queries, groups) for _ in range(g)],
        candidates
    ):
        pair_features = encoder.encode_pair(query, candidate)
        X.append(pair_features)
    
    X = np.array(X)
    y = np.array(relevances)
    
    print(f"  ✓ Feature matrix: {X.shape}")
    
    # 5-fold cross-validation
    print(f"\n[4/4] Running {n_splits}-fold cross-validation...")
    
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    fold_ndcg_scores = []
    fold_details = []
    
    for fold_idx, (train_query_idx, val_query_idx) in enumerate(kfold.split(groups), 1):
        print(f"\n  Fold {fold_idx}/{n_splits}:")
        
        # Split by queries
        train_groups = groups[train_query_idx]
        val_groups = groups[val_query_idx]
        
        # Get corresponding pair indices
        train_size = sum(train_groups)
        val_start = train_size
        val_size = sum(val_groups)
        
        # Split data
        X_train = X[:train_size]
        X_val = X[val_start:val_start + val_size]
        y_train = y[:train_size]
        y_val = y[val_start:val_start + val_size]
        
        print(f"    Train: {len(train_groups)} queries, {X_train.shape[0]:,} pairs")
        print(f"    Val:   {len(val_groups)} queries, {X_val.shape[0]:,} pairs")
        
        # Train model
        ranker = xgb.XGBRanker(
            objective='rank:pairwise',
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        ranker.fit(X_train, y_train, group=train_groups, verbose=False)
        
        # Evaluate on validation set
        y_pred_val = ranker.predict(X_val)
        
        # Compute NDCG@10 per query
        query_ndcg_scores = []
        start_idx = 0
        
        for group_size in val_groups:
            end_idx = start_idx + group_size
            
            query_pred = y_pred_val[start_idx:end_idx]
            query_true = y_val[start_idx:end_idx]
            
            # Sort by prediction
            sorted_indices = np.argsort(query_pred)[::-1]
            ranked_relevances = query_true[sorted_indices].tolist()
            
            # NDCG@10
            ndcg = ndcg_at_k(ranked_relevances, 10)
            query_ndcg_scores.append(ndcg)
            
            start_idx = end_idx
        
        # Average NDCG for this fold
        fold_ndcg = np.mean(query_ndcg_scores)
        fold_ndcg_scores.append(fold_ndcg)
        
        print(f"    NDCG@10: {fold_ndcg:.4f}")
        
        fold_details.append({
            'fold': fold_idx,
            'ndcg@10': fold_ndcg,
            'n_queries': len(val_groups),
            'n_pairs': X_val.shape[0]
        })
    
    # Summary
    print("\n" + "=" * 70)
    print("Cross-Validation Results")
    print("=" * 70)
    
    print("\n  NDCG@10 by Fold:")
    for detail in fold_details:
        print(f"    Fold {detail['fold']}: {detail['ndcg@10']:.4f}")
    
    mean_ndcg = np.mean(fold_ndcg_scores)
    std_ndcg = np.std(fold_ndcg_scores)
    min_ndcg = np.min(fold_ndcg_scores)
    max_ndcg = np.max(fold_ndcg_scores)
    
    print(f"\n  Summary Statistics:")
    print(f"    Mean NDCG@10: {mean_ndcg:.4f}")
    print(f"    Std Dev:      {std_ndcg:.4f}")
    print(f"    Min:          {min_ndcg:.4f}")
    print(f"    Max:          {max_ndcg:.4f}")
    print(f"    Range:        {max_ndcg - min_ndcg:.4f}")
    
    # Interpretation
    print("\n" + "=" * 70)
    print("Generalization Assessment")
    print("=" * 70)
    
    if std_ndcg < 0.02:
        print("\n  ✅ EXCELLENT GENERALIZATION")
        print(f"     Variance: {std_ndcg:.4f} < 0.02")
        print("     Model is stable across folds")
        print("     → No additional noise needed!")
        recommendation = "deploy_as_is"
    elif std_ndcg < 0.05:
        print("\n  ✅ GOOD GENERALIZATION")
        print(f"     Variance: {std_ndcg:.4f} < 0.05")
        print("     Model generalizes well")
        print("     → Optional: Add 5% label noise for robustness")
        recommendation = "optional_noise"
    elif std_ndcg < 0.10:
        print("\n  ⚠️  MODERATE GENERALIZATION")
        print(f"     Variance: {std_ndcg:.4f} < 0.10")
        print("     Some overfitting detected")
        print("     → Recommended: Add 5-10% label noise")
        recommendation = "add_noise"
    else:
        print("\n  ❌ POOR GENERALIZATION")
        print(f"     Variance: {std_ndcg:.4f} >= 0.10")
        print("     Significant overfitting!")
        print("     → Required: Add noise + collect more real data")
        recommendation = "major_changes_needed"
    
    print("\n" + "=" * 70)
    
    return {
        'mean_ndcg': mean_ndcg,
        'std_ndcg': std_ndcg,
        'min_ndcg': min_ndcg,
        'max_ndcg': max_ndcg,
        'fold_scores': fold_ndcg_scores,
        'recommendation': recommendation
    }


if __name__ == "__main__":
    results = cross_validate_ranker(
        n_splits=5,
        n_queries=1000,
        candidates_per_query=100
    )
    
    print(f"\nRecommendation: {results['recommendation']}")
