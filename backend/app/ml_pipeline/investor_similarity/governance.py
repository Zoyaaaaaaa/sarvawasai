"""
Feature Governance Module

Enforces feature contract compliance:
- Source declaration validation
- Confidence weight tracking
- Refresh cadence monitoring
- Bias test registration
- Feature version management
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .feature_contracts import FeatureBlock, FeatureSource


@dataclass
class FeatureMetadata:
    """Metadata for a feature instance"""
    feature_name: str
    feature_block: str  # 'A', 'B', or 'C'
    source: str
    last_updated: str  # ISO 8601
    confidence_weight: float
    refresh_cadence: str
    next_refresh_due: str  # ISO 8601
    bias_tests_passed: bool
    version: str
    
    def to_dict(self) -> dict:
        return {
            "feature_name": self.feature_name,
            "feature_block": self.feature_block,
            "source": self.source,
            "last_updated": self.last_updated,
            "confidence_weight": self.confidence_weight,
            "refresh_cadence": self.refresh_cadence,
            "next_refresh_due": self.next_refresh_due,
            "bias_tests_passed": self.bias_tests_passed,
            "version": self.version
        }


class GovernanceValidator:
    """
    Validates feature compliance with governance rules
    
    Rules:
    1. All features must declare source
    2. Confidence weights must be in [0, 1]
    3. Refresh cadence must be specified
    4. Bias tests must be registered
    """
    
    def __init__(self, feature_version: str = "v1.0"):
        self.feature_version = feature_version
        self.metadata_store = {}
    
    def validate_feature_snapshot(self, snapshot) -> Dict:
        """
        Validate a complete feature snapshot
        
        Args:
            snapshot: FeatureSnapshot object
            
        Returns:
            Validation report
        """
        report = {
            "snapshot_id": snapshot.investor_id,
            "timestamp": snapshot.snapshot_timestamp,
            "passed": True,
            "issues": []
        }
        
        # Validate source declaration
        if snapshot.data_source not in ["platform", "survey", "synthetic", "behavioral"]:
            report["passed"] = False
            report["issues"].append(f"Invalid data_source: {snapshot.data_source}")
        
        # Validate confidence weight
        if not (0.0 <= snapshot.confidence_weight <= 1.0):
            report["passed"] = False
            report["issues"].append(
                f"confidence_weight out of range: {snapshot.confidence_weight}"
            )
        
        # Validate feature version
        if snapshot.feature_version != self.feature_version:
            report["issues"].append(
                f"Feature version mismatch: {snapshot.feature_version} != {self.feature_version}"
            )
        
        # Validate reproducibility hash
        if snapshot.source_log_hash is None and snapshot.data_source != "synthetic":
            report["issues"].append("Missing source_log_hash for reproducibility")
        
        return report
    
    def register_feature_update(
        self,
        feature_name: str,
        feature_block: str,
        source: str,
        confidence_weight: float,
        refresh_cadence: str
    ) -> FeatureMetadata:
        """
        Register a feature update with metadata
        
        Args:
            feature_name: Name of feature
            feature_block: 'A', 'B', or 'C'
            source: Data source
            confidence_weight: Confidence in feature
            refresh_cadence: How often to refresh
            
        Returns:
            FeatureMetadata object
        """
        now = datetime.utcnow()
        
        # Compute next refresh due
        next_refresh = self._compute_next_refresh(now, refresh_cadence)
        
        metadata = FeatureMetadata(
            feature_name=feature_name,
            feature_block=feature_block,
            source=source,
            last_updated=now.isoformat(),
            confidence_weight=confidence_weight,
            refresh_cadence=refresh_cadence,
            next_refresh_due=next_refresh.isoformat(),
            bias_tests_passed=False,  # Must run bias tests
            version=self.feature_version
        )
        
        # Store metadata
        key = f"{feature_block}.{feature_name}"
        self.metadata_store[key] = metadata
        
        return metadata
    
    def _compute_next_refresh(
        self,
        last_updated: datetime,
        cadence: str
    ) -> datetime:
        """Compute next refresh timestamp"""
        if cadence == "on_survey_update":
            return last_updated + timedelta(days=90)  # Assume quarterly surveys
        elif cadence == "on_profile_update":
            return last_updated + timedelta(days=30)  # Check monthly
        elif cadence == "weekly":
            return last_updated + timedelta(days=7)
        elif cadence == "monthly":
            return last_updated + timedelta(days=30)
        else:
            return last_updated + timedelta(days=365)  # Annual default
    
    def check_refresh_due(self, feature_key: str) -> bool:
        """Check if feature refresh is due"""
        if feature_key not in self.metadata_store:
            return True  # Never refreshed, due now
        
        metadata = self.metadata_store[feature_key]
        next_refresh = datetime.fromisoformat(metadata.next_refresh_due)
        
        return datetime.utcnow() >= next_refresh
    
    def mark_bias_tests_passed(self, feature_key: str):
        """Mark bias tests as passed for feature"""
        if feature_key in self.metadata_store:
            self.metadata_store[feature_key].bias_tests_passed = True
    
    def get_features_needing_refresh(self) -> List[FeatureMetadata]:
        """Get list of features that need refresh"""
        needing_refresh = []
        
        for key, metadata in self.metadata_store.items():
            if self.check_refresh_due(key):
                needing_refresh.append(metadata)
        
        return needing_refresh
    
    def export_metadata(self, filepath: str):
        """Export all feature metadata to file"""
        metadata_dict = {
            key: metadata.to_dict()
            for key, metadata in self.metadata_store.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
    
    def get_governance_report(self) -> Dict:
        """Generate governance compliance report"""
        total_features = len(self.metadata_store)
        
        # Count by block
        block_counts = {"A": 0, "B": 0, "C": 0}
        for metadata in self.metadata_store.values():
            block_counts[metadata.feature_block] += 1
        
        # Count by source
        source_counts = {}
        for metadata in self.metadata_store.values():
            source = metadata.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Count bias tests passed
        bias_tests_passed = sum(
            1 for m in self.metadata_store.values() if m.bias_tests_passed
        )
        
        # Count features needing refresh
        refresh_needed = len(self.get_features_needing_refresh())
        
        report = {
            "feature_version": self.feature_version,
            "total_features": total_features,
            "features_by_block": block_counts,
            "features_by_source": source_counts,
            "bias_tests_passed": bias_tests_passed,
            "bias_tests_pending": total_features - bias_tests_passed,
            "features_needing_refresh": refresh_needed
        }
        
        return report


class VersionManager:
    """
    Manages feature contract versions
    
    Ensures backward compatibility and migration paths.
    """
    
    def __init__(self):
        self.versions = {
            "v1.0": {
                "release_date": "2026-01-24",
                "blocks": ["A", "B", "C"],
                "total_features": 10,
                "changes": "Initial release"
            }
        }
        self.current_version = "v1.0"
    
    def add_version(
        self,
        version: str,
        release_date: str,
        changes: str
    ):
        """Register a new feature version"""
        self.versions[version] = {
            "release_date": release_date,
            "changes": changes
        }
        self.current_version = version
    
    def get_version_info(self, version: str) -> Dict:
        """Get information about a version"""
        return self.versions.get(version, {})
    
    def list_versions(self) -> List[str]:
        """List all versions"""
        return sorted(self.versions.keys())
