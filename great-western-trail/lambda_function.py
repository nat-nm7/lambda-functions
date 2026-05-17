import random
import boto3

ssm = boto3.client("ssm")

PARAM_PATH = "/great-western-trail"

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

def lambda_handler(event, context):
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
    response_body = """{header}

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

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain;charset=UTF-8"
        },
        "body": response_body
    }
