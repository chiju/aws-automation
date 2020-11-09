#URL: http:/IP:5000/data
#For sample request
#curl --header "Content-Type: application/json" --request POST --data '{ "domain_name":"xyz.com", "email_id":"xyz@xyz.com", "dns_provider":"cloudflare", "cloudflare_email_id":"xyz@uvw.com",  "cloudflare_token":"763475433597547383d7djd80hdfkhdsf"}' https://7d7djf83e.execute-api.ap-south-1.amazonaws.com/dev

import os
from flask import Flask, request, jsonify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
import OpenSSL
import hashlib
from time import sleep
import CloudFlare
import route53
import boto3
from acme import challenges
from acme import client
from acme import crypto_util
from acme import messages
import josepy as jose


# Account key size
ACC_KEY_BITS = 2048

# ACME server
DIRECTORY_URL = 'https://acme-v02.api.letsencrypt.org/directory'
#DIRECTORY_URL = 'http://acme-staging-v02.api.letsencrypt.org/directory'
USER_AGENT = 'python-acme-example'

# Certificate private key size
CERT_PKEY_BITS = 2048


# CSR Creation
def new_csr_comp(domain_name, pkey_pem=None):
  """Create certificate signing request."""
  if pkey_pem is None:
    pkey = OpenSSL.crypto.PKey()
    pkey.generate_key(OpenSSL.crypto.TYPE_RSA, CERT_PKEY_BITS)
    pkey_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM,
	                                              pkey)
  csr_pem = crypto_util.make_csr(pkey_pem, [domain_name])
  return pkey_pem, csr_pem


# DNS challenge selection from the 3 chalalnge options 
def select_dns01_chall(orderr):
  """Extract authorization resource from within order resource."""
  # Authorization Resource: authz.
  # This object holds the offered challenges by the server and their status.
  authz_list = orderr.authorizations
  for authz in authz_list:
  # Choosing challenge.
  # authz.body.challenges is a set of ChallengeBody objects.
    for i in authz.body.challenges:
      # Find the supported challenge.
      if isinstance(i.chall, challenges.DNS01):
      	return i

  raise Exception('DNS-01 challenge was not offered by the CA server.')

#Function for TXT record
def txt_record(DOMAIN, validation):
  TXT_record = '_acme-challenge.' + DOMAIN + ' IN TXT ' + validation
  return TXT_record

# If the dns_provider is Cloudflare, adding TXT record in the DNS zone
def cloudflare_dns(cloudflare_email_id, DOMAIN, cloudflare_token, validation):
  name = '_acme-challenge.' + DOMAIN
  
  
  cf = CloudFlare.CloudFlare( email = cloudflare_email_id, token=cloudflare_token)  
  dns_record = { 'name':name, 'type':'TXT', 'content':validation, 'ttl':120}
  zone_id = cf.zones.get(params={'name': DOMAIN})[0]['id']
  dns_records = []

  for record in cf.zones.dns_records.get(zone_id):
    dns_records.append(record['name'])
  if name in dns_records:
    for record in cf.zones.dns_records.get(zone_id):
      if record['name'] == name:
        cf.zones.dns_records.delete(zone_id, record['id'])
        cf.zones.dns_records.post(zone_id, data=dns_record)
  else:
    cf.zones.dns_records.post(zone_id, data=dns_record)	

# If the dns provider is aws route53, adding TXT record in the DNS zone
def aws_dns(DOMAIN, aws_access_key_id, aws_secret_access_key, validation  ):

  DOMAIN = DOMAIN + '.'
  txt_name = '_acme-challenge.' + DOMAIN 
  txt_value = '"' + validation + '"'
  conn = route53.connect( aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key)
  for zone in conn.list_hosted_zones():
    if zone.name == DOMAIN:
      zone_id = zone.id
  records = []
  for record_set in zone.record_sets:
      records.append(record_set.name)
  if txt_name in records: 
    for record_set in zone.record_sets:
      if txt_name == record_set.name:
        record_set.delete()
        zone = conn.get_hosted_zone_by_id(zone_id)
        zone.create_txt_record(name = txt_name, values=[txt_value], ttl=60)
  else:
    zone = conn.get_hosted_zone_by_id(zone_id)
    zone.create_txt_record(name = txt_name, values=[txt_value], ttl=60)


# Saving certificate and private to s3 bucket
def saving_certs_and_key(DOMAIN, bucket_name, pkey_pem, fullchain):

  private_key = DOMAIN + "_" + "private.key"
  certificate = DOMAIN + "_" +  "fullchain.pem"

  certificate_path = DOMAIN + '/' +certificate
  private_key_path = DOMAIN + '/' + private_key

  certificate_encoded = fullchain.encode("utf-8")
  private_key_encoded = pkey_pem

  s3 = boto3.resource("s3")
  buckets = [bucket.name for bucket in s3.buckets.all()]
  if bucket_name not in buckets:
    s3.create_bucket( Bucket = bucket_name, CreateBucketConfiguration = { 'LocationConstraint': 'ap-south-1'})
    #s3.create_bucket( Bucket = bucket_name)

  s3.Bucket(bucket_name).put_object(Key=certificate_path, Body=certificate_encoded )
  s3.Bucket(bucket_name).put_object(Key=private_key_path, Body=private_key_encoded )

  path_certificate = "https://s3.ap-south-1.amazonaws.com/" + bucket_name + "/" + certificate_path
  path_private_key = "https://s3.ap-south-1.amazonaws.com/" + bucket_name + "/" + private_key_path

  return path_certificate, path_private_key

# Flask App
app = Flask(__name__)

@app.route('/', methods=['POST']) #GET requests will be blocked
def cert():
  req_data = request.get_json()
  domain_name = req_data['domain_name']
  email_id = req_data['email_id']
  dns_provider = req_data['dns_provider']
  bucket_name = req_data['bucket_name']

  DOMAIN = domain_name


  # Create account key
  acc_key = jose.JWKRSA( key = rsa.generate_private_key( 
							       public_exponent = 65537,
                                   key_size = ACC_KEY_BITS, 
                                   backend = default_backend() ))

  # Register acceptcount and accept TOS
  net = client.ClientNetwork(acc_key, user_agent=USER_AGENT)
  directory = messages.Directory.from_json(net.get(DIRECTORY_URL).json())
  client_acme = client.ClientV2(directory, net=net)

  # Terms of Service URL is in client_acme.directory.meta.terms_of_service 
  # Registration Resource: regr 
  # Creates account with contact information. 
  email = email_id
  regr = client_acme.new_account( messages.NewRegistration.from_data( 
												email = email, 
                                                terms_of_service_agreed = True ))

  # Create domain private key and CSR 
  pkey_pem, csr_pem = new_csr_comp(DOMAIN)

  # Issue certificate
  orderr = client_acme.new_order(csr_pem)

  # Select DNS-01 within offered challenges by the CA server
  challb = select_dns01_chall(orderr)


  # Generating TXT record from account key and token
  #

  # Creation of SHA256 hash of account key
  thumbprint = acc_key.thumbprint(hash_function=hashes.SHA256)

  # Token
  token = challb.token

  # Constructing a key authorization from the token value provided in the challenge and the account key
  key_authorization = jose.b64encode(token).decode() + '.' + jose.b64encode(thumbprint).decode()

  # Computing the SHA-256 digest of the key authorization
  validation = jose.b64encode(hashlib.sha256(key_authorization.encode()).digest()).decode()

  # Printing the TXT record that needs to be updated in DNS records
  txt_record(DOMAIN, validation)

  #Cloudflare
  if dns_provider.lower() == 'cloudflare':
  	try:
  	  cloudflare_email_id = req_data['cloudflare_email_id']
  	  cloudflare_token = req_data['cloudflare_token']
  	  cloudflare_dns(cloudflare_email_id, DOMAIN, cloudflare_token, validation)
  	  sleep(120)
  	except ( UnboundLocalError, KeyError ):
  	  print('please provide "cloudflare_email_id" and "cloudflare_token"')
  #aws
  elif dns_provider.lower() == 'aws':
  	try:
  		aws_access_key_id = req_data['aws_access_key_id']
  		aws_secret_access_key = req_data['aws_secret_access_key']
  		aws_dns( DOMAIN, aws_access_key_id, aws_secret_access_key, validation )
  		sleep(120)
  	except ( UnboundLocalError, KeyError ):
  		print('please provide "aws_access_key_id" and "aws_secret_access_key"')
  else:
    sleep(300)

  #validation
  response, validation = challb.response_and_validation(client_acme.net.key)
  client_acme.answer_challenge(challb, response)

  finalized_orderr = client_acme.poll_and_finalize(orderr)

  # Saving and printing the certs and keys
  Private_key, Certificate = saving_certs_and_key(DOMAIN, bucket_name ,pkey_pem, finalized_orderr.fullchain_pem)



  # Returning path for private key and doamin certificate
  return '''
	Domain name is: {} 
	Email Id is: {}
	DNS provider is: {}
	Private Key path is: {}
	Certificate path is: {}
	'''.format(domain_name, email_id, dns_provider, Private_key, Certificate )


if __name__ == '__main__':
  app.run()
