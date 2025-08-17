
import pandas as pd
import numpy as np
from pyproj import Geod

df = pd.read_csv("C:\\Users\\huaweieayture\\Desktop\\trial\data\\overall_data_1.csv",sep=",",  on_bad_lines="skip",low_memory=False)

print(df.dtypes)

g = Geod(ellps="WGS84")

# column vectors → NumPy arrays
lons = df["longitude"].to_numpy()
lats = df["latitude"].to_numpy()

# make 1-D arrays of the same length, filled with constants
az   = np.full(lons.shape,  180.0)   # 90° = east
dist = np.full(lons.shape,  10.0)   # 10 metres

lon2, lat2, _ = g.fwd(lons, lats, az, dist)

df["longitude_shifted"] = lon2
df["latitude_shifted"]  = lat2

print(df)
cols_to_drop = [
    "latitude",              # example
    "longitude",              # example
    # …
]
df.drop(columns=cols_to_drop, errors="ignore", inplace=True)

df.rename(columns={'latitude_shifted': 'latitude', 'longitude_shifted': 'longitude'}, inplace=True)


# column vectors → NumPy arrays
lons = df["longitude"].to_numpy()
lats = df["latitude"].to_numpy()

# make 1-D arrays of the same length, filled with constants
az   = np.full(lons.shape,  45.0)   # 90° = east
dist = np.full(lons.shape,  10.0)   # 10 metres

lon2, lat2, _ = g.fwd(lons, lats, az, dist)

df["longitude_shifted"] = lon2
df["latitude_shifted"]  = lat2

print(df)
cols_to_drop = [
    "latitude",              # example
    "longitude",              # example
    # …
]
df.drop(columns=cols_to_drop, errors="ignore", inplace=True)

df.rename(columns={'latitude_shifted': 'latitude', 'longitude_shifted': 'longitude'}, inplace=True)


df.to_csv(
    "C:\\Users\\huaweieayture\\Desktop\\trial\data\\overall_data_1.csv",   # output path / name
    sep=",",           # comma is the default, but it’s explicit here
    index=False,       # drop the row index column
)