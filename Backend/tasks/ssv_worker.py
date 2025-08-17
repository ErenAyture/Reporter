# BACKEND/tasks/ssv_worker.py
from celery import shared_task

from database.ssv_task_service import mark_started_sync, mark_done_sync,get_ssv_args_sync
from .SSV.SSV4G import SSV4G
from .mutex_lock import lock
from config import settings



@shared_task(bind=True)
def process_one_item(self, item_id: int):
    ssv: SSV4G = None
    mark_started_sync(item_id, self.request.id)

    # ---------- real work ----------
    task_id, site_id, date, tech = get_ssv_args_sync(item_id)
    try:
        match tech:
            case "NR":
                pass
            case "LTE":
                print("HERE")
                ssv = SSV4G(siteid=site_id,
                            task_date=date,
                            mutex_lock=lock,
                            BASE_URL=settings.BASE_URL,
                            task_id=task_id)
                ssv.build()
            case "UMTS":
                pass
            case "GSM":
                pass
            case _:
                print(f'given tech could not be found: {tech}')
        
    except Exception as exc:
        mark_done_sync(item_id, ok=False, result=str(exc))
    else:
        mark_done_sync(item_id, ok=True, result="ok")
    
    # --------------------------------
    return f' itemid: {item_id} rest:{task_id} {site_id} {date} {tech}'
    

    
