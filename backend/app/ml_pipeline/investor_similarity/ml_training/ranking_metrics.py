"""
Ranking Metrics

Implements standard ranking evaluation metrics:
- NDCG@K (Normalized Discounted Cumulative Gain)
- MAP (Mean Average Precision)
- MRR (Mean Reciprocal Rank)
"""

import numpy as np
from typing import List


def dcg_at_k(relevances: List[float], k: int) -> float:
    """
    Discounted Cumulative Gain at K
    
    Args:
        relevances: List of relevance scores in ranked order
        k: Cutoff position
        
    Returns:
        DCG@K score
    """
    relevances = np.array(relevances[:k])
    if len(relevances) == 0:
        return 0.0
    
    # DCG = sum(rel_i / log2(i+1))
    discounts = np.log2(np.arange(2, len(relevances) + 2))
    return float(np.sum(relevances / discounts))


def ndcg_at_k(relevances: List[float], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain at K
    
    Args:
        relevances: List of relevance scores in ranked order
        k: Cutoff position
        
    Returns:
        NDCG@K score in [0, 1]
    """
    dcg = dcg_at_k(relevances, k)
    
    # Ideal DCG (sort by relevance descending)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def average_precision(relevances: List[float], threshold: float = 1.0) -> float:
    """
    Average Precision
    
    Args:
        relevances: List of relevance scores in ranked order
        threshold: Minimum relevance to be considered relevant
        
    Returns:
        Average precision score
    """
    relevances = np.array(relevances)
    
    # Binary relevance (1 if >= threshold)
    is_relevant = (relevances >= threshold).astype(float)
    
    if is_relevant.sum() == 0:
        return 0.0
    
    # Precision at each position
    precisions = []
    num_relevant = 0
    
    for i, rel in enumerate(is_relevant, 1):
        if rel:
            num_relevant += 1
            precision_at_i = num_relevant / i
            precisions.append(precision_at_i)
    
    return float(np.mean(precisions)) if precisions else 0.0


def mean_average_precision(all_relevances: List[List[float]], threshold: float = 1.0) -> float:
    """
    Mean Average Precision across all queries
    
    Args:
        all_relevances: List of relevance lists (one per query)
        threshold: Relevance threshold
        
    Returns:
        MAP score
    """
    aps = [average_precision(rels, threshold) for rels in all_relevances]
    return float(np.mean(aps)) if aps else 0.0


def reciprocal_rank(relevances: List[float], threshold: float = 1.0) -> float:
    """
    Reciprocal Rank - 1/position of first relevant item
    
    Args:
        relevances: List of relevance scores in ranked order
        threshold: Minimum relevance to be considered relevant
        
    Returns:
        Reciprocal rank
    """
    for i, rel in enumerate(relevances, 1):
        if rel >= threshold:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(all_relevances: List[List[float]], threshold: float = 1.0) -> float:
    """
    Mean Reciprocal Rank across all queries
    
    Args:
        all_relevances: List of relevance lists (one per query)
        threshold: Relevance threshold
        
    Returns:
        MRR score
    """
    rrs = [reciprocal_rank(rels, threshold) for rels in all_relevances]
    return float(np.mean(rrs)) if rrs else 0.0


def precision_at_k(relevances: List[float], k: int, threshold: float = 1.0) -> float:
    """
    Precision at K - fraction of top K results that are relevant
    
    Args:
        relevances: List of relevance scores in ranked order
        k: Cutoff position
        threshold: Minimum relevance to be considered relevant
        
    Returns:
        Precision@K score in [0, 1]
    """
    if k == 0 or len(relevances) == 0:
        return 0.0
    
    top_k = relevances[:k]
    num_relevant = sum(1 for rel in top_k if rel >= threshold)
    
    return float(num_relevant / k)


def kendall_tau(predicted_ranks: np.ndarray, true_ranks: np.ndarray) -> float:
    """
    Kendall's Tau correlation - measures ranking stability/agreement
    
    Tau = (concordant_pairs - discordant_pairs) / total_pairs
    
    Args:
        predicted_ranks: Predicted ranking (scores or positions)
        true_ranks: True ranking (ground truth scores)
        
    Returns:
        Kendall's Tau in [-1, 1]
        1.0 = perfect agreement
        0.0 = random
        -1.0 = perfect disagreement
    """
    from scipy.stats import kendalltau
    
    if len(predicted_ranks) != len(true_ranks):
        return 0.0
    
    if len(predicted_ranks) < 2:
        return 0.0
    
    tau, _ = kendalltau(predicted_ranks, true_ranks)
    
    # Handle NaN case
    if np.isnan(tau):
        return 0.0
    
    return float(tau)


def evaluate_ranking(
    predicted_scores: np.ndarray,
    true_relevances: np.ndarray,
    k_values: List[int] = [3, 5, 10, 20]
) -> dict:
    """
    Comprehensive ranking evaluation with extended metrics
    
    Args:
        predicted_scores: Predicted scores for candidates
        true_relevances: True relevance labels
        k_values: Cutoff values for NDCG@K and Precision@K
        
    Returns:
        Dictionary of metrics including NDCG@K, Precision@K, MAP, MRR, Kendall's Tau
    """
    # Sort by predicted scores (descending)
    sorted_indices = np.argsort(predicted_scores)[::-1]
    ranked_relevances = true_relevances[sorted_indices].tolist()
    
    metrics = {}
    
    # NDCG@K for each k
    for k in k_values:
        metrics[f'ndcg@{k}'] = ndcg_at_k(ranked_relevances, k)
    
    # Precision@K for each k
    for k in k_values:
        metrics[f'precision@{k}'] = precision_at_k(ranked_relevances, k, threshold=1.0)
    
    # Special: Precision@1 (most important item)
    metrics['precision@1'] = precision_at_k(ranked_relevances, 1, threshold=1.0)
    
    # MAP
    metrics['map'] = average_precision(ranked_relevances, threshold=1.0)
    
    # MRR
    metrics['mrr'] = reciprocal_rank(ranked_relevances, threshold=1.0)
    
    # Kendall's Tau (ranking stability)
    # Compare predicted ranking vs ideal ranking
    ideal_sorted = np.argsort(true_relevances)[::-1]
    metrics['kendall_tau'] = kendall_tau(sorted_indices, ideal_sorted)
    
    return metrics


if __name__ == "__main__":
    print("Ranking Metrics Test")
    print("=" * 60)
    
    # Example: 5 candidates with predicted scores and true relevances
    predicted = np.array([0.9, 0.3, 0.7, 0.5, 0.8])
    true_relevances = np.array([4, 0, 3, 1, 2])  # 0-4 scale
    
    print("Predicted scores:", predicted)
    print("True relevances:", true_relevances)
    print("Ranked order: [0.9, 0.8, 0.7, 0.5, 0.3]")
    print("True order:   [  4,   2,   3,   1,   0] (by relevance)")
    
    # Evaluate
    metrics = evaluate_ranking(predicted, true_relevances, k_values=[1, 3, 5])
    
    print("\nRanking Metrics:")
    print("\n  NDCG:")
    for k in [1, 3, 5]:
        print(f"    NDCG@{k}: {metrics[f'ndcg@{k}']:.4f}")
    
    print("\n  Precision:")
    for k in [1, 3, 5]:
        print(f"    Precision@{k}: {metrics[f'precision@{k}']:.4f}")
    
    print(f"\n  MAP: {metrics['map']:.4f}")
    print(f"  MRR: {metrics['mrr']:.4f}")
    print(f"  Kendall's Tau: {metrics['kendall_tau']:.4f}")
    
    print("\nInterpretation:")
    print("  NDCG@K: 1.0 = perfect, 0.5 = random, 0.0 = worst")
    print("  Precision@K: Fraction of top K that are relevant")
    print("  Precision@1: Is the top result relevant? (binary)")
    print("  MAP: Higher = better precision throughout ranking")
    print("  MRR: 1.0 = best match at top, 0.5 = at position 2")
    print("  Kendall's Tau: 1.0 = perfect rank agreement, 0.0 = random")

