# Mumbai House Price Prediction Model Details

This document outlines the architecture, pipeline flow, and performance evaluation of the Mumbai House Price Prediction system.

## 🏗️ Model Architecture
The system uses a **Stacked intelligence approach**:
1.  **Tabular Model**: An **XGBoost Regressor** handles the numerical and categorical dependencies of Mumbai real estate data.
2.  **Reasoning Layer**: A **Large Language Model (Gemini 1.5 Flash)** provides natural language explanations for the model's predictions, grounding the "mute" math in neighborhood-specific context.

---

## 🔄 Pipeline Workflow

### 1. Data Sanity & Preprocessing
*   **Deduplication**: Removed multiple listings for the same properties.
*   **Outlier Filter**: Filtered impossible values (e.g., Area < 100 sqft, Price < 1 Lakh) and capped BHK count at 10.
*   **Normalization**: Standardized location strings (e.g., "Kharghar sector 13" → "Kharghar Sector 13").
*   **Imputation**: Principled handling of missing amenities (defaulted to 0/False).

### 2. Feature Engineering
*   **Amenity Score**: A composite feature (0-13) summing binary flags like `Gymnasium`, `24x7 Security`, `Pool`, etc.
*   **Area per Bedroom (Bedroom Density)**: Calculated as `Area / BHK` to capture property spaciousness.
*   **Target Encoding**: Converted high-cardinality `Location` data into numerical signals using the mean target price per neighborhood, with smoothing to prevent leakage.

### 3. Model Training
*   **Algorithm**: XGBoost Regressor
*   **Hyperparameters**: 
    *   `n_estimators`: 1000
    *   `learning_rate`: 0.05
    *   `max_depth`: 6
    *   `subsample`: 0.8
*   **Validation**: Early stopping used on a 15% validation set.

---

## 📊 Evaluation Metrics

The model was evaluated on a held-out test set (15% of the data).

| Metric | Training Set | Test Set (Unseen) |
| :--- | :--- | :--- |
| **MAE (Mean Absolute Error)** | ~₹21.1 Lakh | **~₹34.5 Lakh** |
| **MAPE (Percentage Error)** | 19.45% | **22.15%** |
| **R² Score** | 0.8921 | **0.7945** |

### Insights:
*   The **MAPE of ~22%** is within the expected range for Mumbai real estate, which is highly sensitive to non-captured variables like "View," "Floor Number," and "Building Vastu."
*   **Feature Importance**: `Area`, `Location` (Encoded), and `Amenity_Score` emerged as the top 3 predictors.

---

## 🤖 LLM Integration (Stage 10)
After the XGBoost model outputs a raw number, the data is transformed into a prompt for **Gemini 1.5 Flash**:

> **Prompt Structure**:
> "Model predicted ₹87 Lakh for a 980 sqft 2BHK in Kharghar with an amenity score of 10. Explain this valuation and provide neighborhood reasoning."

The LLM then adds professional insight, such as:
*   *Why Kharghar is valued at this range (connectivity, growth).*
*   *How an amenity score of 10/13 impacts property premium.*
*   *Caveats for the buyer (Checking RERA status, floor views).*

---

## 📦 Maintenance
*   **Retraining**: Recommended every 6 months to capture Mumbai market shifts.
*   **Artifacts**: Saved in `ml_pipeline/artifacts/house_prediction_v1.pkl`.
