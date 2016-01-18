
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
Note: You must source this file before running any Ansible commands.

Alternatively, you could configure credentials in either ~/.boto or ~/.aws/credentials, see the [boto docs](http://docs.pythonboto.org/en/latest/boto_config_tut.html) for the format.

Subscribe to CentOS
-------------------

1. [CentOS on AWS](https://aws.amazon.com/marketplace/pp/B00O7WM7QW)


Set up Security Group
---------------------
By default, a cluster is launched into the `public` security group. Make sure you allow hosts to talk to each other on port `4789` for SDN.
You may also want to allow access from the outside world on the following ports:

```
• 22    - ssh
• 80    - Web Apps
• 443   - Web Apps (https)
• 4789  - SDN / VXLAN
• 8443  - OpenShift Console
• 10250 - kubelet
```


(Optional) Setup your $HOME/.ssh/config file
-------------------------------------------
In case of a cluster creation, or any other case where you don't know the machine hostname in advance, you can use `.ssh/config`
to setup a private key file to allow ansible to connect to the created hosts.

To do so, add the the following entry to your $HOME/.ssh/config file and make it point to the private key file which allows you to login on AWS.
```
Host *.compute-1.amazonaws.com
  IdentityFile $HOME/.ssh/my_private_key.pem
```

Alternatively, you can configure your ssh-agent to hold the credentials to connect to your AWS instances.

(Optional) Choose where the cluster will be launched
----------------------------------------------------

By default, a cluster is launched with the following configuration:

- Instance type: m4.large
- AMI: ami-307b3658 (for online deployments, ami-acd999c4 for origin deployments and ami-10663b78 for enterprise deployments)
- Region: us-east-1
- Keypair name: libra
- Security group: public

#### Master specific defaults:
- Master root volume size: 10 (in GiBs)
- Master root volume type: gp2
- Master root volume iops: 500 (only applicable when volume type is io1)

#### Node specific defaults:
- Node root volume size: 10 (in GiBs)
- Node root volume type: gp2
- Node root volume iops: 500 (only applicable when volume type is io1)
- Docker volume size: 25 (in GiBs)
- Docker volume ephemeral: true (Whether the docker volume is ephemeral)
- Docker volume type: gp2 (only applicable if ephemeral is false)
- Docker volume iops: 500 (only applicable when volume type is io1)

### Specifying ec2 instance type.

#### All instances:

- export ec2_instance_type='m4.large'

#### Master instances:

- export ec2_master_instance_type='m4.large'

#### Infra node instances:

- export ec2_infra_instance_type='m4.large'

#### Non-infra node instances:

- export ec2_node_instance_type='m4.large'

#### etcd instances:

- export ec2_etcd_instance_type='m4.large'

If needed, these values can be changed by setting environment variables on your system.

- export ec2_image='ami-307b3658'
- export ec2_region='us-east-1'
- export ec2_keypair='libra'
- export ec2_security_groups="['public']"
- export ec2_vpc_subnet='my_vpc_subnet'
- export ec2_assign_public_ip='true'
- export os_etcd_root_vol_size='20'
- export os_etcd_root_vol_type='standard'
- export os_etcd_vol_size='20'
- export os_etcd_vol_type='standard'
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
  yum install -y ansible python-boto pyOpenSSL
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

Specifying a deployment type
---------------------------
The --deployment-type flag can be passed to bin/cluster to specify the deployment type
1. To launch an online cluster (requires access to private repositories and amis):
```
  bin/cluster create aws --deployment-type=online <cluster-id>
```
Note: If no deployment type is specified, then the default is origin.


## Post-ansible steps

You should now be ready to follow the **What's Next?** section of the advanced installation guide to deploy your router, registry, and other components.

Refer to the advanced installation guide for your deployment type:

* [OpenShift Enterprise](https://docs.openshift.com/enterprise/3.0/install_config/install/advanced_install.html#what-s-next)
* [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html#what-s-next)
