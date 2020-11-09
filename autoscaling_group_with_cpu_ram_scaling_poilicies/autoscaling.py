#!/usr/bin/python3

from argparse import ArgumentParser
from boto3 import client
import time

parser = ArgumentParser( description = 'autoscaling script', usage = "autoscaling.py -ami_id <AMI Id> [ -region <AWS region> ]")
parser.add_argument('-ami_id', nargs = 1, type=str,  dest = "ami_id",  help = '-ami_id <AMI Id>')
parser.add_argument('-region', type = str, nargs=1, dest = "region", help = '-region <-region region name>')
args = parser.parse_args()

ami_id = args.ami_id[0]
region = args.region[0]
aws_key = 'chiju'
instance_type = 't2.micro'
launch_configuration_name = 'launch_conf_2'
autoscaling_group_name = 'autoscaling_group_2'
max_size = 4
min_size = 1
cpu_utilization_trigger_value = 60
mem_utilization_trigger_value = 60

client_availabily_zones = client('ec2', region_name = region )
client_autoscaling = client('autoscaling', region_name = region )

#creating launch configuration
launch_configuration_autoscaling = client_autoscaling.create_launch_configuration( 
                                     ImageId = ami_id,
                                     KeyName = aws_key,
                                     InstanceType = instance_type, 
                                     LaunchConfigurationName = launch_configuration_name, 
                                     InstanceMonitoring= { 'Enabled': True } )

#getting availability zones
availability_zones = [ zone[ 'ZoneName' ]  for zone in client_availabily_zones.describe_availability_zones()[ 'AvailabilityZones' ] ]

#creating auto scaling group
autoscaling_group_autoscaling = client_autoscaling.create_auto_scaling_group( 
                                  AutoScalingGroupName = autoscaling_group_name, 
                                  LaunchConfigurationName = launch_configuration_name, 
                                  MaxSize = max_size, 
                                  MinSize = min_size, 
                                  AvailabilityZones = availability_zones )

#wating for instance creation
time.sleep(60)

#Getting instance ids of autoscaling group's instances
instance_id = client_autoscaling.describe_auto_scaling_instances()['AutoScalingInstances'][0]['InstanceId']


#enabling group metrics collection
enabling_metrics_collection = client_autoscaling.enable_metrics_collection( 
                                AutoScalingGroupName = autoscaling_group_name, 
                                Granularity = '1Minute' )

#scaling policy based on cpu utilization, scale up if avg cpu utilization is more than threshhold value, for example 60%
cpu_scaling_policy = client_autoscaling.put_scaling_policy( 
                       AutoScalingGroupName = autoscaling_group_name,
                       PolicyName = 'AverageCPUUtilization',
                       PolicyType = 'TargetTrackingScaling',
                       AdjustmentType = 'PercentChangeInCapacity',
                       EstimatedInstanceWarmup = 20,
                       TargetTrackingConfiguration = { 
                         'CustomizedMetricSpecification': { 
                           'MetricName': 'CPUUtilization',
                           'Namespace': 'AWS/EC2',
                           'Dimensions': [{
                             'Name': 'AutoScalingGroupName',
                             'Value': autoscaling_group_name }],
                           'Statistic': 'Average', 
                           'Unit': 'Percent'},
                         'TargetValue': cpu_utilization_trigger_value })

#scalling policy based on memory utilization, scale up if avg memory utilization is more than threshold value for examble 60%
mem_scaling_policy = client_autoscaling.put_scaling_policy(
                       AutoScalingGroupName = autoscaling_group_name,
                       PolicyName = 'Averagememoryutilization',
                       PolicyType = 'TargetTrackingScaling',
                       AdjustmentType = 'PercentChangeInCapacity',
                       EstimatedInstanceWarmup = 20,
                       TargetTrackingConfiguration = {
                         'CustomizedMetricSpecification': {
                           'MetricName': 'mem_used_percent',
                           'Namespace': 'CWAgent',
                           'Dimensions': [
                             {'Name': 'InstanceId', 'Value': instance_id },
                             {'Name': 'AutoScalingGroupName', 'Value': autoscaling_group_name },
                             {'Name': 'ImageId', 'Value': ami_id },
                             {'Name': 'InstanceType', 'Value': instance_type }],
                           'Statistic': 'Average',
                           'Unit': 'Percent'},
                         'TargetValue': mem_utilization_trigger_value })
