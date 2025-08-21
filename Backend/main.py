from fastapi import FastAPI, Response #,Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.db import get_db
# from database.models import all_data, kpi_data, celldb   # the Table objects you defined
# from typing import Union
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from router.limiter import limiter
from router.ssv import router as ssv_router
from router.reports import router as report_router
from router.ssv_task import router as ssv_task_router
from router.general_tasks import router as tasks_router
from router.task_download import router as download_router
from router.ws import ws_router
from router.ws_notify import router as ws_notify
from router.auth import decode_dashboard_jwt
from infrustructure.ws_bus import bus
from contextlib import asynccontextmanager


# from celery.result import AsyncResult
# from celery_app import celery_app
# from tasks.reports import generate_report   # the sample task
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.startup()    # 👈 THIS LINE FIXES IT
    yield
    # optional cleanup here
    # await bus.stop() if defined
app = FastAPI(
    title="Reporter",
    root_path= settings.ROOT_PATH
    ,lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,       # or ["*"] while developing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Routers
app.include_router(ssv_router)
app.include_router(report_router)
app.include_router(ssv_task_router)
app.include_router(tasks_router)
app.include_router(download_router)
app.include_router(ws_router)
app.include_router(ws_notify)


#set limiter for multiple request at a time
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)

@app.get("/")
def read_root():

    return Response("Server is Running")

class VerifyIn(BaseModel):
    token: str

class VerifyOut(BaseModel):
    ok: bool
    username: str | None = None
    exp: int | None = None  # epoch seconds if present

@app.post("/auth/verify", response_model=VerifyOut)
def verify(body: VerifyIn):
    username, exp = decode_dashboard_jwt(body.token)
    return VerifyOut(ok=True, username=username, exp=exp)

# @app.post("/reports/{report_id}")
# async def queue_report(report_id: int):
#     task = generate_report.delay(report_id)
#     return {"task_id": task.id, "status": "queued"}

# @app.get("/reports/status/{task_id}")
# async def report_status(task_id: str):
#     res: AsyncResult = celery_app.AsyncResult(task_id)
#     return {"state": res.state, "result": res.result}

# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
# #100046-121
# @app.get("/kpi/{siteid_cellid}")
# async def latest_kpi(siteid_cellid: str, db: AsyncSession = Depends(get_db)):
#     stmt = (
#         select(kpi_data)
#         .where(kpi_data.c.siteid_cellid == siteid_cellid)
#         .order_by(kpi_data.c.date.desc())
#         .limit(30)
#     )
#     result = await db.execute(stmt)
#     rows = result.mappings().all()      # maps() → dict-like rows
#     return rows


# ⬇️  Only executed when you call `python main.py`
if __name__ == "__main__":
    import uvicorn
    # Option A – pass the import string (lets --reload work)
    # uvicorn.run(
    #     "main:app",          # "module_name:variable_name"
    #     host="0.0.0.0",      # or "127.0.0.1" for local-only
    #     port=8000,
    #     reload=True,         # hot-reload in development
    #     log_level="info",
    # )

    # Option B – pass the object directly (no reload hot-swap)
    uvicorn.run(app, host=settings.BASE_HOST, port=settings.BASE_PORT, log_level="info")