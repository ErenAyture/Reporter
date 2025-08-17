# BACKEND/tasks/maintenance.py

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
from typing import List

from celery import shared_task

from database.db import session_scope           # your helper from db.py
from database.models_tasks import TaskGroup
from database.result_archiver import ResultArchiver      # zips live here

# ────────────────────────────────────────────────────────────────
# configuration – change in one place
# ────────────────────────────────────────────────────────────────
AGE_LIMIT  = timedelta(days=15)                 # keep the last 15 days
_ARCHIVER  = ResultArchiver()                   # defaults: outputs/, results/
_RESULTS   : Path = _ARCHIVER.results_dir
_OUTPUTS   : Path = _ARCHIVER.outputs_dir


@shared_task(name="tasks.maintenance.cleanup_tmp")
def cleanup_tmp() -> str:
    """
    Periodic maintenance task.

    * For every  <results>/<gid>.zip  older than AGE_LIMIT
        – delete the zip file
        – delete leftovers in   outputs/<gid>/
        – delete TaskGroup row  (cascade → TaskItem / SSVTask)
    * Returns a short text so Celery shows something useful.
    """
    cutoff = datetime.now(timezone.utc) - AGE_LIMIT
    removed: List[int] = []

    # pass 1 ─ scan result archives
    for zip_file in _RESULTS.glob("*.zip"):
        zip_mtime = datetime.fromtimestamp(zip_file.stat().st_mtime,
                                           tz=timezone.utc)
        if zip_mtime >= cutoff:          # still recent → keep
            continue

        try:
            gid = int(zip_file.stem)     # "24.zip" → 24
        except ValueError:
            continue                     # ignore stray files such as README.zip

        # pass 2 ─ delete DB data (if it still exists)
        with session_scope() as db:
            grp = db.get(TaskGroup, gid)
            if grp is not None:
                db.delete(grp)
                db.commit()

        # pass 3 ─ delete files on disk
        zip_file.unlink(missing_ok=True)                       # results/<gid>.zip
        shutil.rmtree(_OUTPUTS / str(gid), ignore_errors=True) # outputs/<gid>/

        removed.append(gid)

    return f"cleanup removed {len(removed)} group(s): {removed or 'none'}"


# ---------------------------------------------------------------------------

def _delete_dir(path: Path) -> None:
    """Recursively remove *path* if it exists."""
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)

def _delete_file(path: Path) -> None:
    """Unlink *path* if it exists."""
    try:
        path.unlink(missing_ok=True)
    except AttributeError:                 # Py < 3.8 fallback
        if path.exists():
            path.unlink()
