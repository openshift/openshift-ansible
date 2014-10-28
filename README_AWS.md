
AWS Setup Instructions
======================

Get AWS API credentials
-----------------------
1. [AWS credentials documentation](http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html)


Create a credentials file
-------------------------
1. Create a credentials file (eg ~/.aws_creds) that looks something like this (variables must have have these exact names).
```
   export AWS_ACCESS_KEY_ID='AKIASTUFF'
   export AWS_SECRET_ACCESS_KEY='STUFF'
```

1. source this file
```
  source ~/.aws_creds
```

1. Note: You must source this file in each shell that you want to run cloud.rb


Install Dependencies
--------------------
1. Ansible requires python-boto for aws operations:
```
  yum install -y ansible python-boto
```


Test The Setup
--------------
1. cd openshift-online-ansible
1. Try to list all instances:
```
  ./cloud.rb aws list
```
