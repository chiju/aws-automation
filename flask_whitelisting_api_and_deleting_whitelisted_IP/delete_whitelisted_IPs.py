#!/usr/bin/python3

import boto3
import datetime

#variables
#please change the security_group variable to correct one
now = datetime.datetime.now() 
date = "{}-{}-{}".format(now.day, now.month, now.year)
ip_list_for_deleting = []
port = 5001
security_group = 'sg-0ad9a3b8192e888e9'

ec2 = boto3.resource('ec2')
security_group = ec2.SecurityGroup(security_group)

#getting rules which has date as discription in the security group rule
for rule in security_group.ip_permissions:
  for ip_range in rule['IpRanges']:
    try:
      if ip_range['Description'] == date:
        ip_list_for_deleting.append(ip_range['CidrIp'])
    except KeyError:
      pass


#deleting the rules
for ip in ip_list_for_deleting:
  print(ip)
  security_group.revoke_ingress(
                                 CidrIp = ip,
                                 FromPort = port,
                                 ToPort = port,
                                 IpProtocol = 'tcp')

