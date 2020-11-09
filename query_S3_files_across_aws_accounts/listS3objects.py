# For getting S3 files which has a perticuler name format and which are created in last 24 hours 
# across multiple aws accounts

import boto3
import re
from datetime import datetime, timedelta

# Time before 24 hours
time_before_twentyfour_hours = datetime.now() - timedelta(hours=24)

# To get all the aws profiles
profiles = boto3.Session().available_profiles

# File name pattern to compare
filename_pattern = '(.*)-([0-9]*)-(.*).gz'

# Looping through profiles
for profile in profiles:
  session = boto3.Session(profile_name=profile)
  s3_client = session.client('s3')
  resp = s3_client.list_buckets()
  for bucket in resp['Buckets']:
    try:
      for key in s3_client.list_objects(Bucket=bucket['Name'])['Contents']:
        file_date = key['LastModified'].replace(tzinfo=None)
        if ( re.match(filename_pattern, key['Key']) and file_date > time_before_twentyfour_hours ):
          print("Bucket name: {}, File name: {}, Time: {}".format(bucket['Name'], key['Key'], file_date))
    except KeyError:
      pass