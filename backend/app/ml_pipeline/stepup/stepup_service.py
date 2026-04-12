from .price_predictor import predict_price
from .finance_engine import calculate_finance

def run_stepup(payload):

    current, future = predict_price(payload)

    finance = calculate_finance(
        current=current,
        future=future,
        stake=payload["investor_stake"],
        rent=payload["monthly_rent"],
        years=payload["years"]
    )

    return {
        "current_price": round(current),
        "future_price": round(future),
        "finance": finance
    }
