import SpatialKPIDensity

# prep_inputs_by_cell.py
# ---------------------------------------------------------------
# Fetch the three objects your SpatialKPIDensity constructor needs
# when you want to render ONE sector (siteid_cellid) only.
# ---------------------------------------------------------------

import requests
import pandas as pd


def fetch_inputs_for_cell(
    *,
    base_url: str = "http://127.0.0.1:8000",
    siteid_cellid: str,              # <-- NEW: "100046-121"
    date: str,                       #  "YYYY-MM-DD"
    kpi_col: str = "rsrp",
    beamwidth_default: int = 65,
    timeout: int = 10,
) -> tuple[pd.DataFrame, str, pd.DataFrame]:
    """
    Returns
    -------
    df_all : pd.DataFrame
        Every point for that cell+day. Must have 'latitude','longitude', <kpi_col>.
    kpi_col : str
        Echoed unchanged (so your caller can plug it straight in).
    cells : pd.DataFrame
        One-row DataFrame with 'latitude','longitude','azimuth','beamwidth'.
    """
    ssv       = f"{base_url.rstrip('/')}/ssv"
    get_json  = lambda path, **params: requests.get(
        f"{ssv}{path}", params=params or None, timeout=timeout
    ).json()

    # ------------------------------------------------------------------
    # 1) Full-resolution KPI samples for this single sector
    #    /ssv/all_data/?siteid_cellid=<XX>&date=<YYYY-MM-DD>
    # ------------------------------------------------------------------
    df_all = pd.DataFrame(
        get_json("/all_data/", siteid_cellid=siteid_cellid, date=date)
    )

    # Narrow down to exactly the columns SpatialKPIDensity expects
    df_all = df_all[["latitude", "longitude", kpi_col]]

    # ------------------------------------------------------------------
    # 2) Geometry row (lat / lon / azimuth / beamwidth) for THIS cell only
    #    We still call /get_site_info/<siteid>; then filter the row we need.
    # ------------------------------------------------------------------
    siteid = int(siteid_cellid.split("-")[0])
    df_info = pd.DataFrame(get_json(f"/get_site_info/{siteid}"))

    cell_row = df_info.loc[df_info["siteid_cellid"] == siteid_cellid].copy()
    if cell_row.empty:
        raise ValueError(f"Cell {siteid_cellid} not found in site-info table")

    if "beamwidth" not in cell_row.columns:
        cell_row["beamwidth"] = beamwidth_default

    # Keep only the four mandatory columns
    cell_row = cell_row[["latitude", "longitude", "azimuth", "beamwidth"]]

    return df_all, kpi_col, cell_row



df_all, kpi, cell_df = fetch_inputs_for_cell(
    base_url="http://127.0.0.1:8000",
    siteid_cellid="100046-121",
    date="2025-01-01",
    kpi_col="rsrp",
)

sp = SpatialKPIDensity(
    df_all=df_all,          # Dask-ready point cloud
    kpi_col=kpi,            # "rsrp"
    cells=cell_df,          # one-row DataFrame
    crs_in=4326,
    crs_plot=3857,
    canvas=(2048, 2048),
)

print(sp)