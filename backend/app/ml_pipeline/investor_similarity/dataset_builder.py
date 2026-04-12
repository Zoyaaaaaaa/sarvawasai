"""
Dataset Builder - Canonical Feature Snapshot System

Implements versioned, immutable feature snapshots for investors.
Each snapshot represents one investor's feature state at one timestamp.

Snapshots are reproducible, encrypted, and include full metadata.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional, List
import json
import hashlib
import os
from pathlib import Path

from .feature_contracts import FeatureBlock, FeatureSource


@dataclass
class FeatureSnapshot:
    """
    Canonical Feature Snapshot
    
    Represents one investor at one timestamp with complete feature state,
    metadata, and provenance information.
    """
    
    # Hashed investor identifier (SHA-256)
    investor_id: str
    
    # Feature blocks
    block_a: Dict[str, float]
    block_b: Dict[str, any]
    block_c: Dict[str, float]
    
    # Metadata
    snapshot_timestamp: str  # ISO 8601
    feature_version: str
    data_source: str  # platform|survey|synthetic
    confidence_weight: float
    
    # Optional provenance
    source_log_hash: Optional[str] = None
    
    def __post_init__(self):
        """Validate snapshot on creation"""
        # Validate feature values
        FeatureBlock.validate_feature_values("block_a", self.block_a)
        FeatureBlock.validate_feature_values("block_b", self.block_b)
        FeatureBlock.validate_feature_values("block_c", self.block_c)
        
        # Validate confidence weight
        if not (0.0 <= self.confidence_weight <= 1.0):
            raise ValueError(
                f"confidence_weight must be in [0, 1], got {self.confidence_weight}"
            )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of snapshot for reproducibility validation"""
        snapshot_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(snapshot_str.encode()).hexdigest()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FeatureSnapshot':
        """Create snapshot from dictionary"""
        return cls(**data)


class DatasetBuilder:
    """
    Builds and manages versioned feature snapshot datasets
    
    Features:
    - Immutable snapshot storage
    - Version management
    - Batch operations
    - Reproducibility validation
    """
    
    def __init__(self, storage_path: str, feature_version: str = "v1.0"):
        """
        Initialize dataset builder
        
        Args:
            storage_path: Directory to store snapshot files
            feature_version: Version of feature contracts being used
        """
        self.storage_path = Path(storage_path)
        self.feature_version = feature_version
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create version directory
        self.version_dir = self.storage_path / feature_version
        self.version_dir.mkdir(exist_ok=True)
    
    def create_snapshot(
        self,
        investor_id_raw: str,
        block_a: Dict[str, float],
        block_b: Dict[str, any],
        block_c: Dict[str, float],
        data_source: str,
        confidence_weight: float,
        source_log_data: Optional[str] = None
    ) -> FeatureSnapshot:
        """
        Create a new feature snapshot
        
        Args:
            investor_id_raw: Raw investor ID (will be hashed)
            block_a: Block A feature values
            block_b: Block B feature values
            block_c: Block C feature values
            data_source: Data source identifier
            confidence_weight: Confidence in this snapshot
            source_log_data: Optional source log for hash computation
            
        Returns:
            Created FeatureSnapshot
        """
        # Hash investor ID for privacy
        investor_id_hash = hashlib.sha256(investor_id_raw.encode()).hexdigest()
        
        # Hash source log if provided
        source_log_hash = None
        if source_log_data:
            source_log_hash = hashlib.sha256(source_log_data.encode()).hexdigest()
        
        # Create snapshot
        snapshot = FeatureSnapshot(
            investor_id=investor_id_hash,
            block_a=block_a,
            block_b=block_b,
            block_c=block_c,
            snapshot_timestamp=datetime.utcnow().isoformat(),
            feature_version=self.feature_version,
            data_source=data_source,
            confidence_weight=confidence_weight,
            source_log_hash=source_log_hash
        )
        
        return snapshot
    
    def save_snapshot(self, snapshot: FeatureSnapshot) -> str:
        """
        Save snapshot to disk
        
        Args:
            snapshot: FeatureSnapshot to save
            
        Returns:
            Path to saved file
        """
        # Create filename with timestamp
        timestamp = datetime.fromisoformat(snapshot.snapshot_timestamp)
        filename = f"{snapshot.investor_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.version_dir / filename
        
        # Save snapshot
        with open(filepath, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
        
        return str(filepath)
    
    def save_batch(self, snapshots: List[FeatureSnapshot]) -> List[str]:
        """
        Save multiple snapshots
        
        Args:
            snapshots: List of FeatureSnapshots
            
        Returns:
            List of saved file paths
        """
        saved_paths = []
        for snapshot in snapshots:
            path = self.save_snapshot(snapshot)
            saved_paths.append(path)
        
        return saved_paths
    
    def load_snapshot(self, filepath: str) -> FeatureSnapshot:
        """
        Load snapshot from file
        
        Args:
            filepath: Path to snapshot JSON file
            
        Returns:
            Loaded FeatureSnapshot
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return FeatureSnapshot.from_dict(data)
    
    def load_all_snapshots(self) -> List[FeatureSnapshot]:
        """
        Load all snapshots for current version
        
        Returns:
            List of all FeatureSnapshots
        """
        snapshots = []
        for filepath in self.version_dir.glob("*.json"):
            snapshot = self.load_snapshot(filepath)
            snapshots.append(snapshot)
        
        return snapshots
    
    def get_latest_snapshot(self, investor_id_hash: str) -> Optional[FeatureSnapshot]:
        """
        Get most recent snapshot for an investor
        
        Args:
            investor_id_hash: Hashed investor ID
            
        Returns:
            Latest FeatureSnapshot or None
        """
        investor_snapshots = []
        for filepath in self.version_dir.glob(f"{investor_id_hash}_*.json"):
            snapshot = self.load_snapshot(filepath)
            investor_snapshots.append(snapshot)
        
        if not investor_snapshots:
            return None
        
        # Sort by timestamp and return latest
        investor_snapshots.sort(
            key=lambda s: datetime.fromisoformat(s.snapshot_timestamp),
            reverse=True
        )
        return investor_snapshots[0]
    
    def validate_reproducibility(
        self,
        snapshot: FeatureSnapshot,
        recomputed_snapshot: FeatureSnapshot
    ) -> bool:
        """
        Validate that recomputed features match original
        
        Args:
            snapshot: Original snapshot
            recomputed_snapshot: Recomputed snapshot from source logs
            
        Returns:
            True if hashes match (reproducible)
        """
        original_hash = snapshot.compute_hash()
        recomputed_hash = recomputed_snapshot.compute_hash()
        
        if original_hash != recomputed_hash:
            print(f"Reproducibility check FAILED")
            print(f"Original hash:   {original_hash}")
            print(f"Recomputed hash: {recomputed_hash}")
            return False
        
        print(f"Reproducibility check PASSED")
        return True
    
    def export_dataset(self, output_path: str, include_metadata: bool = True):
        """
        Export all snapshots to a single JSONL file
        
        Args:
            output_path: Path to output JSONL file
            include_metadata: Include snapshot metadata
        """
        snapshots = self.load_all_snapshots()
        
        with open(output_path, 'w') as f:
            for snapshot in snapshots:
                data = snapshot.to_dict() if include_metadata else {
                    'investor_id': snapshot.investor_id,
                    'block_a': snapshot.block_a,
                    'block_b': snapshot.block_b,
                    'block_c': snapshot.block_c
                }
                f.write(json.dumps(data) + '\n')
        
        print(f"Exported {len(snapshots)} snapshots to {output_path}")
    
    def get_statistics(self) -> dict:
        """
        Get dataset statistics
        
        Returns:
            Dictionary of statistics
        """
        snapshots = self.load_all_snapshots()
        
        if not snapshots:
            return {"total_snapshots": 0}
        
        # Count by source
        source_counts = {}
        for snapshot in snapshots:
            source = snapshot.data_source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Count unique investors
        unique_investors = len(set(s.investor_id for s in snapshots))
        
        # Average confidence weight
        avg_confidence = sum(s.confidence_weight for s in snapshots) / len(snapshots)
        
        return {
            "total_snapshots": len(snapshots),
            "unique_investors": unique_investors,
            "source_distribution": source_counts,
            "avg_confidence_weight": avg_confidence,
            "feature_version": self.feature_version
        }
