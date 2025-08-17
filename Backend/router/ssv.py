from fastapi import APIRouter,HTTPException,Request,Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import  Depends
from database.db import NotFoundError,get_db
from database.ssv import site_kpi,site_kpi_by_list,distinct_cells_for_site,siteids_starting_with,get_all_data,site_info,all_data_by_list
from .limiter import limiter
from typing import List
from datetime import date
from schemas import KPISiteQueryParams, KPIData,KPISiteidCellidQueryParams,AllData,AllDataQueryParams
from starlette.requests import Request as req
import sys,logging,json



router = APIRouter(
    prefix="/ssv"
)
#http://127.0.0.1:8000/ssv/get_site_kpi/?siteid=100046&date=2025-01-01
@router.get(
    "/get_site_kpi/",
    response_model=List[KPIData],          # list → FastAPI handles JSON encode
)
#@limiter.limit("1/second")
async def get_site_kpi(
    params: KPISiteQueryParams = Depends(),    # pulls ?siteid_cellid= & ?date=
    request: Request = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await site_kpi(params.siteid, params.date, db)
        return rows
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")

#GET http://127.0.0.1:8000/ssv/site_kpi_by_list/?siteid_cellids=["100046-121",100046-141","100046-165"]&date=2025-01-01

@router.get(
    "/site_kpi_by_list/",
    response_model=List[KPIData],          # list → FastAPI handles JSON encode
)
#@limiter.limit("1/second")
async def get_site_kpi_by_list(
    params : KPISiteidCellidQueryParams = Depends(),
    request: Request  = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):
    
    
    try:
        rows = await site_kpi_by_list(json.loads(params.siteid_cellids), params.date, db)
        
        return rows
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
    
@router.get("/site_cells/{siteid}")#27566
#@limiter.limit("1/second")
async def get_site_cells(
    siteid: int,
    request: Request  = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):

    try:
        cells = await distinct_cells_for_site(siteid, db)
        # return {"siteid": siteid, "cells": cells}
        return cells
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
    
@router.get("/get_site_info/{siteid}")#27566
#@limiter.limit("1/second")
async def get_site_info(
    siteid: int,
    request: Request  = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):

    try:
        site = await site_info(siteid, db)
        return site
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
    
@router.get("/sites/by_prefix/{prefix}")
#@limiter.limit("1/second")
async def sites_by_prefix(
    prefix: str,
    request: Request  = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):
    try:
        ids = await siteids_starting_with(prefix, db)
        return ids
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
    

@router.get(
    "/all_data/",
    response_model=list[AllData],              # ← use the schema
)
async def get_all_datas(
    params: AllDataQueryParams = Depends(),    # ?siteid_cellid=&date=
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await get_all_data(params.siteid_cellid, params.date, db)
        return rows 
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
    
@router.get(
    "/get_all_data_by_list/",
    response_model=List[AllData],          # list → FastAPI handles JSON encode
)
#@limiter.limit("1/second")
async def get_all_data_by_list(
    params : KPISiteidCellidQueryParams = Depends(),
    request: Request  = None,        # keep if you need IP etc.
    db: AsyncSession = Depends(get_db),
):
    
    
    try:
        rows = await all_data_by_list(json.loads(params.siteid_cellids), params.date, db)
        
        return rows
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")
         
