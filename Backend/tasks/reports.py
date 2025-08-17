from celery import shared_task
import time, random

@shared_task(bind=True, max_retries=3, name="tasks.reports.generate_report")
def generate_report(self, report_id: int) -> str:
    try:
        time.sleep(random.uniform(3, 6))   # pretend work
        return f"report-{report_id}.pdf"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
