import boto3
import traceback
import json
import os
from data_model import PollResponse
from shared_utils import put_item, build_success_response, build_failure_response


boto3_client = boto3.client('dynamodb')
table_name = 'Poll_Response'


def lambda_handler(event, context):
    request_body = json.loads(event['body'])
    try:
        source_ip = None
        try:
            source_ips = event['headers']['X-Forwarded-For'].split(",")
            source_ip = source_ips[0]
        except Exception as e:
            print("Could not extract source IP")

        poll_response = PollResponse(source_ip, request_body['sessionName'], request_body['whatWentWell'], request_body['whatWentWrong'])
        print('about to persist\n{obj}'.format(obj=poll_response))
        operation_outcome = put_item(
            boto3_client,
            table_name,
            poll_response
        )

        return build_success_response(operation_outcome, os.environ.get('AllowedCorsDomain'))
    except Exception as e:
        tb = traceback.format_exc()
        print('we failed: {error}\n{trace}'.format(error=repr(e), trace=repr(tb)))
        return build_failure_response(repr(tb))

