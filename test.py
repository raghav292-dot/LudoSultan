import boto3
import time

def lambda_handler():
    # Create an S3 client
    # sfn = boto3.client('stepfunctions')

    # Retrieve the state of the Step Function
    # response = sfn.describe_execution(executionArn="arn:aws:states:ap-south-1:455664674507:express:LobbyTTL:100104:532f192e-726e-4383-a6c7-11a91b8f2b79")

    # Print the state of the Step Function

    # current timestamp
    current_timestamp = time.time()
    
    # some other timestamp in the past
    past_timestamp = 1674962054256
    
    # calculate the difference in seconds
    diff = current_timestamp - past_timestamp
    
    print("diff", current_timestamp, diff)

    # print(response)
