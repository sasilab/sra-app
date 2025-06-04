import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_pvnode_forecast(latitude, longitude, slope, orientation, forecast_days=2):
    """
    ## Returns a 2 days forecast using the pvnode API.

    Input Arguments:
    - latitude of the string
    - longitude of the string
    - slope of the string
    - orientation of the string

    Returns:
    - pandas DataFrame with the rows GTI and temp

     References
    ----------
    - [1]
    ---
    """
    url = "https://api.pvnode.com/v1/forecast/"
    headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
    body = {
        "latitude": latitude,
        "longitude": longitude,
        "slope": slope,
        "orientation": orientation,
        "required_data": "GTI,temp",
        "past_days": 0,
        "forecast_days": forecast_days,
    }
    response = requests.get(url, headers=headers, params=body)
    data = response.json()
    df = pd.DataFrame(data["values"]).copy()
    df["dtm"] = pd.to_datetime(df["dtm"])
    df.set_index("dtm", inplace=True)
    return df
