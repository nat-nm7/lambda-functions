import json
import logging
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    webhook_url = event["webhook_url"]
    message = event["message"]

    logger.info("Sending request to Discord Webhook...")
    payload = {
        "content": message,
        "username":"Amazon Web Services",
        "avatar_url": "https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/main/dist/Groups/AWSCloud.png"
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )

    urllib.request.urlopen(req)
    logger.info("Discord notification completed successfully")
