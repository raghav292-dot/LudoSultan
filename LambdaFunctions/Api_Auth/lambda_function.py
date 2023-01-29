import json
import os


def lambda_handler(event, context):
    print(event)
    if event['headers']['authorization'] == os.environ['api_auth_key']:
        response = {
            "isAuthorized": True,
            "content": {
                "key": "value"
            }
        }
    else:
        response = {
            "isAuthorized": False,
            "content": {
                "key": "value"
            }
        }
    return response
