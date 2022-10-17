import boto3
import traceback
import json
from data_model import PollConfig
from shared_utils import put_item, build_success_response, build_failure_response


boto3_client = boto3.client('dynamodb')
table_name = 'Poll_Config'


def lambda_handler(event, context):
    request_body = json.loads(event['body'])
    try:
        current_session_name = PollConfig('CURRENT_SESSION_NAME', request_body['sessionName'])
        current_session_title = PollConfig('CURRENT_SESSION_TITLE', request_body['sessionTitle'])
        poll_submit_url = PollConfig('POLL_SUBMIT_URL', request_body['pollSubmitUrl']) if 'pollSubmitUrl' in request_body else None

        for item in current_session_name, current_session_title, poll_submit_url:
            if item is not None:
                print('about to persist\n{obj}'.format(obj=item))
                put_item(
                    boto3_client,
                    table_name,
                    item
                )

        return build_success_response(None, '*')
    except Exception as e:
        tb = traceback.format_exc()
        print('we failed: {error}\n{trace}'.format(error=repr(e), trace=repr(tb)))
        return build_failure_response(repr(tb))

