"""
Example: Run Bias Audit

Demonstrates how to audit a dataset for demographic bias.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from investor_similarity.bias_monitor import BiasMonitor, AutomaticAuditScheduler


def generate_mock_demographics(num_investors: int):
    """Generate mock demographic data for testing"""
    np.random.seed(42)
    
    demographics = {
        "age": np.random.randint(25, 65, size=num_investors),
        "gender": np.random.randint(0, 2, size=num_investors),  # 0=F, 1=M
        "city_tier": np.random.randint(1, 4, size=num_investors),  # 1, 2, 3
        "occupation_code": np.random.randint(0, 5, size=num_investors)
    }
    
    return demographics


def main():
    print("=" * 60)
    print("Investor Similarity System - Bias Audit")
    print("=" * 60)
    
    # Load dataset
    print("\n[1/3] Loading dataset...")
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",  # Updated to match scale_to_10k output
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots)} snapshots")
    
    # Generate mock demographics (in production, this would be real data)
    print("\n[2/3] Preparing demographic data...")
    demographics = generate_mock_demographics(len(snapshots))
    print(f"  ✓ Generated mock demographics for {len(snapshots)} investors")
    
    # Run bias audit
    print("\n[3/3] Running bias audit...")
    bias_monitor = BiasMonitor(correlation_threshold=0.1)
    scheduler = AutomaticAuditScheduler(bias_monitor)
    
    report = scheduler.run_audit(
        snapshots=snapshots,
        demographics=demographics,
        feature_version="v1.0"
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("Bias Audit Report")
    print("=" * 60)
    
    print(f"Audit timestamp: {report.audit_timestamp}")
    print(f"Feature version: {report.feature_version}")
    print(f"Total samples: {report.total_samples}")
    print(f"Status: {'✅ PASSED' if report.passed else '❌ FAILED'}")
    
    if report.violations:
        print(f"\n⚠️  Violations detected: {len(report.violations)}")
        print("\nDetails:")
        for v in report.violations[:5]:  # Show first 5
            print(f"  - {v['feature']} × {v['demographic']}: "
                  f"correlation = {v['correlation']:.3f}")
        
        print("\n📋 Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")
    else:
        print("\n✅ No bias violations detected!")
        print("All features are below the correlation threshold.")
    
    # Save report
    report.save("./data/bias_audit_report.json")
    print(f"\n📄 Report saved to: ./data/bias_audit_report.json")
    
    # Additional tests
    print("\n" + "=" * 60)
    print("Additional Bias Tests")
    print("=" * 60)
    
    # Capital dominance test
    capital_test = bias_monitor.test_capital_dominance(snapshots)
    print(f"\nCapital diversity: {'✅ DIVERSE' if capital_test['diverse'] else '❌ DOMINATED'}")
    print(f"High-capital ratio: {capital_test['high_capital_ratio']:.2%}")
    print(f"Distribution: {capital_test['capital_distribution']}")


if __name__ == "__main__":
    main()
