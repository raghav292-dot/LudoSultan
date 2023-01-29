import json


def lambda_handler(event, context):
    connectionId = event['requestContext']['connectionId']
    print("connected from ", connectionId)
    return {}
