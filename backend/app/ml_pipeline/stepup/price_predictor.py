import pandas as pd
from .loader import get_spatial_model, get_loc_df, get_hpi

def get_lat_long(locality):
    loc_df = get_loc_df()
    row = loc_df[loc_df["locality"] == locality]
    return float(row.iloc[0]["latitude"]), float(row.iloc[0]["longitude"])

def get_growth_factor(bhk, years):
    hpi = get_hpi()
    col = {1:"bhk1",2:"bhk2",3:"bhk3"}.get(bhk,"all")
    series = hpi[col].dropna()
    start = series.iloc[-61]
    end = series.iloc[-1]
    cagr = (end/start)**(1/5) - 1
    return (1 + cagr) ** years

def predict_price(data):
    spatial_model = get_spatial_model()
    lat, lon = get_lat_long(data["locality"])

    df = pd.DataFrame([{
        **data,
        "latitude": lat,
        "longitude": lon
    }])

    current = spatial_model.predict(df)[0]
    future = current * get_growth_factor(
        data["bedroom_num"],
        data["years"]
    )

    return current, future
