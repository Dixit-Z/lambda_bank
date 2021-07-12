'''
Ephemeral ec2 killer :
Stop or terminate instance after a tag based duration value
Tag Names (in priority order):
- Stop-After: Terminate instance
- Terminate-After: Stop instance

Tag Value: Indicates running duration (eg '30m', '1.5h', '24h')
Schedule this Lambda function to run at regular intervals (ie every 5 minutes)
'''

import boto3
from datetime import datetime, timedelta

TAG_STOP      = 'stop-after'
TAG_TERMINATE = 'terminate-after'

def lambda_handler(event, context):

    ec2_regions = ['eu-west-1']

    if not ec2_regions:
        ec2_regions = [r['RegionName'] for r in boto3.client('ec2').describe_regions()['Regions']]

    for region in ec2_regions:
        ec2_resource = boto3.resource('ec2', region_name = region)
        
        running_filter = {'Name':'instance-state-name', 'Values':['running']}
        instances = ec2_resource.instances.filter(Filters=[running_filter])
        
        for instance in instances:

            if instance.tags == None:
                continue

            if value := [tag['Value'] for tag in instance.tags if tag['Key'] == TAG_STOP]:
                if check_duration(value[0], instance.launch_time):
                    print(f'Stopping instance {instance.id}')
                    instance.stop()

            elif value := [tag['Value'] for tag in instance.tags if tag['Key'] == TAG_TERMINATE]:
                if check_duration(value[0], instance.launch_time):
                    print(f'Terminating instance {instance.id}')
                    instance.terminate()

def check_duration(duration_string, launch_time):
    
    # Extract duration to wait
    try:
        if duration_string[-1] == 'm':
            minutes = int(duration_string[:-1])
        elif duration_string[-1] == 'h':
            minutes = int(float(duration_string[:-1]) * 60)
        else:
            print(f'Invalid duration of "{duration_string}" for instance {instance.id}')
            return False
    except:
        print(f'Invalid duration of "{duration_string}" for instance {instance.id}')
        return False
    
    # Check whether required duration has elapsed
    return datetime.now().astimezone() > launch_time + timedelta(minutes=minutes)
