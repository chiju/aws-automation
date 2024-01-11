
# Let's encrypt SSL Cetificate creation using ACME protocol

## Usage

Example for Json POST Request to Flask App - Cloudflare
```shell
curl --header "Content-Type: application/json" --request POST --data '{ "bucket_name":"fhfjhfjfhjftrjkjdfskjjkjklj", "domain_name":"xyz.tk", "email_id":"xyz@uvw.com", "dns_provider":"cloudflare", "cloudflare_email_id":"xyz@gmail.com",  "cloudflare_token":"hkhklnljlkj7kj8k59l40j7tl48hj9dhe356"}'  https://yktnujlfnrlmf.execute-api.ap-south-1.amazonaws.com/production
```
Example for Json POST Request to Flask App - AWS Rout53
```shell
curl --header "Content-Type: application/json" --request POST --data '{ "domain_name":"example.com", "email_id":"xyxyxxnxk@fgjjsd.com", "dns_provider":"aws", "aws_access_key_id":"jksjkljkjdksld;klsd", "aws_secret_access_key":"sdkjhdfskjsdlfjdfsljldsfj"}' http://localhost:5000/data
```

## Steps for deploying to AWS Lambda
Files needed in the folder
```
letsencrypt-lambda-s3.py
requirements.txt
zappa_settings.json
```
Execute below commands 
```shell
virtualenv .env
source .env/bin/activate
pip install -r requirements.txt
zappa deploy production
```

### Contents in the files
requirements.txt
```
boto3
flask
zappa
cryptography
pyOpenSSL==17.0.0
CloudFlare
route53
acme 
josepy
```
zappa_settings.json
```
{
    "production": {
        "app_function": "letsencrypt-lambda-s3.app",
        "aws_region": "ap-south-1",
        "profile_name": "default",
        "project_name": "letsencrypt-lam",
        "runtime": "python3.6",
        "timeout_seconds": 900
    }
}
```


## Steps for creating Flask app

###  Defining Flask App and getting email ID, Domain name and DNS provider

```shell
# Flask App
app = Flask(__name__)

@app.route('/data', methods=['POST']) #GET requests will be blocked
def cert():
  req_data = request.get_json()
  domain_name = req_data['domain_name']
  email_id = req_data['email_id']
  dns_provider = req_data['dns_provider']
    bucket_name = req_data['bucket_name']
  DOMAIN = domain_name
```

### Creating account key 
```shell
acc_key = jose.JWKRSA( key = rsa.generate_private_key( 
                       public_exponent = 65537, 
                                     key_size = ACC_KEY_BITS, 
                                     backend = default_backend() ))
```
### Creating client and registering an account

```shell

  # Register account and accept TOS
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
```
### Creating domain private key and CSR
```shell
# Create domain private key and CSR 
pkey_pem, csr_pem = new_csr_comp(DOMAIN)
# CSR Creation
def new_csr_comp(domain_name, pkey_pem=None):
    """Create certificate signing request."""
    if pkey_pem is None:
        # Create private key.
        pkey = OpenSSL.crypto.PKey()
        pkey.generate_key(OpenSSL.crypto.TYPE_RSA, CERT_PKEY_BITS)
        pkey_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                                  pkey)
    csr_pem = crypto_util.make_csr(pkey_pem, [domain_name])
    return pkey_pem, csr_pem
```
### Issue Certificate
```shell
# Issue certificate
  orderr = client_acme.new_order(csr_pem)
```
### Using DNS-01 for challenge
```# Select DNS-01 within offered challenges by the CA server
  challb = select_dns01_chall(orderr)
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
```
### Generating TXT record from account key and token
```shell
# Creation of SHA256 hash of account key
  thumbprint = acc_key.thumbprint(hash_function=hashes.SHA256)

  # Token
  token = challb.token

  # Constructing a key authorization from the token value provided in the challenge and the account key
  key_authorization = jose.b64encode(token).decode() + '.' + jose.b64encode(thumbprint).decode()

  # Computing the SHA-256 digest of the key authorization
  validation = jose.b64encode(hashlib.sha256(key_authorization.encode()).digest()).decode()
```
### Printing TXT record
```shell
# Printing the TXT record that needs to be updated in DNS records
  txt_record(DOMAIN, validation)
```
txt_record function
```shell
#Function for TXT record
def txt_record(DOMAIN, validation):
  TXT_record = '_acme-challenge.' + DOMAIN + ' IN TXT ' + validation
  return TXT_record
```

**TXT record**
```shell
_acme-challenge.chiju.adi.im IN TXT dpJXwXcJ7q_75kbC-FsruLasKtEgD-YtPzEBP378TX8
```
### CloudFlare - Updating TXT record in DNS zone
```shell
#Cloudflare
  if dns_provider.lower() == 'cloudflare':
    try:
      cloudflare_email_id = req_data['cloudflare_email_id']
      cloudflare_token = req_data['cloudflare_token']
      cloudflare_dns(cloudflare_email_id, DOMAIN, cloudflare_token, validation)
      sleep(120)
    except ( UnboundLocalError, KeyError ):
      print('please provide "cloudflare_email_id", "cloudflare_token" values')
      exit()
  else:
    sleep(300)
```
cloudflare_dns function
```shell
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
```
### AWS Route53 - Updating TXT record in DNS zone
```shell
elif dns_provider.lower() == 'aws':
    try:
      aws_access_key_id = req_data['aws_access_key_id']
      aws_secret_access_key = req_data['aws_secret_access_key']
      aws_dns( DOMAIN, aws_access_key_id, aws_secret_access_key, validation )
      sleep(120)
    except ( UnboundLocalError, KeyError ):
      print('please provide "aws_access_key_id", "aws_secret_access_key" values')
```
aws_dns function
```shell
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
```
### After updating TXT record in DNS, making an empty request to do validation and generating domain certificate

```shell
response, validation = challb.response_and_validation(client_acme.net.key)
client_acme.answer_challenge(challb, response)
finalized_orderr = client_acme.poll_and_finalize(orderr)
```
### Printing and saving private key and domain certificate
```shell
# Saving and printing the certs and keys
  Private_key, Certificate = saving_certs_and_key(DOMAIN, pkey_pem, finalized_orderr.fullchain_pem)

  # Returning path for private key and doamin certificate
  return '''
  Domain name is: {} 
  Email Id is: {}
  DNS provider is: {}
  Private Key path is: {}
  Certificate path is: {}
  '''.format(domain_name, email_id, dns_provider, Private_key, Certificate )
```
saving_certs_and_key function
```shell
### Saving and printing the certs and keys
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
  ```

### For Reference

**documentations**
->[DNS Chalange](https://tools.ietf.org/html/rfc8555#page-63)
->[ACME](https://github.com/certbot/certbot/tree/master/acme)

**ACME Servers**

 ACME v1

-   [Production]  `https://acme-v01.api.letsencrypt.org/directory`
-   [Staging]  `https://acme-staging.api.letsencrypt.org/directory`

ACME v2

-   [Production]  `https://acme-v02.api.letsencrypt.org/directory`
-   [Staging]  `https://acme-staging-v02.api.letsencrypt.org/directory`

[https://letsencrypt.org/2017/06/14/acme-v2-api.html](https://letsencrypt.org/2017/06/14/acme-v2-api.html)
