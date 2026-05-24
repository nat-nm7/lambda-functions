import json
import boto3
import logging

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jpholiday

NOTIFIER_FUNCTION_NAME = "discord-notifier"
SCHEDULE_NAME = "salary-day-reminder"
TIMEZONE = "Asia/Tokyo"
SALARY_DAY = 25
CRON_HOUR = 9
CRON_MINUTE = 0

lambda_client = boto3.client("lambda")
scheduler = boto3.client("scheduler")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_discord(event):

    lambda_client.invoke(
        FunctionName=NOTIFIER_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps(event)
    )

def next_salary_day():

    now = datetime.now(ZoneInfo(TIMEZONE))

    year = now.year
    month = now.month + 1

    if month == 13:
        year += 1
        month = 1

    dt = datetime(
        year,
        month,
        SALARY_DAY,
        CRON_HOUR,
        CRON_MINUTE,
        tzinfo=ZoneInfo(TIMEZONE)
    )

    while True:

        if dt.weekday() >= 5:
            dt -= timedelta(days=1)
            continue

        if jpholiday.is_holiday(dt.date()):
            dt -= timedelta(days=1)
            continue

        break

    return dt

def update_schedule(dt):

    current = scheduler.get_schedule(
        Name=SCHEDULE_NAME
    )

    scheduler.update_schedule(
        Name=SCHEDULE_NAME,
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        ScheduleExpression=(
            f"at({dt.strftime('%Y-%m-%dT%H:%M:%S')})"
        ),
        ScheduleExpressionTimezone=TIMEZONE,
        State="ENABLED",
        Target=current["Target"]
    )

def lambda_handler(event, context):

    send_discord(event)
    logger.info("Discord notifier invoked")

    next_dt = next_salary_day()
    update_schedule(next_dt)
    logger.info(f"Schedule updated: {next_dt.isoformat()}")
