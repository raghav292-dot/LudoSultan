import json
import time

import boto3
import Constants
import utils

client = boto3.client('stepfunctions')


def start_timer(user_id, t_name, connectionId):
    print("LobbyTTL Timer started")
    input = {"user_id": user_id, "connectionId": connectionId,
             "Comment": f"From MatchMaker to expire {user_id} LobbyTTL"}
    response = client.start_execution(
        stateMachineArn='arn:aws:states:ap-south-1:455664674507:stateMachine:LobbyTTL', name=user_id, input=json.dumps(input))

    current_timestamp = str(time.time())
    utils.update_column(user_id, t_name, 'req_timestamp', current_timestamp)
    print("step function response", response, current_timestamp)

    # step function response {'executionArn': 'arn:aws:states:ap-south-1:455664674507:express:LobbyTTL:user111:9a5f02b7-ff42-4e41-b331-957811b6f33f',
    # 'startDate': datetime.datetime(2023, 1, 2, 10, 31, 46, 573000, tzinfo=tzlocal()),
    # 'ResponseMetadata': {'RequestId': '53ac6e5a-789d-4b03-b023-532204eae399', 'HTTPStatusCode': 200,
    # 'HTTPHeaders': {'x-amzn-requestid': '53ac6e5a-789d-4b03-b023-532204eae399', 'date': 'Mon, 02 Jan 2023 10:31:46 GMT', 'content-type': 'application/x-amz-json-1.0', 'content-length': '148'},
    # 'RetryAttempts': 0}}
