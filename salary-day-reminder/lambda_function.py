import os
import json
import boto3
import urllib.request

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jpholiday


scheduler = boto3.client("scheduler")

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
SCHEDULE_NAME = os.environ["SCHEDULE_NAME"]
TIMEZONE = os.environ["TIMEZONE"]
SALARY_DAY = int(os.environ["SALARY_DAY"])
RUN_HOUR = int(os.environ["RUN_HOUR"])
RUN_MINUTE = int(os.environ["RUN_MINUTE"])
MESSAGE = os.environ["MESSAGE"]


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
        RUN_HOUR,
        RUN_MINUTE,
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


def send_discord():

    payload = {
        "content": MESSAGE
    }

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )

    urllib.request.urlopen(req)


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

    send_discord()

    next_dt = next_salary_day()

    update_schedule(next_dt)
