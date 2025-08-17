# BACKEND/router/reports.py
from fastapi import APIRouter, status
from celery.result import AsyncResult
from celery_app import celery_app
from tasks.reports import generate_report

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

@router.post(
    "/{report_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a report generation task",
)
async def queue_report(report_id: int):
    """
    Enqueue a Celery task that will generate a PDF (or whatever) for *report_id*.

    Returns the Celery task ID so the client can poll `/reports/status/{task_id}`.
    """
    task = generate_report.delay(report_id)
    return {"task_id": task.id, "status": "queued"}


@router.get(
    "/status/{task_id}",
    summary="Check the status/result of a queued report",
)
async def report_status(task_id: str):
    """
    Look up the Celery task by *task_id* and return its current state
    (PENDING, STARTED, SUCCESS, FAILURE, etc.) plus the result if finished.
    """
    res: AsyncResult = celery_app.AsyncResult(task_id)
    return {"state": res.state, "result": res.result}
