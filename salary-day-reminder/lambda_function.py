import json
import boto3
import urllib.request

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jpholiday

scheduler = boto3.client("scheduler")
ssm = boto3.client("ssm")

PARAM_PATH = "/Lambda/salary-day-reminder"

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

WEBHOOK_URL = PARAMS["WEBHOOK_URL"]
SCHEDULE_NAME = PARAMS["SCHEDULE_NAME"]
TIMEZONE = PARAMS["TIMEZONE"]
SALARY_DAY = int(PARAMS["SALARY_DAY"])
RUN_HOUR = int(PARAMS["RUN_HOUR"])
RUN_MINUTE = int(PARAMS["RUN_MINUTE"])
MESSAGE = PARAMS["MESSAGE"]

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
