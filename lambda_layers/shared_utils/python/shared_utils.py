import json
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()
deserializer = TypeDeserializer()


def serialize(item):
    serialized_item = serializer.serialize(vars(item))

    return item if 'M' not in serialized_item else serialized_item['M']


def deserialize(dynamodb_json_string):
    return deserializer.deserialize({'M': dynamodb_json_string})


def get_item(dynamodb_client, table_name, key):
    return_data = dynamodb_client.get_item(
        TableName=table_name,
        Key=serialize(key)
    )
    return deserialize(return_data['Item']) if 'Item' in return_data else None


def put_item(dynamodb_client, table_name, item):
    return_data = dynamodb_client.put_item(
        TableName=table_name,
        Item=serialize(item)
    )
    return return_data


def delete_item(dynamodb_client, table_name, key):
    return_data = dynamodb_client.delete_item(
        TableName=table_name,
        Key=serialize(key)
    )
    return return_data


def get_items(dynamodb_client, table_name):
    return_data = dynamodb_client.scan(
        TableName=table_name
    )
    return deserialize(return_data['Items']) if 'Items' in return_data else None


def scan(dynamodb_client, table_name, scan_filter, max_results_count=1):
    return_data = dynamodb_client.scan(
        TableName=table_name,
        ScanFilter=scan_filter
    )
    return deserialize(return_data['Items'][min(max_results_count, max(len(return_data['Items'])-1, 0))]) \
        if 'Items' in return_data and len(return_data['Items']) > 0 \
        else None


def parse_invocation_result(invocation_data):
    if 'Payload' in invocation_data:
        payload = json.load(invocation_data['Payload'])
        print('Lambda returned {data}'.format(data=payload))
        return_code = payload['statusCode']
        if return_code == 200:
            return json.loads(payload['body'])['data']
        else:
            raise Exception(json.loads(payload['body'])['message'])
    else:
        raise Exception('Lambda returned a malformed response: {response}'.format(
            response=repr(invocation_data)
        ))


def invoke_lambda_function(client, function_name, payload):
    return_data = client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=payload
    )
    return parse_invocation_result(return_data)


def build_success_response(success_data, allowed_cors_domain):
    headers = {"Content-Type": "application/json"}
    if allowed_cors_domain is not None:
        allowed_cors_domain = allowed_cors_domain.replace('\'', '')
        print('allowed_cors_domain is {allowed_cors_domain}'.format(allowed_cors_domain=allowed_cors_domain))
        headers['Access-Control-Allow-Origin'] = allowed_cors_domain
        headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({
            "message": "Operation executed successfully",
            "data": success_data
        })
    }


def build_failure_response(failure_data):
    return {
        "statusCode": 500,
        "body": json.dumps({
            "message": "Problems executing the operation",
            "headers": {"Content-Type": "application/json"},
            "data": failure_data
        })
    }
