"""Step-Up: Smart Matchmaking"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

print("Loading training dataset...")
ROOT_DIR = Path(__file__).resolve().parents[2]
matches_df = pd.read_csv(ROOT_DIR / 'data' / 'raw' / 'legacy' / 'buyer_investor_matches.csv')
print("Matches loaded:", matches_df.shape)

matches_df.dropna(inplace=True)

le_buyer = LabelEncoder()
le_investor = LabelEncoder()
matches_df['buyerRisk'] = le_buyer.fit_transform(matches_df['buyerRisk'])
matches_df['investorRisk'] = le_investor.fit_transform(matches_df['investorRisk'])

X = matches_df[['buyerBudgetMax', 'buyerRisk', 'locationMatch', 'investorMaxDeal', 'investorRisk']]
y = matches_df['matchScore']

scaler = StandardScaler()
X[['buyerBudgetMax', 'investorMaxDeal']] = scaler.fit_transform(X[['buyerBudgetMax', 'investorMaxDeal']])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

best_knn = KNeighborsRegressor(n_neighbors=3, weights='distance', metric='euclidean')
best_knn.fit(X_train, y_train)

y_pred = best_knn.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Model trained successfully | Test MSE: {mse:.6f}")

investors_df = pd.read_csv(ROOT_DIR / 'backend' / 'data' / 'raw' / 'investor_profiles_mumbai.csv')
print("Investors loaded:", investors_df.shape)

def recommend_investors(buyer_input, investors_df):
    """
    Recommend top 3 investors for a given buyer profile.
    buyer_input = {
        'buyerBudgetMax': float,
        'buyerRisk': int (0=Low, 1=Medium, 2=High),
        'location': str (e.g., "Andheri West")
    }
    """
    recommendations = []

    for _, inv in investors_df.iterrows():

        preferred = str(inv['preferredLocations'])
        location_match = 1 if buyer_input['location'] in preferred else 0

        features = pd.DataFrame([{
            'buyerBudgetMax': buyer_input['buyerBudgetMax'],
            'buyerRisk': buyer_input['buyerRisk'],
            'locationMatch': location_match,
            'investorMaxDeal': inv['maxInvestmentPerDeal'],
            'investorRisk': (
                0 if inv['riskAppetite'] == 'Low' else
                1 if inv['riskAppetite'] == 'Medium' else
                2
            )
        }])

        features[['buyerBudgetMax', 'investorMaxDeal']] = scaler.transform(
            features[['buyerBudgetMax', 'investorMaxDeal']]
        )

        score = best_knn.predict(features)[0]

        recommendations.append({
            "investorId": inv['userId'],
            "profession": inv['profession'],
            "riskAppetite": inv['riskAppetite'],
            "budget": inv['maxInvestmentPerDeal'],
            "locationMatch": location_match,
            "score": round(float(score), 3)
        })

    top3 = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:3]
    return top3

buyer_input = {
    "buyerBudgetMax": 25000000,
    "buyerRisk": 2,
    "location": "Bandra West"
}
top_matches = recommend_investors(buyer_input, investors_df)

print("\nTop Investor Matches for Buyer:")
for i, match in enumerate(top_matches, start=1):
    label = ["Best Match", "Better Match", "Good Match"][i-1]
    print(f"\n{label}:")
    print(f"Investor ID: {match['investorId']}")
    print(f"Profession: {match['profession']}")
    print(f"Risk Appetite: {match['riskAppetite']}")
    print(f"Budget: ₹{match['budget']}")
    print(f"Location Match: {'Yes' if match['locationMatch'] else 'No'}")
    print(f"Predicted Match Score: {match['score']}")

joblib.dump(best_knn, 'knn_investor_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
print("\n💾 Model and Scaler saved successfully!")
