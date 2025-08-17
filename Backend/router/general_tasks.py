from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db,NotFoundError          # <- async session dependency
from database.general_task_service import groups_with_items,active_group_summaries,ensure_group_archive,delete_group_and_data,TaskGroupSummary,TaskGroupOut

from fastapi.responses import FileResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskGroupOut])
async def all_task_groups(
    username: str | None = Query(None, description="Owner filter (optional)"),
    db: AsyncSession     = Depends(get_db),
):
    """
    Return every Task-Group (optionally belonging to *username*)
    together with its Task-Items.
    """
    try:
        groups = await groups_with_items(db, username=username)
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error: {str(e)} ")

    # Pydantic does all the heavy lifting – just return the ORM objects
    return groups


@router.get(
    "/active",
    response_model=list[TaskGroupSummary],
    summary="Queued + running task groups only (no items)"
)
async def list_active_groups(
    db: AsyncSession = Depends(get_db)
):
    """
    Lightweight view: just `group_id`, `type`, `created_at`, `status`.
    """
    return await active_group_summaries(db)


@router.get("/{gid}/download", summary="Download ZIP for a task-group")
async def download_task_group(
    gid: int, db: AsyncSession = Depends(get_db),
):
    zip_path = await ensure_group_archive(db, gid)
    return FileResponse(
        path=zip_path,
        filename=zip_path.name,
        media_type="application/zip",
    )


@router.delete(
    "/delete/{gid}",
    status_code=204,
    summary="Delete a task-group and all associated data",
)
async def delete_task_group(
    gid: int, db: AsyncSession = Depends(get_db),
):
    await delete_group_and_data(db, gid)