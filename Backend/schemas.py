# schemas.py
from datetime import date
from typing import List,Annotated,Union,Optional
from fastapi import Query
import json

from pydantic import BaseModel, Field
'''
KPI SCHEMAS
'''
class KPISiteidCellidQueryParams(BaseModel):

    siteid_cellids: str #= Query(None, alias="item")
    date: date
class KPISiteQueryParams(BaseModel):
    """
    Validates the incoming query/path parameters.
    """
    siteid: str 
    date: date


class KPIData(BaseModel):
    """
    Outgoing row shape.  Keep only the columns you really need.
    """
    date: date
    siteid_cellid: str
    rsrp: float
    rsrq: float
    rssinr: float
    fail: int
    block: int
    dl_throughput: float
    ul_throughput_mb: float
    total_traffic_mb: float

class AllData(BaseModel):
    date:               date
    siteid_cellid:      str
    rsrp:               float
    rsrq:               float
    rssinr:             float
    fail:               int
    block:              int
    dl_throughput:      float
    ul_throughput_mb:   float
    total_traffic_mb:   float
    longitude:          Optional[float] = Field(None, description="Decimal degrees")
    latitude:           Optional[float] = Field(None,  description="Decimal degrees")

    class Config:
        orm_mode = True        # allows .from_orm(row) if you switch to ORM


# ── 2.  Query parameters for a single-day request ───────────────────────
class AllDataQueryParams(BaseModel):
    siteid_cellid: str
    date: date
