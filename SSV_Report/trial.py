"""
demo_ssv_requests.py
--------------------
Examples for every /ssv/* endpoint using the *requests* library.
Adapt them or copy-paste straight into a notebook / script.
"""

import json
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"          # <-- change for Docker / prod
SSV = f"{BASE_URL}/ssv"                     # convenience prefix


def pretty(title, response: requests.Response):
    """Small helper to print status + JSON."""
    payload = response.json()
    # Most of your endpoints return list[dict]; this handles that.
    df = pd.DataFrame(payload)
    print(f"\n🟢 {title}  ->  HTTP {response.status_code}")
    # pprint.pp(response.json())
    print(df)


# ────────────────────────────────────────────────────────────────
# 1) /ssv/get_site_kpi/
#    ?siteid=<str>&date=<YYYY-MM-DD>
# ────────────────────────────────────────────────────────────────
params = {"siteid": "100046", "date": "2025-01-01"}
resp = requests.get(f"{SSV}/get_site_kpi/", params=params, timeout=10)
pretty("get_site_kpi", resp)


# ────────────────────────────────────────────────────────────────
# 2) /ssv/site_kpi_by_list/
#    ?siteid_cellids=<JSON list string>&date=<YYYY-MM-DD>
#    NOTE: send the list **as a JSON-encoded string** because your
#    endpoint later does `json.loads(params.siteid_cellids)`.
# ────────────────────────────────────────────────────────────────
cell_list = ["100046-121", "100046-141", "100046-165"]
params = {
    "siteid_cellids": json.dumps(cell_list),   # <-- stringify!
    "date": "2025-01-01",
}
resp = requests.get(f"{SSV}/site_kpi_by_list/", params=params, timeout=10)
pretty("site_kpi_by_list", resp)


# ────────────────────────────────────────────────────────────────
# 3) /ssv/site_cells/{siteid}
# ────────────────────────────────────────────────────────────────
siteid = 27566
resp = requests.get(f"{SSV}/site_cells/{siteid}", timeout=10)
pretty("site_cells", resp)


# ────────────────────────────────────────────────────────────────
# 4) /ssv/get_site_info/{siteid}
# ────────────────────────────────────────────────────────────────
resp = requests.get(f"{SSV}/get_site_info/{siteid}", timeout=10)
pretty("get_site_info", resp)


# ────────────────────────────────────────────────────────────────
# 5) /ssv/sites/by_prefix/{prefix}
# ────────────────────────────────────────────────────────────────
prefix = "275"
resp = requests.get(f"{SSV}/sites/by_prefix/{prefix}", timeout=10)
pretty("sites_by_prefix", resp)


# ────────────────────────────────────────────────────────────────
# 6) /ssv/all_data/
#    ?siteid_cellid=<str>&date=<YYYY-MM-DD>
# ────────────────────────────────────────────────────────────────
params = {"siteid_cellid": "37233-191", "date": "2025-01-01"}
resp = requests.get(f"{SSV}/all_data/", params=params, timeout=10)
pretty("all_data", resp)
