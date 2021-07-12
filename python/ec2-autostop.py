'''
Auto-Stop :
Stop EC2 based on hours defined in Auto-stop* tags

By default, EC2 running without any tags are ignored and default Auto-stop-action is 'stop'.

Add an 'Auto-stop-action' to change the action to execute on the EC2 :
- 'Terminate' to terminate the instance (test, poc, etc..)
- 'Skip' to skip this instance (can be set temporarily on an instance supposed to shutdown on schedule)
'''

from datetime import datetime
import boto3

FMT='%H:%M'
TAG_SCHEDULE  = 'auto-stop'
TAG_STOP      = 'stop'
TAG_TERMINATE = 'terminate'
# Set to half the run frequency of the lambda (i.e. Lambda runs every 10 minutes, set frequency to 5)
CHECK_FREQUENCY = 5

def lambda_handler(event, context):
    # Set to empty to check all regions
    ec2_regions = ['eu-west-1']

    if not ec2_regions:
        ec2_regions = [r['RegionName'] for r in boto3.client('ec2').describe_regions()['Regions']]

    for region in ec2_regions:

        ec2_resource = boto3.resource('ec2', region_name = region)

        running_filter = {'Name':'instance-state-name', 'Values':['running']}
        instances = ec2_resource.instances.filter(Filters=[running_filter])

        for instance in instances:

            if instance.tags == None:
                print(f'Nothing to do for {instance.id}')
                continue

            tag_action = 'stop' # Default action
            uptime = datetime.now()

            for tag in instance.tags:

              if tag['Key'].lower().startswith(TAG_SCHEDULE) :
                diff = timeDifference(value[0], datetime.now)
                if diff < 0 or diff > CHECK_FREQUENCY:
                    continue

                if tag['Key'].lower() == 'auto-stop-action' :
                    action = tag['Value'].lower()

                if tag_action == TAG_STOP :
                    print(f'Stopping instance {instance.id}')
                    instance.stop()

                elif tag_action == TAG_TERMINATE :
                    print(f'Terminating instance {instance.id}')
                    instance.terminate()

def timeDifference(then, now):
    diff = datetime.strptime(now,FMT) - datetime.strptime(then,FMT)
    return diff
