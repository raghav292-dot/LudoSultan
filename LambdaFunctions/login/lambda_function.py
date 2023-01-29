import json

import Constants
import requests

ip = '172.31.7.200'


def send_request(payload):
    headers = {
        'accept': 'text/plain',
        'Content-Type': 'application/json'
    }
    api_endpoint = f"http://{ip}:5000/api/rpc"
    response = requests.request(
        "POST", api_endpoint, headers=headers, data=payload, verify=False)
    return response.text


def prepare_payload(method, inp_payload):
    if method == 'statelist':
        return {
            "method": method
        }
    elif method == 'ShopPlanList':
        return {
            "method": method
        }

    return {
        "method": method,
        "requestData": inp_payload
    }


def lambda_handler(event, context):
    inp_payload = None
    if 'body' in event:
        inp_payload = json.loads(event['body'])

    method = Constants.method_mapping[event['requestContext']['http']['path'].split(
        '/')[1]]
    print(inp_payload, event, method)
    payload = json.dumps(prepare_payload(method, inp_payload))
    print('request payload', payload)

    response = send_request(payload)
    print('response', response)

    return {
        'statusCode': 200,
        'body': response
    }
