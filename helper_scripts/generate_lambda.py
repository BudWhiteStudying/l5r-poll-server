import yaml
import humps
import argparse
import os
import shutil
import re
from functools import cmp_to_key

parser = argparse.ArgumentParser(description="Accepts the arguments required for generating a new Lambda Function")
parser.add_argument(
    '--name',
    dest="snake_case_name",
    type=str,
    help="snake-cased name of the new Lambda function",
    required=True
)
parser.add_argument(
    '--method',
    dest="http_method",
    type=str,
    help="HTTP method through which the function shall be exposed on the API Gateway",
    required=True
)
parser.add_argument(
    '--input',
    dest="input_file",
    type=str,
    help="path to the input YAML file, default is './template.yaml'",
    required=False
)
parser.add_argument(
    '--api',
    dest='should_create_api',
    action='store_true'
)


class Sub(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Sub'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.val)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


class GetAtt(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!GetAtt'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.val)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


class Ref(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Ref'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.val)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


function_resource_template = {
    'Type': 'AWS::Serverless::Function',
    'Properties': {
        'CodeUri': '',
        'Handler': 'app.lambda_handler',
        'Runtime': 'python3.9',
        'Architectures': ['x86_64'],
        'FunctionName': '',
        'Events': {}
    }
}

function_resource_event_template = {
    'Type': 'Api',
    'Properties': {
        'Path': '',
        'Method': ''
    }
}

api_output_template = {
    'Description': 'API Gateway endpoint URL for the Prod stage'
}

function_output_template = {
    'Description': 'Lambda Function ARN'
}

function_role_output_template = {
    'Description': 'Implicit IAM Role created for the Lambda Function'
}


def load_cf_manifest(manifest_file_path):
    with open(manifest_file_path, 'r') as f:
        cf_manifest = yaml.safe_load(f)
    return cf_manifest


def build_function_role_output(pascal_case_function_name):
    function_role_output = function_role_output_template
    function_role_output['Value'] = GetAtt('{pascal_fn_name}FunctionRole.Arn'.format(pascal_fn_name=pascal_case_function_name))
    return function_role_output


def build_function_output(pascal_case_function_name):
    function_output = function_output_template
    function_output['Value'] = GetAtt('{pascal_fn_name}Function.Arn'.format(pascal_fn_name=pascal_case_function_name))
    return function_output


def build_api_output(hyphenated_function_name_no_verb):
    api_output = api_output_template
    api_output[
        'Value'] = Sub('https://${{ServerlessRestApi}}.execute-api.${{AWS::Region}}.amazonaws.com/Prod/{snake_fn_name}/'.format(snake_fn_name=hyphenated_function_name_no_verb))
    return api_output


def build_function_resource_event(hyphenated_function_name, function_method):
    function_resource_event = function_resource_event_template
    function_resource_event['Properties']['Path'] = '/{path}'.format(path=hyphenated_function_name)
    function_resource_event['Properties']['Method'] = function_method.lower()
    return function_resource_event


def build_function_resource(snake_case_function_name, pascal_case_function_name, function_resource_event):
    function_resource = function_resource_template
    function_resource['Properties']['CodeUri'] = '{snake_fn_name}/'.format(snake_fn_name=snake_case_function_name)
    if function_resource_event is not None:
        function_resource['Properties']['Events'][pascal_case_function_name] = function_resource_event
    function_resource['Properties']['FunctionName'] = pascal_case_function_name+'Function'
    return function_resource


def add_function_to_manifest(snake_case_function_name, function_method, cf_manifest, should_create_api_flag):
    pascal_case_function_name = humps.pascalize(snake_case_function_name)
    snake_case_function_name_no_verb = '_'.join(snake_case_function_name.split('_')[1:])
    pascal_case_function_name_no_verb = humps.pascalize(snake_case_function_name_no_verb)
    hyphenated_function_name = snake_case_function_name.replace('_', '-')
    hyphenated_function_name_no_verb = snake_case_function_name_no_verb.replace('_', '-')

    function_role_output = build_function_role_output(pascal_case_function_name)
    function_output = build_function_output(pascal_case_function_name)
    api_output = None
    function_resource_event = None
    if should_create_api_flag:
        api_output = build_api_output(hyphenated_function_name_no_verb)
        function_resource_event = build_function_resource_event(hyphenated_function_name_no_verb, function_method)
    function_resource = build_function_resource(snake_case_function_name, pascal_case_function_name,
                                                function_resource_event)

    if cf_manifest['Resources'] is None:
        cf_manifest['Resources'] = {}
    if cf_manifest['Outputs'] is None:
        cf_manifest['Outputs'] = {}
    cf_manifest['Resources'][
        '{pascal_fn_name}Function'.format(pascal_fn_name=pascal_case_function_name)] = function_resource
    if '{pascal_fn_name_no_verb}Api'.format(pascal_fn_name_no_verb=pascal_case_function_name_no_verb) not in cf_manifest['Outputs'] and api_output is not None:
        cf_manifest['Outputs'][
            '{pascal_fn_name_no_verb}Api'.format(pascal_fn_name_no_verb=pascal_case_function_name_no_verb)] = api_output
    cf_manifest['Outputs'][
        '{pascal_fn_name}Function'.format(pascal_fn_name=pascal_case_function_name)] = function_output
    cf_manifest['Outputs'][
        '{pascal_fn_name}FunctionIamRole'.format(pascal_fn_name=pascal_case_function_name)] = function_role_output

    return cf_manifest


def build_sort_key(key_to_sort):
    decomposed_key = re.findall('[A-Z][^A-Z]*', key_to_sort)
    return decomposed_key[len(decomposed_key)-1]


def custom_comparator(tuple1, tuple2):
    if build_sort_key(tuple1[0]) > build_sort_key(tuple2[0]):
        return 1
    elif build_sort_key(tuple1[0]) == build_sort_key(tuple2[0]):
        if tuple1[0] > tuple2[0]:
            return 1
        else:
            return -1
    else:
        return -1


def sort_layer(layer_to_sort):
    sorted_layer = {}
    for key in layer_to_sort:
        if isinstance(layer_to_sort[key], dict):
            sorted_layer[key] = sort_layer(layer_to_sort[key])
        else:
            sorted_layer[key] = layer_to_sort[key]
    sorted_layer_items = sorted_layer.items()
    sorted_layer_returnable = sorted(sorted_layer_items, key=cmp_to_key(custom_comparator))
    dict_of_sorted_layer = dict(sorted_layer_returnable)
    return dict_of_sorted_layer
    #return dict(sorted(sorted_layer.items(), key=build_sort_key(sorted_layer).__getitem__))


def generate_function_directory(snake_case_function_name, templates_dir_path):
    if not os.path.exists(os.path.join('..', snake_case_function_name)):
        os.mkdir(os.path.join('..', snake_case_function_name))
        for root, dirs, files in os.walk(templates_dir_path):
            for file in files:
                shutil.copy(
                    os.path.join(os.path.abspath(root), file),
                    os.path.join('..', snake_case_function_name, '.'.join(file.split('.')[0:2])))
    else:
        raise Exception('Directory {dir_name} already exists!'.format(dir_name=snake_case_function_name))


if __name__ == '__main__':
    snake_case_name = parser.parse_args().snake_case_name
    http_method = parser.parse_args().http_method
    input_file = parser.parse_args().input_file
    should_create_api = parser.parse_args().should_create_api
    templates_dir = os.path.join('..', 'lambda_template')

    generate_function_directory(snake_case_name, templates_dir)
    manifest = load_cf_manifest(input_file if input_file else 'template.yaml')
    updated_manifest = add_function_to_manifest(snake_case_name, http_method, manifest, should_create_api)
    sorted_manifest = sort_layer(updated_manifest)
    #print('sorted manifest:\n\n{man}'.format(man=yaml.dump(sorted_manifest, sort_keys=False)))

    shutil.copy(input_file if input_file else 'template.yaml', 'template.yaml.bak')
    with open('../template.yaml', 'w+') as output_file:
        output_file.write(yaml.dump(sorted_manifest, sort_keys=False))
