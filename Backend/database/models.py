from sqlalchemy import BigInteger, Column, Date, Double, MetaData, Numeric, Table, Text
from sqlalchemy.orm.base import Mapped

metadata = MetaData()


all_data = Table(
    'all_data', metadata,
    Column('date', Date),
    Column('siteid_cellid', Text),
    Column('rsrp', Double(53)),
    Column('rsrq', Double(53)),
    Column('rssinr', Double(53)),
    Column('fail', BigInteger),
    Column('block', BigInteger),
    Column('dl_throughput', Double(53)),
    Column('ul_throughput_mb', Double(53)),
    Column('total_traffic_mb', Double(53)),
    Column('longitude', Numeric(9, 6)),
    Column('latitude', Numeric(9, 6)),
    schema='public'
)


celldb = Table(
    'celldb', metadata,
    Column('siteid_cellid_orjinal', Text),
    Column('date', Date),
    Column('siteid', BigInteger),
    Column('sitename', Text),
    Column('cellname', Text),
    Column('siteid_cellid', Text),
    Column('cell_id', BigInteger),
    Column('city', Text),
    Column('district', Text),
    Column('azimuth', BigInteger),
    Column('beamwidth', BigInteger),
    Column('longitude', Numeric(9, 6)),
    Column('latitude', Numeric(9, 6)),
    schema='public'
)


kpi_data = Table(
    'kpi_data', metadata,
    Column('date', Date),
    Column('siteid_cellid', Text),
    Column('rsrp', Double(53)),
    Column('rsrq', Double(53)),
    Column('rssinr', Double(53)),
    Column('fail', BigInteger),
    Column('block', BigInteger),
    Column('dl_throughput', Double(53)),
    Column('ul_throughput_mb', Double(53)),
    Column('total_traffic_mb', Double(53)),
    schema='public'
)
