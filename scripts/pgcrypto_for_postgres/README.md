# pgcrypto

## For enabling `pgcrypto` in a database
```bash
psql -U <database_username> -d <database_name> -c "CREATE EXTENSION pgcrypto;"
```
where  
**database_username** is database username, 
**database_name** is database name 


## Symmetric Encryption

Symmetric encryption encrypts and decrypts data using the same key and is faster than asymmetric encryption.  `pgp_sym_encrypt()` is used for encryption and  `Pgp_sym_decrypt()` is used for decryption

### To Encrypt 
```bash
psql -U postgres -d first -c "UPDATE users3 SET password = pgp_sym_encrypt('data', 'password', 'compress-algo=1, cipher-algo=aes256') where userid = 2;"
``` 
where
**data** is the data to be encrypted
**password** is the symmetric key for encryption
**pgp_sym_encrypt** is the symmetric encryption function
**cipher-algo** is the cipher algorithm 
**compress-algo** is the compression alogorithm

### To Decrypt
To get the encrypted data
```bash
psql -U postgres -d first -c "SELECT password FROM users3 WHERE userid = 2;"
```
the above query will give the encryted data and it will be similer to below given snippet
```bash
\xc30d04090302d2b630df776e48c969d24201f771d3146facc07f2f413bfdba9e12dd7c5b2fd5f58fa429308206f617c9aea6bdc75ccd8b6eb2f296b503dd20002b38058a8937ef1dd6567e7698b44173fdb31a
```
To decrypt the above encrypted data , execute the below query
```sql
psql -U postgres -d first -c "SELECT pgp_sym_decrypt('\xc30d04090302d2b630df776e48c969d24201f771d3146facc07f2f413bfdba9e12dd7c5b2fd5f58fa429308206f617c9aea6bdc75ccd8b6eb2f296b503dd20002b38058a8937ef1dd6567e7698b44173fdb31a', 'password1234');"
```
where 
**password ** is the symertic key for decrypting
**pgp_sym_decrypt** is the decrypting function

## Hashing
The `pgcrypto` module provides cryptographic functions for PostgreSQL. The functions `crypt()` and `gen_salt()` are specifically designed for hashing passwords. `crypt()` does the hashing and `gen_salt()` prepares algorithm parameters for it.



### For hashing passwords
For storing password as hashed password
```bash
psql -U postgres -d first -c "UPDATE users3 SET password = crypt('password123', gen_salt('bf', 8)) where userid = 2;"
```
where 
**password123** is the password,
**crypt('<password123>', gen_salt('bf', 8))** is the hashing functions
### For authenticating
```bash
psql -U postgres -d first -c "SELECT * FROM users3 WHERE userid = 2 AND password = crypt('password123', password);"
``` 
where 
**password123** is the password,
**crypt('password123',  password)** is the checking function

## Reference
[pgcrypto official documentation](https://www.postgresql.org/docs/11/pgcrypto.html#id-1.11.7.34.10)