import json
import requests
import pandas as pd
BASE_URL = "http://127.0.0.1:8000"          # <-- change for Docker / prod
SSV = f"{BASE_URL}/ssv"                     # convenience prefix
siteid = 27566
resp = requests.get(f"{SSV}/site_cells/{siteid}", timeout=10)
def pretty(title, response: requests.Response):
    """Small helper to print status + JSON."""
    payload = response.json()
    # Most of your endpoints return list[dict]; this handles that.
    df = pd.DataFrame(payload)
    print(f"\n🟢 {title}  ->  HTTP {response.status_code}")
    print(type(response.json()))
    # print(df)
pretty("site_cells", resp)