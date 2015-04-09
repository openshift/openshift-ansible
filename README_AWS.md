
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
RHEL/CentOS/Fedora
```
  yum install -y ansible python-boto
```
OSX:
```
  pip install -U boto
```


Test The Setup
--------------
1. cd openshift-ansible
1. Try to list all instances (Passing an empty string as the cluster_id
argument will result in all ec2 instances being listed)
```
  bin/cluster list aws ''
```

Creating a cluster
------------------
1. To create a cluster with one master and two nodes
```
  bin/cluster create aws <cluster-id>
```

Updating a cluster
---------------------
1. To update the cluster
```
  bin/cluster update aws <cluster-id>
```

Terminating a cluster
---------------------
1. To terminate the cluster
```
  bin/cluster terminate aws <cluster-id>
```
