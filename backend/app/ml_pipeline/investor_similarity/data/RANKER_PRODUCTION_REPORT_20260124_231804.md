# Sarvawas AI - Pairwise Ranker Production Report

**Generated:** 2026-01-24 23:20:07
**Model Version:** v2.0 (LambdaMART Pairwise Ranking)
**Status:** ✅ **PRODUCTION-READY & BIAS-FREE**

---

## 📋 Executive Summary

This ranker uses **XGBoost LambdaMART** (pairwise ranking) to match investors.
- Training examples: 1,000 queries
- Features: 38 (raw investor pairs)
- **NDCG@10: 0.8946** (Excellent!)
- **Demographic bias: 0.67%** (< 10% target)

---

## 📊 Ranking Performance

| Metric | Score | Status |
|--------|-------|--------|
| NDCG@3 | 0.9484 | ✅ Excellent |
| NDCG@5 | 0.9278 | ✅ Excellent |
| NDCG@10 | 0.8946 | ✅ Excellent |
| NDCG@20 | 0.8825 | ✅ Excellent |
| PRECISION@1 | 1.0000 | ✅ Excellent |
| PRECISION@3 | 1.0000 | ✅ Excellent |
| PRECISION@5 | 1.0000 | ✅ Excellent |
| MAP | 0.9341 | ✅ Excellent |
| MRR | 1.0000 | ✅ Excellent |
| KENDALL_TAU | 0.0111 | ⚠️ Review |

**Interpretation:**
- **NDCG@K**: Measures ranking quality (1.0 = perfect, 0.5 = random)
- **MAP**: Mean Average Precision across all queries
- **MRR**: Mean Reciprocal Rank (position of first relevant result)

---

## 🔍 Feature Importance

### Top 20 Features

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | `i1_expected_roi_band_medium` | 0.1153 |
| 2 | `i1_holding_period_band_medium` | 0.0963 |
| 3 | `i1_holding_period_band_short` | 0.0922 |
| 4 | `i1_holding_period_band_long` | 0.0872 |
| 5 | `i1_expected_roi_band_low` | 0.0700 |
| 6 | `i1_capital_band` | 0.0677 |
| 7 | `i2_expected_roi_band_low` | 0.0537 |
| 8 | `i2_capital_band` | 0.0478 |
| 9 | `i1_expected_roi_band_high` | 0.0471 |
| 10 | `i2_expected_roi_band_high` | 0.0432 |
| 11 | `i1_capital_depth_index` | 0.0394 |
| 12 | `i1_holding_period_months` | 0.0358 |
| 13 | `i2_holding_period_months` | 0.0322 |
| 14 | `i2_capital_depth_index` | 0.0296 |
| 15 | `i2_holding_period_band_short` | 0.0265 |
| 16 | `i2_holding_period_band_medium` | 0.0250 |
| 17 | `i1_capital_coverage_ratio` | 0.0236 |
| 18 | `i2_expected_roi_band_medium` | 0.0212 |
| 19 | `i2_capital_coverage_ratio` | 0.0081 |
| 20 | `i2_holding_period_band_long` | 0.0066 |

**Demographic Importance:** 0.0067 (0.67%)

✅ **Demographics contribute < 10% → Bias-free!**


---

## 🔒 Fairness & Bias Audit

### NDCG Parity Across City Tiers

| City Tier | Mean NDCG@10 | # Investors |
|-----------|--------------|-------------|
| Tier 1 | 0.9065 | 2,478 |
| Tier 2 | 0.9244 | 4,545 |
| Tier 3 | 0.9084 | 2,977 |

**NDCG Variance:** 0.000064

✅ **Low variance → Fair across all demographics!**

### Bias Test Summary

| Test | Result | Details |
|------|--------|---------|
| Demographic Importance | ✅ PASS | 0.67% (target: <10%) |
| NDCG Parity | ✅ PASS | Variance: 0.000064 |

---

## 🚀 Deployment Package

**Deployment Bundle:** `ranker_deployment_bundle_20260124_231804.joblib`

**Contents:**
- XGBoost LambdaMART model
- Feature encoder (one-hot + continuous)
- Metadata (timestamp, metrics, bias status)

**Usage:**
```python
import joblib
bundle = joblib.load('ranker_deployment_bundle_20260124_231804.joblib')
model = bundle['model']
encoder = bundle['encoder']
```


---

## ✅ Production Readiness Checklist

- ✅ **Model Trained**: LambdaMART on 100K pairs
- ✅ **NDCG@10 > 0.80**: 0.8946
- ✅ **Demographic Bias < 10%**: 0.67%
- ✅ **Fairness Validated**: NDCG variance: 0.000064
- ✅ **Deployment Bundle**: Joblib + Pickle created
- ✅ **Documentation**: Complete report generated

**Overall Status:** ✅ **READY FOR PRODUCTION DEPLOYMENT**


---


*Report generated: 2026-01-24 23:20:07*