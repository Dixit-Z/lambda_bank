'''
Auto-Stop :
Stop EC2 based on hours defined in Auto-stop* tags

By default, EC2 running without any tags are ignored and default Auto-stop-action is 'stop'.

Add an 'Auto-stop-action' to change the action to execute on the EC2 :
- 'Terminate' to terminate the instance (test, poc, etc..)
- 'Skip' to skip this instance (can be set temporarily on an instance supposed to shutdown on schedule)
'''

from datetime import datetime
import dateutil.tz
import boto3

FMT='%H:%M'
TAG_SCHEDULE  = 'auto-stop'
TAG_STOP      = 'stop'
TAG_TERMINATE = 'terminate'
TAG_DAY_OF_SCHEDULE = 'schedule-on'
# Set to half the run frequency of the lambda (i.e. Lambda runs every 10 minutes, set frequency to 5)
CHECK_FREQUENCY = 5
WEEKDAYS = { 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}



def lambda_handler(event, context):
    # Set to empty to check all regions
    ec2_regions = ['eu-west-1']
    now = datetime.now(tz=dateutil.tz.gettz('Europe/Paris'))
    current_time = '{:02d}:{:02d}'.format(now.hour, now.minute)
    current_day = now.weekday();

    if not ec2_regions:
        ec2_regions = [r['RegionName'] for r in boto3.client('ec2').describe_regions()['Regions']]

    for region in ec2_regions:

        ec2_resource = boto3.resource('ec2', region_name = region)

        running_filter = {'Name':'instance-state-name', 'Values':['running']}
        instances = ec2_resource.instances.filter(Filters=[running_filter])

        for instance in instances:

            if instance.tags is None:
                continue

            tag_action = 'stop' # Default action

            for tag in instance.tags:

                if tag['Key'].lower() == TAG_DAY_OF_SCHEDULE and not isScheduleOn(tag,current_day) :
                    continue

                if tag['Key'].lower().startswith(TAG_SCHEDULE) :
                    diff = timeDifference(tag['Value'], current_time)
                    if diff < 0 or diff > CHECK_FREQUENCY:
                        continue

                    if tag['Key'].lower() == 'auto-stop-action' :
                        tag_action = tag['Value'].lower()

                    if tag_action == TAG_STOP :
                        print(f'Stopping instance {instance.id}')
                        instance.stop()

                    elif tag_action == TAG_TERMINATE :
                        print(f'Terminating instance {instance.id}')
                        instance.terminate()

def timeDifference(target_time, present_time):
    diff = datetime.strptime(present_time,FMT) - datetime.strptime(target_time,FMT)
    if diff.total_seconds() < 0 :
        return -1

    return diff.total_seconds()//60

def isScheduleOn(tag, current_day) :
    tag_value = tag['Value'].lower()
    if tag_value == 'weekdays' and current_day > 4 :
        return False
    elif tag_value == 'weekend' and 0 <= current_day < 5 :
        return False
    else :
        for split_value in tag_value.split(",") :
            if split_value.find('-') == -1 :
                if WEEKDAYS[split_value] and WEEKDAYS[split_value] == current_day :
                    return True
            else :
                range = split_value.split('-')
                d1 = range[0]
                d2 = range[1]
                if d1 > d2 :
                    return current_day >= WEEKDAYS[d1] or current_day <= WEEKDAYS[d2]
                else :
                    return WEEKDAYS[d1] <= current_day <= WEEKDAYS[d2]