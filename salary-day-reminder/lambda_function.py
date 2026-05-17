import json
import boto3
import logging
import urllib.request

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jpholiday

scheduler = boto3.client("scheduler")
ssm = boto3.client("ssm")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PARAM_PATH = "/salary-day-reminder"

def load_params():
    response = ssm.get_parameters_by_path(
        Path=PARAM_PATH,
        WithDecryption=False
    )
    params = {}
    for param in response["Parameters"]:
        key = param["Name"].replace(f"{PARAM_PATH}/", "")
        params[key] = param["Value"]
    return params

PARAMS = load_params()

def send_discord():

    payload = {
        "content": PARAMS["MESSAGE"]
    }

    req = urllib.request.Request(
        PARAMS["WEBHOOK_URL"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )

    urllib.request.urlopen(req)

def next_salary_day():

    now = datetime.now(ZoneInfo(PARAMS["TIMEZONE"]))

    year = now.year
    month = now.month + 1
    day = int(PARAMS["SALARY_DAY"])
    hour = int(PARAMS["RUN_HOUR"])
    minute = int(PARAMS["RUN_MINUTE"])

    if month == 13:
        year += 1
        month = 1

    dt = datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=ZoneInfo(PARAMS["TIMEZONE"])
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
        Name=PARAMS["SCHEDULE_NAME"]
    )

    scheduler.update_schedule(
        Name=PARAMS["SCHEDULE_NAME"],
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        ScheduleExpression=(
            f"at({dt.strftime('%Y-%m-%dT%H:%M:%S')})"
        ),
        ScheduleExpressionTimezone=PARAMS["TIMEZONE"],
        State="ENABLED",
        Target=current["Target"]
    )

def lambda_handler(event, context):

    send_discord()

    next_dt = next_salary_day()

    update_schedule(next_dt)

    logger.info(f"schedule updated: {next_dt.isoformat()}")
