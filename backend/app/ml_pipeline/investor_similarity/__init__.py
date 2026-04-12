"""
Investor Similarity System

A production-grade, scalable, non-biased investor similarity system
for real estate co-investment recommendations.

This module provides:
- Feature contracts (immutable data specifications)
- Dataset construction with versioning
- Synthetic data generation (cold-start only)
- Bias monitoring and auditing
- Pre-ML similarity computation

Models are explicitly replaceable. Features and governance are permanent.
"""

__version__ = "1.0.0"
__author__ = "ML / Data Platform Team"

from .feature_contracts import FeatureBlock, BlockA, BlockB, BlockC
from .dataset_builder import FeatureSnapshot, DatasetBuilder
from .similarity_engine import SimilarityEngine

__all__ = [
    "FeatureBlock",
    "BlockA",
    "BlockB",
    "BlockC",
    "FeatureSnapshot",
    "DatasetBuilder",
    "SimilarityEngine",
]
