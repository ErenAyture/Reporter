from database.db import NotFoundError
from .models import kpi_data,celldb,all_data
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,distinct,cast, String

from datetime import date
from typing import Sequence, Mapping, Any, List

'''
KPI DATA
'''
async def site_kpi(
    siteid: str,                      # site id
    query_date: date,
    db: AsyncSession,
) -> Sequence[Mapping[str, Any]]:
    """
    Return ≤30 KPI rows for all cells that belong to one *site* on a given day.
    For an underscore separator the LIKE pattern is '123456\\_%'
    (the back-slash escapes the underscore, which is a single-char wildcard in SQL).
    """
    pattern = f"{siteid}-%"        # 100046-%

    stmt = (
        select(kpi_data)
        .where(
            kpi_data.c.siteid_cellid.like(pattern),
            kpi_data.c.date == query_date,
        )
        .order_by(kpi_data.c.siteid_cellid.asc())
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        raise NotFoundError(f"No KPI data for site {siteid} on {query_date}")
    return rows

async def site_kpi_by_list(
    siteid_cellids: List[str],                      # site id
    query_date: date,
    db: AsyncSession,
) -> Sequence[Mapping[str, Any]]:
    """
    Return KPI rows for all cells that belong to one *site* on a given day.
    For an underscore separator the LIKE pattern is '123456\\_%'
    (the back-slash escapes the underscore, which is a single-char wildcard in SQL).
    """
    stmt = (
        select(kpi_data)
        .where(
            kpi_data.c.siteid_cellid.in_(siteid_cellids),
            kpi_data.c.date == query_date,
        )
        .order_by(kpi_data.c.siteid_cellid.asc())
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        raise NotFoundError(f"No KPI data for cells {siteid_cellids} on {query_date}")
    return rows

'''
CELL DB
'''
async def distinct_cells_for_site(
    siteid: int,
    db: AsyncSession,
) -> list[str]:
    """
    Return the unique `siteid_cellid` values that belong to one site.
    """
    stmt = (
        select(distinct(celldb.c.siteid_cellid))   # SELECT DISTINCT ...
        .where(celldb.c.siteid == siteid)          # WHERE siteid = :siteid
    )

    result = await db.execute(stmt)
    if not result:
        raise NotFoundError(f"No cells for {siteid} ")
    return [row[0] for row in result]

async def siteids_starting_with(
    prefix: str,                # e.g. "27566"
    db: AsyncSession,
) -> list[int]:
    """
    Return the `siteid` values whose text form begins with <prefix>.
    """
    stmt = (
        select(distinct(celldb.c.siteid))
        .where(cast(celldb.c.siteid, String).like(f"{prefix}%"))
        .limit(10)
        .order_by(celldb.c.siteid.asc())
    )

    result = await db.execute(stmt)
    return [row.siteid for row in result]

async def site_info(
    siteid: int,
    db: AsyncSession,
) -> Sequence[Mapping[str, Any]]:
    """
    Return every distinct `siteid_cellid` that belongs to one site
    together with site-level latitude / longitude / azimuth.
    """
    stmt = (
        select(
            distinct(celldb.c.siteid_cellid),  # DISTINCT on this column
            celldb.c.siteid,
            celldb.c.latitude,
            celldb.c.longitude,
            celldb.c.azimuth,
            celldb.c.beamwidth,
        )
        .where(celldb.c.siteid == siteid)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()             # RowMapping → dict-like rows

    if not rows:
        raise NotFoundError(f"No cells for site {siteid}")

    return rows 
'''
ALL DATA
'''
async def get_all_data(
    siteid_cellid: str,                
    query_date: date,
    db: AsyncSession,
) -> Sequence[Mapping[str, Any]]:
    """
    Return the `siteid` values whose text form begins with <prefix>.
    """
    stmt = (
        select(all_data)
        .where(
            all_data.c.siteid_cellid == siteid_cellid,
            all_data.c.date == query_date,
        )
        .order_by(all_data.c.date)           # optional
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()           # RowMapping → dict-like rows

    if not rows:
        raise NotFoundError(
            f"No all_data rows for {siteid_cellid} on {query_date}"
        )
    return rows

async def all_data_by_list(
    siteid_cellids: List[str],                
    query_date: date,
    db: AsyncSession,
) -> Sequence[Mapping[str, Any]]:
    """
    Return the `siteid` values whose text form begins with <prefix>.
    """
    stmt = (
        select(all_data)
        .where(
            all_data.c.siteid_cellid.in_(siteid_cellids),
            all_data.c.date == query_date,
        )
        .order_by(all_data.c.siteid_cellid)           # optional
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()           # RowMapping → dict-like rows

    if not rows:
        raise NotFoundError(
            f"No all_data rows for {siteid_cellids} on {query_date}"
        )
    return rows