import pandas as pd
from sqlalchemy import create_engine, inspect, types as sqltypes

kpi_df = pd.read_csv("C:\\Users\\erena\\Desktop\\Reporter\\Backend\\Files\\kpi_data_2.csv")
all_df = pd.read_csv("C:\\Users\\erena\\Desktop\\Reporter\\Backend\\Files\\all_data_3.csv")
celldb_df = pd.read_csv("C:\\Users\\erena\\Desktop\\Reporter\\Backend\\Files\\overall_data_1.csv")
print(kpi_df.dtypes)
print()
print(all_df.dtypes)
print()
print(celldb_df.dtypes)
# # Define database connection string
# connection_string = 'postgresql://postgres:ankara_123@localhost:5432/reporter'

# # Create engine
# engine = create_engine(connection_string)


# ───────────────────────────────────────────────
# 1) Create the SQLAlchemy engine
# ───────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://postgres:ankara_123@localhost:5432/reporter",
    echo=False,          # True → prints every SQL statement (great for debugging)
    future=True,
)

# ───────────────────────────────────────────────
# 2) Helper: write a DF to the DB if the table is absent
# ───────────────────────────────────────────────
def write_if_missing(df: pd.DataFrame, table_name: str, *, schema: str = "public"):
    insp = inspect(engine)
    if not insp.has_table(table_name, schema=schema):
        print(f"Creating table ⇢ {schema}.{table_name}")

        # (optional) fine-tune a couple of dtypes:
        overrides = {
            "date":           sqltypes.Date,      # store as DATE instead of TEXT
            "longitude":      sqltypes.Numeric(9, 6),
            "latitude":       sqltypes.Numeric(9, 6),
        }
        df.to_sql(
            name        = table_name,
            con         = engine,
            schema      = schema,
            if_exists   = "fail",   # insure we only create once
            index       = False,
            dtype       = overrides,
            chunksize   = 10_000,   # batch insert size when the CSV is large
            method      = "multi",  # multi-row insert ⇒ faster
        )
    else:
        print(f"Table {schema}.{table_name} already exists → skipping.")

# ───────────────────────────────────────────────
# 3) Ship the three data sets
# ───────────────────────────────────────────────
write_if_missing(kpi_df,    "kpi_data")
write_if_missing(all_df,    "all_data")
write_if_missing(celldb_df, "celldb")