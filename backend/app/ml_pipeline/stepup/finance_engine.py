def calculate_finance(current, future, stake, rent, years):
    invested = current * stake
    rent_income = rent * stake * 12 * years
    buyback = future * stake
    roi = ((rent_income + buyback - invested) / invested) * 100

    return {
        "invested": round(invested),
        "rent_income": round(rent_income),
        "buyback_price": round(buyback),
        "roi": round(roi, 2)
    }
