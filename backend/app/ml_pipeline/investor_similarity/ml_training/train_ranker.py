"""
Train Pairwise Ranking Model

LambdaMART training using XGBoost rank:pairwise objective.
"""

import sys
from pathlib import Path
import numpy as np
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine
from backend.app.ml_pipeline.investor_similarity.ml_training.feature_encoder import InvestorFeatureEncoder
from backend.app.ml_pipeline.investor_similarity.ml_training.ranking_data_generator import RankingDataGenerator
from backend.app.ml_pipeline.investor_similarity.ml_training.ranking_metrics import evaluate_ranking, ndcg_at_k


def train_ranking_model(
    n_queries: int = 1000,
    candidates_per_query: int = 100,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Complete pairwise ranking training pipeline
    
    Args:
        n_queries: Number of query investors
        candidates_per_query: Candidates per query
        test_size: Validation fraction
        random_state: Random seed
    """
    
    print("=" * 70)
    print("XGBoost Pairwise Ranking Training")
    print("=" * 70)
    
    # Step 1: Load dataset
    print("\n[1/7] Loading dataset...")
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots):,} investors")
    
    # Step 2: Generate query groups
    print(f"\n[2/7] Generating query groups...")
    engine = SimilarityEngine()
    generator = RankingDataGenerator(snapshots, engine)
    
    queries, candidates, relevances, groups = generator.generate_query_groups(
        n_queries=n_queries,
        candidates_per_query=candidates_per_query,
        seed=random_state
    )
    
    # Step 3: Encode features
    print("\n[3/7] Encoding features...")
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
    print(f"  ✓ Relevance labels: {y.shape}")
    
    # Step 4: Train/test split (by query groups)
    print(f"\n[4/7] Splitting data by queries...")
    
    # Split query indices
    n_train_queries = int(len(groups) * (1 - test_size))
    train_groups = groups[:n_train_queries]
    test_groups = groups[n_train_queries:]
    
    # Split features accordingly
    train_size = sum(train_groups)
    X_train = X[:train_size]
    X_test = X[train_size:]
    y_train = y[:train_size]
    y_test = y[train_size:]
    
    print(f"  ✓ Training: {len(train_groups)} queries, {X_train.shape[0]:,} pairs")
    print(f"  ✓ Testing: {len(test_groups)} queries, {X_test.shape[0]:,} pairs")
    
    # Step 5: Train XGBoost Ranker
    print("\n[5/7] Training LambdaMART ranker...")
    
    ranker_params = {
        'objective': 'rank:pairwise',
        'eval_metric': 'ndcg',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'tree_method': 'hist',
        'random_state': random_state,
        'n_jobs': -1
    }
    
    model = xgb.XGBRanker(**ranker_params)
    
    model.fit(
        X_train, y_train,
        group=train_groups,
        eval_set=[(X_test, y_test)],
        eval_group=[test_groups],
        verbose=10
    )
    
    print("  ✓ Training complete!")
    
    # Step 6: Evaluate with ranking metrics
    print("\n[6/7] Evaluating ranker...")
    
    # Predict on test set
    y_pred_test = model.predict(X_test)
    
    # Evaluate per query with extended metrics
    test_metrics = {
        'ndcg@3': [], 'ndcg@5': [], 'ndcg@10': [], 'ndcg@20': [],
        'precision@1': [], 'precision@3': [], 'precision@5': [],
        'map': [], 'mrr': [], 'kendall_tau': []
    }
    
    start_idx = 0
    for group_size in test_groups:
        end_idx = start_idx + group_size
        
        query_pred = y_pred_test[start_idx:end_idx]
        query_true = y_test[start_idx:end_idx]
        
        metrics = evaluate_ranking(query_pred, query_true, k_values=[3, 5, 10, 20])
        
        for key, value in metrics.items():
            if key in test_metrics:
                test_metrics[key].append(value)
        
        start_idx = end_idx
    
    # Average metrics
    print("\n  Test Set Ranking Performance:")
    
    # NDCG
    print("\n  NDCG (Ranking Quality):")
    for k in [3, 5, 10, 20]:
        avg = np.mean(test_metrics[f'ndcg@{k}'])
        print(f"    NDCG@{k}: {avg:.4f}")
    
    # Precision
    print("\n  Precision (Top-K Accuracy):")
    for k in [1, 3, 5]:
        avg = np.mean(test_metrics[f'precision@{k}'])
        print(f"    Precision@{k}: {avg:.4f}")
    
    # Other metrics
    print("\n  Additional Metrics:")
    print(f"    MAP (Mean Avg Precision): {np.mean(test_metrics['map']):.4f}")
    print(f"    MRR (Mean Reciprocal Rank): {np.mean(test_metrics['mrr']):.4f}")
    print(f"    Kendall's Tau (Rank Stability): {np.mean(test_metrics['kendall_tau']):.4f}")
    
    # Feature importance
    print("\n  Top 10 Most Important Features:")
    feature_names_full = (
        [f"i1_{n}" for n in encoder.feature_names] +
        [f"i2_{n}" for n in encoder.feature_names] +
        [f"diff_{n}" for n in encoder.feature_names] +
        [f"prod_{n}" for n in encoder.feature_names]
    )
    
    importance = model.feature_importances_
    top_indices = np.argsort(importance)[-10:][::-1]
    
    for i, idx in enumerate(top_indices, 1):
        print(f"    {i}. {feature_names_full[idx]}: {importance[idx]:.4f}")
    
    # Step 7: Save model
    print("\n[7/7] Saving ranker...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    model_path = f"./data/xgboost_ranker_model_{timestamp}.json"
    encoder_path = f"./data/ranker_encoder_{timestamp}.pkl"
    
    model.save_model(model_path)
    
    with open(encoder_path, 'wb') as f:
        pickle.dump(encoder, f)
    
    print(f"  ✓ Ranker saved: {model_path}")
    print(f"  ✓ Encoder saved: {encoder_path}")
    
    # Save metrics
    avg_metrics = {k: float(np.mean(v)) for k, v in test_metrics.items()}
    
    metrics = {
        'timestamp': timestamp,
        'n_queries': n_queries,
        'candidates_per_query': candidates_per_query,
        'n_features': X.shape[1],
        'test_metrics': avg_metrics,
        'model_params': ranker_params
    }
    
    metrics_path = f"./data/ranking_metrics_{timestamp}.pkl"
    with open(metrics_path, 'wb') as f:
        pickle.dump(metrics, f)
    
    print(f"  ✓ Metrics saved: {metrics_path}")
    
    print("\n" + "=" * 70)
    print("✅ Ranking Training Complete!")
    print("=" * 70)
    
    print(f"\nRanking Performance Summary:")
    print(f"  NDCG@10: {avg_metrics['ndcg@10']:.4f}")
    print(f"  MAP:     {avg_metrics['map']:.4f}")
    print(f"  MRR:     {avg_metrics['mrr']:.4f}")
    
    if avg_metrics['ndcg@10'] >= 0.80:
        print("\n  🎉 Excellent! NDCG@10 >= 0.80")
    elif avg_metrics['ndcg@10'] >= 0.70:
        print("\n  ✅ Good! NDCG@10 >= 0.70")
    else:
        print("\n  ⚠️  Consider more training data or hyperparameter tuning")
    
    return model, encoder, metrics


if __name__ == "__main__":
    # Train pairwise ranker
    model, encoder, metrics = train_ranking_model(
        n_queries=1000,
        candidates_per_query=100,
        test_size=0.2,
        random_state=42
    )
