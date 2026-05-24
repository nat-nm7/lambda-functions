import json
import urllib.request

def lambda_handler(event, context):

    webhook_url = event["webhook_url"]
    message = event["message"]

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
