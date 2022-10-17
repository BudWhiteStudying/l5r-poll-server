import boto3
import traceback
import os
from data_model import PollConfigKey
from shared_utils import get_item, build_success_response, build_failure_response


boto3_client = boto3.client('dynamodb')
table_name = 'Poll_Config'


def lambda_handler(event, context):
    try:
        session_name = get_item(
            boto3_client,
            table_name,
            PollConfigKey(rule_id='CURRENT_SESSION_NAME')
        )['value']
        session_title = get_item(
            boto3_client,
            table_name,
            PollConfigKey(rule_id='CURRENT_SESSION_TITLE')
        )['value']
        poll_submit_url = get_item(
            boto3_client,
            table_name,
            PollConfigKey(rule_id='POLL_SUBMIT_URL')
        )['value']

        return build_success_response({
            'session_name': session_name,
            'session_title': session_title,
            'poll_submit_url': poll_submit_url
        }, os.environ.get('AllowedCorsDomain'))
    except Exception as e:
        tb = traceback.format_exc()
        print('we failed: {error}\n{trace}'.format(error=repr(e), trace=repr(tb)))
        return build_failure_response(repr(tb))

