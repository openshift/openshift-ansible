
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
Note: You must source this file in each shell that you want to run cloud.rb


(Optional) Setup your $HOME/.ssh/config file
-------------------------------------------
In case of a cluster creation, or any other case where you don't know the machine hostname in advance, you can use '.ssh/config' 
to setup a private key file to allow ansible to connect to the created hosts.

To do so, add the the following entry to your $HOME/.ssh/config file and make it point to the private key file which allows you to login on AWS.
'''
Host *.compute-1.amazonaws.com
  PrivateKey $HOME/.ssh/my_private_key.pem
'''

Alternatively, you can configure your ssh-agent to hold the credentials to connect to your AWS instances.


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

Alternate AWS Credential Config
-------------------------------
1. The AWS CLI config settings will be honored if present. This includes the [Environment Variables](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-environment) as well as the [CLI Config Files](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-config-files).
1. The vagrant-openshift [AWS Credentials File](https://github.com/openshift/vagrant-openshift/#aws-credentials) will be honored if present (and will take precedence over the AWS CLI config if both are present).
