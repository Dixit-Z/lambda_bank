'''
Auto-Start :
Start stopped EC2 based on hours defined in Auto-start* tags

i.e.
List of tags :
Auto-start : 08:00
Auto-start : 14:00
'''

from datetime import datetime
import dateutil.tz
import boto3

FMT='%H:%M'
TAG_SCHEDULE  = 'auto-start'
# Set to half the run frequency of the lambda (i.e. Lambda runs every 10 minutes, set frequency to 5)
CHECK_FREQUENCY = 10

def lambda_handler(event, context):
    # Set to empty to check all regions
    ec2_regions = ['eu-west-1']

    now = datetime.now(tz=dateutil.tz.gettz('Europe/Paris'))
    current_time = '{:02d}:{:02d}'.format(now.hour, now.minute)

    if not ec2_regions:
        ec2_regions = [r['RegionName'] for r in boto3.client('ec2').describe_regions()['Regions']]

    for region in ec2_regions:

        ec2_resource = boto3.resource('ec2', region_name = region)

        stopped_filter = {'Name':'instance-state-name', 'Values':['stopped']}
        instances = ec2_resource.instances.filter(Filters=[stopped_filter])

        if not instances :
            continue

        for instance in instances:

            if instance.tags is None:
                continue

            for tag in instance.tags:

                if tag['Key'].lower().startswith(TAG_SCHEDULE) :
                    diff = timeDifference(tag['Value'], current_time)
                    if diff < 0 or diff > CHECK_FREQUENCY :
                        continue
                    else :
                        instance.start()

def timeDifference(then, now):
    diff = datetime.strptime(now,FMT) - datetime.strptime(then,FMT)
    if diff.total_seconds() < 0 :
        return -1

    return (diff.total_seconds()//60)%60