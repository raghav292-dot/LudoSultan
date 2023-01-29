import json

import boto3

dynamodb = boto3.client('dynamodb')
db = boto3.resource('dynamodb')


def update_column(connection, column, val):
    table = db.Table('PlayersMetadata')
    resp = table.update_item(
        Key={'connectionId': connection},
        UpdateExpression=f"SET {column}=:s",
        ExpressionAttributeValues={':s': val}
    )


def Delete_metadata(key):
    dynamodb.delete_item(
        TableName='PlayersMetadata',
        Key={
            'connectionId': {'S': key}
        }
    )


def Delete_match(match_table, uid):
    dynamodb.delete_item(
        TableName=match_table,
        Key={
            'user_id': {'S': uid}
        }
    )


def _is_uid_exist(table_name: str, uid) -> bool:
    try:
        res = dynamodb.get_item(
            TableName=table_name,
            Key={'user_id': {'S': uid}}
        )
    except:
        return False
    if 'Item' in res:
        return True
    return False


def Update_Availability_Status_on_abnormal_disconnect(key: str, disconnectReason: str):
    # Erasing Metadata
    res = ''
    try:
        res = dynamodb.get_item(
            TableName='PlayersMetadata',
            Key={'connectionId': {'S': key}
                 }
        )
        Delete_metadata(key)
    except:
        print("something went wrong in Update_Availability_Status(Abnormal) in Disconnect")

    # Updating Availability Status in Lobby/Match
    if 'Item' in res:
        uid = res['Item']['user_id']['S']
        match_table = res['Item']['match_type']['S']
        if _is_uid_exist(match_table, uid):
            table = db.Table(match_table)
            resp = table.update_item(
                Key={'user_id': uid},
                UpdateExpression=f"SET Availability=:s",
                ExpressionAttributeValues={':s': 'Offline'}
            )
            print("Updating status in match")
        if _is_uid_exist('Lobby', uid):
            table = db.Table('Lobby')
            column = 'Availability'
            val = 'Offline'
            resp = table.update_item(
                Key={'user_id': uid},
                UpdateExpression=f"SET {column}=:s",
                ExpressionAttributeValues={':s': val}
            )
            print("Updating status in Lobby")


def End_game_on_normal_disconnect(key: str, disconnectReason: str):
    # Game-End scenario: Erasing Metadata and match
    res = ''
    try:
        res = dynamodb.get_item(
            TableName='PlayersMetadata',
            Key={'connectionId': {'S': key}
                 }
        )
        Delete_metadata(key)
    except:
        print("something went wrong in End_game_on_normal_disconnect(playermetadata) in Disconnect")

    if 'Item' in res:
        uid = res['Item']['user_id']['S']
        match_table = res['Item']['match_type']['S']
        if _is_uid_exist(match_table, uid):
            Delete_match(match_table, uid)
        else:
            print(
                f"uid does not exists in {match_table} End_game_on_normal_disconnect(match-table) in Disconnect")


def lambda_handler(event, context):
    print(event, context)
    connectionId = event['requestContext']['connectionId']
    disconnectStatusCode = event['requestContext']['disconnectStatusCode']
    disconnectReason = event['requestContext']['disconnectReason']
    if int(disconnectStatusCode) == 1006:
        # update Availability status of the connection
        print("inside abnormal disconnect")
        Update_Availability_Status_on_abnormal_disconnect(
            connectionId, disconnectReason)
    elif int(disconnectStatusCode) == 1000:
        # Erase entry from online match_table
        # To-do: Check the End-Game flag before Remove the user from Game
        print("inside normal disconnect")
        End_game_on_normal_disconnect(connectionId, disconnectReason)

    return {}
