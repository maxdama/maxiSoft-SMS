from celery.schedules import crontab
from celery.task import periodic_task

@periodic_task(run_every=crontab(hour=0, minute=5, day_of_week="mon"))
def every_monday_morning():
    print("This is run every Monday morning at 7:30")