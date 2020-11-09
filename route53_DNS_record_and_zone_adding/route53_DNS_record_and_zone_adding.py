#!/usr/bin/env python3

import argparse
import csv
import boto3
import random

random_num = random.randint(1,1044441)
random_number = str(random_num)

parser = argparse.ArgumentParser(description = 'Adding DNS records in AWS route53', usage = "%(prog)s --csv_file <CSV File>")
parser.add_argument('--csv_file', nargs = 1, type=str,  dest = "csv_file",  help = 'CSV file which has the DNS records')
args = parser.parse_args()

csv_file = args.csv_file[0]
fields = []
rows = []
with open(csv_file, 'r' ) as csvfile:
  csvreader = csv.reader(csvfile)
  fields = next(csvreader)
  for row in csvreader:
    rows.append(row)

# For getting currently present hosted zones
present_zones = {}
client = boto3.client('route53')
response_list = client.list_hosted_zones()
for hosted_zone in response_list['HostedZones']:
  present_zones[hosted_zone['Name']] = hosted_zone['Id']


# Function for getting domain name from the "name" section of the record
def split(strng, sep, pos):
  strng = strng.split(sep)
  return sep.join(strng[pos:])

#Looping through the rows in CSV file
for rw in rows:
  typ = rw[0]
  name = rw[1]
  value = rw[2]
  ttl = int(rw[3])
  domain = split(rw[1], '.', -2) + '.'
  
  #adding hosted zone if it is not already there
  if domain not in present_zones.keys():        
    response_create_zone = client.create_hosted_zone( Name = domain, CallerReference = random_number)
    
    #when there is no hosted zones, need to handle the IndexError
    try:
        zone_id = client.list_hosted_zones_by_name( DNSName = domain, MaxItems='1')['HostedZones'][0]['Id']
    except IndexError as e:
        print(e)
    present_zones[domain] =  zone_id
    print(zone_id)

  # To get zone_id of of the hosted zone
  zone_id = client.list_hosted_zones_by_name( DNSName = domain, MaxItems='1')['HostedZones'][0]['Id']
  zone_id = zone_id.split('/')[2]
  
  # Adding double quotes '"' in the value if the record type is TXT
  if rw[0].upper() == 'TXT':
    value = '"' + value + '"'

  # Adding priority in the value section if the record type is MX
  if rw[0].upper() == 'MX':
    priority = rw[4]
    value = priority + ' ' + value

  # Adding DNS record
  try:
    client.change_resource_record_sets(
                                        HostedZoneId = zone_id,
                                        ChangeBatch={
                                          'Changes': [{ 
                                            'Action': 'CREATE',
                                            'ResourceRecordSet': {
                                              'Name': name,
                                              'Type': typ, 
                                              'TTL': ttl, 
                                              'ResourceRecords': [{
                                                'Value': value}]} }]})
    print("1)added", " ", typ, name, value, "\n")
  
  # Exception handling for InvalidChangeBatch and InvalidInput Errors
  except ( client.exceptions.InvalidChangeBatch, client.exceptions.InvalidInput ) as e:
    print(e)
    
    # If there is already DNS record with the same name and if we want to add value to the values section
    try:
        
      # To get current values of the DNS record
      current_values = client.list_resource_record_sets(
                              HostedZoneId = zone_id,
                              StartRecordName = name,
                              StartRecordType = typ,
                              MaxItems = '1')['ResourceRecordSets'][0]['ResourceRecords']
      record_values = []
      for i in current_values:
        record_values.append(i['Value'])
      
      # To add the value to the values if the value is not present in the values
      if value not in record_values:
        current_values.append({'Value':value})
        client.change_resource_record_sets(
                                    HostedZoneId = zone_id,
                                    ChangeBatch={
                                        'Changes': [{ 
                                            'Action': 'UPSERT',
                                            'ResourceRecordSet': {
                                                'Name': name,
                                                'Type': typ, 
                                                'TTL': ttl, 
                                                'ResourceRecords': current_values }}]})
        print("2)added", " ", typ, name, current_values, "\n")                                                                          

    # For ANMAE record, handling InvalidInput error
    except client.exceptions.InvalidInput as e:
      print(e, "3")
      print("3)PASSING", typ, name + "\n")
      pass