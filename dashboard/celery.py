from celery import Celery
from .services import check_alerts

app = Celery('trading_alerts')

@app.task
def run_alert_checks():
    check_alerts()
