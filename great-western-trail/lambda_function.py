import random
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client("ssm")

PARAM_PATH = "/great-western-trail"

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_text}</title>
    <style>
        body {{ font-family: monospace; font-size: 16px; line-height: 1.5; background-color: #f8f9fa; color: #333; padding: 20px; }}
        pre {{ background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; white-space: pre-wrap; font-family: monospace; }}
        .seed-info {{ color: #666; margin-bottom: 15px; }}
        .form-container {{ margin-bottom: 20px; display: flex; gap: 10px; align-items: center; }}
        .input-seed {{ box-sizing: border-box; height: 44px; padding: 0 12px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; font-family: monospace; width: 180px; }}
        .btn {{ box-sizing: border-box; height: 44px; display: inline-flex; align-items: center; justify-content: center; background-color: #007bff; color: white; text-decoration: none; padding: 0 20px; font-size: 16px; font-weight: bold; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: none; cursor: pointer; font-family: monospace; white-space: nowrap; }}
        .btn:hover {{ background-color: #0056b3; }}
    </style>
</head>
<body>
    <pre>{content}</pre>
    <hr>
    <div class="seed-info">Seed: {seed_value}</div>
    <form action="{base_url}" method="get" class="form-container">
        <input type="text" name="seed" class="input-seed" placeholder="シード（空欄可）">
        <button type="submit" class="btn">引き直す</button>
    </form>
</body>
</html>"""

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

def generate_main_text(seed_value):
    random.seed(seed_value)

    # 1. 私有、拡張建物タイルの生成 (1〜12)
    private_tiles_first_half = []  # 1〜5用
    private_tiles_second_half = [] # 6〜10用
    expansion_tiles = [] # 11〜12用

    for i in range(1, 13):
        side = random.choice(["a", "b"])
        tile_str = f"{i:2d}{side}" # 1桁の数字の前に半角スペースを入れて揃える(例: " 1a")

        if i <= 5:
            private_tiles_first_half.append(tile_str)
        elif i <= 10:
            private_tiles_second_half.append(tile_str)
        else:
            expansion_tiles.append(tile_str)

    # スペース区切りの文字列にする
    private_row1 = " ".join(private_tiles_first_half)
    private_row2 = " ".join(private_tiles_second_half)
    expansion_row = " ".join(expansion_tiles)

    # 2. 共有建物タイルの生成 (A〜Gのシャッフル)
    neutral_tiles = ["A", "B", "C", "D", "E", "F", "G"]
    random.shuffle(neutral_tiles)
    neutral_row = " ".join(neutral_tiles) # 見やすさのために文字の間にスペースを挟む

    # 3. トリプルクォートで文章を組み立てる
    main_text = """{header}

{title_private}
{p_row1}
{p_row2}

{title_expansion}
{e_row}

{title_neutral}
{n_row}

{footer}""".format(
        header=PARAMS["MESSAGE_HEADER"],
        title_private=PARAMS["TITLE_PRIVATE"],
        p_row1=private_row1,
        p_row2=private_row2,
        title_expansion=PARAMS["TITLE_EXPANSION"],
        e_row=expansion_row,
        title_neutral=PARAMS["TITLE_NEUTRAL"],
        n_row=neutral_row,
        footer=PARAMS["MESSAGE_FOOTER"]
    )

    return main_text

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    seed_param = query_params.get("seed")

    request_context = event.get("requestContext") or {}
    domain_name = request_context.get("domainName", "")
    raw_path = event.get("rawPath", "/").strip()

    if "favicon.ico" in raw_path:
        response = {
            "statusCode": 204,
            "body": ""
        }
        return response

    current_base_url = f"https://{domain_name}{raw_path}"

    if seed_param and seed_param.strip() != "":
        logger.info(f"Seed detected. Recreating map with seed: {seed_param}")

        main_text = generate_main_text(seed_param)

        html_body = HTML_TEMPLATE.format(
            title_text=PARAMS["MESSAGE_HEADER"],
            base_url=current_base_url,
            seed_value=seed_param,
            content=main_text
        )

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html;charset=UTF-8"
            },
            "body": html_body
        }
        return response
    else:
        new_seed = str(random.randint(1, 99999999))
        redirect_url = f"{current_base_url}?seed={new_seed}"

        logger.info(f"First access or empty seed. Generating seed [{new_seed}] and redirecting to {redirect_url}")

        response = {
            "statusCode": 302,
            "headers": {
                "Location": redirect_url
            },
            "body": ""
        }
        return response
