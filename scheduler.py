from apscheduler.schedulers.background import BackgroundScheduler
from .utils import cleanup_expired_containers

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(cleanup_expired_containers, 'interval', minutes=5)
    scheduler.start()
