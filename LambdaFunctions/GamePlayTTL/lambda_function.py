import json

import boto3

dynamodb = boto3.client('dynamodb')
db = boto3.resource('dynamodb')

url = 'dnipb2guye.execute-api.ap-south-1.amazonaws.com/LudoSultanProduction'

ws_client = boto3.client('apigatewaymanagementapi',
                         endpoint_url="https://" + url)


def send_msg_to_players(connectionIds: list, message):
    for connectionId in connectionIds:
        ws_client.post_to_connection(
            Data=json.dumps(message).encode('utf-8'),
            ConnectionId=connectionId
        )


def Delete_from_Lobby(uid):
    dynamodb.delete_item(
        TableName='Lobby',
        Key={
            'user_id': {'S': uid}
        }
    )


def Delete_from_metadata(conn):
    dynamodb.delete_item(
        TableName='PlayersMetadata',
        Key={
            'connectionId': {'S': conn}
        }
    )


def _is_uid_exist(table_name: str, uid):
    try:
        res = dynamodb.get_item(
            TableName=table_name,
            Key={'user_id': {'S': uid}}
        )
    except:
        return False
    if 'Item' in res:
        print(res)
        return True, res['Item']['connectionId']['S']
    return False, 'NA'


def lambda_handler(event, context):
    # try:
    #     status, conn = _is_uid_exist('Lobby', event['uid'])
    #     if status:
    #         message = {'status': False, 'msg': 'No Match found.. Please try again'}
    #         send_msg_to_players([conn], message)
    #         Delete_from_Lobby(event['uid'])
    #         Delete_from_metadata(conn)
    #     res = True
    # except:
    #     res = False
    return {
        'statusCode': 200,
        'body': json.dumps({"status": True, 'uid': 'test'})
    }
