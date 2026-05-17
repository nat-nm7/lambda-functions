import random

def lambda_handler(event, context):
    response = ''
    response += 'こんにちは！GWTランダムタイル配置生成ツールです。'
    response += '\r\n'
    response += '\r\n'
    response += '・私有建物タイル'
    response += '\r\n'
    for i in range(1, 13):
        # 0か1の乱数を生成
        flag = random.randint(0, 1)
        # 出力
        if i < 10:
            response += ' '
        if flag:
            response += str(i) + 'a '
        else:
            response += str(i) + 'b '
        if i == 6 or i == 12:
            response += '\r\n'

    response += '\r\n'
    response += '・共有建物タイル'
    response += '\r\n'
    # AからGを内包するリストを作成
    tiles = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    # リストをシャッフル
    random.shuffle(tiles)
    # 出力
    for i in range(7):
        response += tiles[i]
    response += '\r\n'
    response += '\r\n'
    response += '以上'
    return {
        'statusCode': 200,
        'headers': {
            'Content-type': 'application/json;charset=UTF-8'
        },
        'body': response
    }
