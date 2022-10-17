import subprocess
import argparse
import json
import sys

DEFAULT_REGION = 'eu-south-1'
DEFAULT_STACK_NAME = 'l5r-poll-cf-stack'

parser = argparse.ArgumentParser(
    description="Accepts the arguments required for deploying the application to the AWS cloud")
parser.add_argument(
    '--bucket',
    dest="bucket_name",
    type=str,
    help="Name of the AWS S3 bucket that CloudFormation will use in order to upload the artifacts to AWS",
    required=True
)
parser.add_argument(
    '--region',
    dest="region",
    type=str,
    help="AWS region where to deploy the application to, default is '{DEFAULT_REGION}'".format(
        DEFAULT_REGION=DEFAULT_REGION),
    required=False,
    default=DEFAULT_REGION
)
parser.add_argument(
    '--stack-name',
    dest="stack_name",
    type=str,
    help="Name of the CloudFormation stack to deploy to, default is '{DEFAULT_STACK_NAME}'".format(
        DEFAULT_STACK_NAME=DEFAULT_STACK_NAME),
    required=False,
    default=DEFAULT_STACK_NAME
)


def prepare_package_command(bucket_name, deployment_region):
    package_command = ['sam', 'package', '--output-template-file', 'packaged.yaml', '--s3-bucket', '{bucket_name}',
                       '--region', '{deployment_region}']
    package_command = [c.replace('{bucket_name}', support_bucket_name) for c in package_command]
    package_command = [c.replace('{deployment_region}', region) for c in package_command]

    return package_command


def prepare_deploy_command(deployment_region_value, target_stack_name_value):
    deploy_command = ['aws', 'cloudformation', 'deploy', '--region', '{deployment_region}', '--template-file',
                      'packaged.yaml', '--stack-name', '{target_stack_name}', '--capabilities', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
    deploy_command = [c.replace('{deployment_region}', deployment_region_value) for c in deploy_command]
    deploy_command = [c.replace('{target_stack_name}', target_stack_name_value) for c in deploy_command]

    return deploy_command


if __name__ == '__main__':

    support_bucket_name = parser.parse_args().bucket_name  # you actually need to create it on AWS S3
    region = parser.parse_args().region
    stack_name = parser.parse_args().stack_name

    CREDENTIALS_CHECK_COMMAND = ['aws', 'sts', 'get-caller-identity']
    BUILD_COMMAND = ['sam', 'build', '-p']
    PACKAGE_COMMAND = prepare_package_command(support_bucket_name, region)
    DEPLOY_COMMAND = prepare_deploy_command(region, stack_name)

    # Execute credentials check
    credentials_check_result = subprocess.run(CREDENTIALS_CHECK_COMMAND, capture_output=True)
    if credentials_check_result.returncode == 0:
        print('Executing operations with account {account_id}'.format(
            account_id=json.loads(credentials_check_result.stdout.decode())['Account']))
    else:
        raise Exception('Not logged in to the AWS CLI, aborting')

    # Execute build, package, deploy
    for command in [BUILD_COMMAND, PACKAGE_COMMAND, DEPLOY_COMMAND]:
        print('Executing \'{command}\''.format(command=' '.join(command)))
        try:
            command_return_data = subprocess.run(command, capture_output=True)
            if command_return_data.returncode == 0:
                print('Done')
            else:
                raise Exception('Command {cmd} returned {rc} code: {data}'.format(
                    cmd=' '.join(command),
                    rc=command_return_data.returncode,
                    data=command_return_data.stdout.decode()
                ))
        except Exception as e:
            sys.exit('Problems executing build & deploy commands: {error}'.format(error=repr(e)))
