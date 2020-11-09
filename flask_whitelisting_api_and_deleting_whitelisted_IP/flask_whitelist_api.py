
from flask import Flask, request
import boto3
import datetime

#variables
now = datetime.datetime.now() 
date = "{}-{}-{}".format(now.day, now.month, now.year)
app = Flask(__name__)


#whitelisting function
def whitelist(ip):
  security_group = 'sg-0ad9a3b8192e888e9'
  ip_address = ip + '/32'
  description = date
  port_number = 5001
  protocol = 'tcp'

  ec2 = boto3.resource('ec2')
  security_group = ec2.SecurityGroup(security_group)
  security_group.authorize_ingress(
                                 IpPermissions = [{
                                   'IpProtocol': protocol,
                                   'FromPort': port_number,
                                   'ToPort':  port_number,
                                   'IpRanges': [{
                                      'CidrIp': ip_address,
                                      'Description': description }]}])
 
#flask app                                  
@app.route('/')
def hello_world():
  whitelist(request.remote_addr)
  return request.remote_addr