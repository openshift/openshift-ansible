
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
2. source this file
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

(Optional) Choose where the cluster will be launched
----------------------------------------------------

By default, a cluster is launched with the following configuration:

- Instance type: m3.large
- AMI: ami-307b3658 (for online deployments, ami-acd999c4 for origin deployments and ami-10663b78 for enterprise deployments)
- Region: us-east-1
- Keypair name: libra
- Security group: public

Master specific defaults:
- Master root volume size: 10 (in GiBs)
- Master root volume type: gp2
- Master root volume iops: 500 (only applicable when volume type is io1)

Node specific defaults:
- Node root volume size: 10 (in GiBs)
- Node root volume type: gp2
- Node root volume iops: 500 (only applicable when volume type is io1)
- Docker volume size: 25 (in GiBs)
- Docker volume ephemeral: true (Whether the docker volume is ephemeral)
- Docker volume type: gp2 (only applicable if ephemeral is false)
- Docker volume iops: 500 (only applicable when volume type is io1)

If needed, these values can be changed by setting environment variables on your system.

- export ec2_instance_type='m3.large'
- export ec2_ami='ami-307b3658'
- export ec2_region='us-east-1'
- export ec2_keypair='libra'
- export ec2_security_group='public'
- export os_master_root_vol_size='20'
- export os_master_root_vol_type='standard'
- export os_node_root_vol_size='15'
- export os_docker_vol_size='50'
- export os_docker_vol_ephemeral='false'

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
