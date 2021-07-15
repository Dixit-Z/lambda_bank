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
TAG_DAY_OF_SCHEDULE = 'schedule-on'

# Set to half the run frequency of the lambda (i.e. Lambda runs every 10 minutes, set frequency to 5)
CHECK_FREQUENCY = 10
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

        stopped_filter = {'Name':'instance-state-name', 'Values':['stopped']}
        instances = ec2_resource.instances.filter(Filters=[stopped_filter])

        if not instances :
            continue

        for instance in instances:

            if instance.tags is None :
                continue

            for tag in instance.tags:

                if tag['Key'].lower() == TAG_DAY_OF_SCHEDULE and not isScheduleOn(tag,current_day) :
                    continue

                if tag['Key'].lower().startswith(TAG_SCHEDULE) :
                    diff = getMinutesDifference(tag['Value'], current_time)
                    if diff < 0 or diff > CHECK_FREQUENCY :
                        continue
                    else :
                        instance.start()

def getMinutesDifference(target_time, present_time):
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