import json

import boto3

client = boto3.client('stepfunctions')


def start_timer(user_id, connectionId):
    print("GamePlayTTL Timer started")
    input = {"user_id": user_id, "connectionId": connectionId,
             "Comment": f"From MatchMaker to expire {user_id} GamePlayTTL"}

    response = client.start_execution(
        stateMachineArn='arn:aws:states:ap-south-1:455664674507:stateMachine:GamePlayTTL',
        name=user_id,
        input=json.dumps(input)
    )

    # reduce heartbeat on every turn expiry only if statebit is 1.
