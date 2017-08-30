# AWS playbooks

## Provisioning

With recent desire for provisioning from customers and developers alike, the AWS
 playbook directory now supports a limited set of ansible playbooks to achieve a
 complete cluster setup. These playbooks bring into alignment our desire to
 deploy highly scalable Openshift clusters utilizing AWS auto scale groups and
 custom AMIs.

### Where do I start?

Before any provisioning may occur, AWS account credentials must be present in the environment.  This can be done in two ways:

- Create the following file `~/.aws/credentials` with the contents (substitute your access key and secret key):
   ```
   [myaccount]
   aws_access_key_id = <Your access_key here>
   aws_secret_access_key = <Your secret acces key here>
   ```
   From the shell:
   ```
   $ export AWS_PROFILE=myaccount
   ```
 ---
- Alternatively to using a profile you can export your AWS credentials as environment variables.
   ```
  $ export AWS_ACCESS_KEY_ID=AKIXXXXXX
  $ export AWS_SECRET_ACCESS_KEY=XXXXXX
   ```

### Let's Provision!

The newly added playbooks are the following:
- build_ami.yml - Builds a custom AMI.  This currently requires the user to supply a valid AMI with access to repositories that contain openshift repositories.
- provision.yml - Create a vpc, elbs, security groups, launch config, asg's, etc.
- install.yml - Calls the openshift-ansible installer on the newly created instances
- provision_nodes.yml - Creates the infra and compute node scale groups
- accept.yml - This is a playbook to accept infra and compute nodes into the cluster
- provision_install.yml - This is a combination of all 3 of the above playbooks. (provision, install, and provision_nodes as well as accept.yml)

The current expected work flow should be to provide an AMI with access to Openshift repositories.  There should be a repository specified in the `openshift_additional_repos` parameter of the inventory file. The next expectation is a minimal set of values in the `provisioning_vars.yml` file to configure the desired settings for cluster instances.  These settings are AWS specific and should be tailored to the consumer's AWS custom account settings.

```yaml
---
openshift_node_bootstrap: True

# specify a clusterid
# openshift_aws_clusterid: default

# specify a region
# openshift_aws_region: us-east-1

# must specify a base_ami when building an AMI
# openshift_aws_base_ami: # base image for AMI to build from
# specify when using a custom AMI
# openshift_aws_ami:

# when creating an encrypted AMI please specify use_encryption
# openshift_aws_ami_encrypt: False

# custom certificates are required for the ELB
# openshift_aws_iam_cert_path: '/path/to/cert/wildcard.<clusterid>.<domain>.com.crt'
# openshift_aws_iam_cert_key_path: '/path/to/key/wildcard.<clusterid>.<domain>.com.key'
# openshift_aws_iam_cert_chain_path: '/path/to/ca_cert_file/ca.crt'

# This is required for any ec2 instances
# openshift_aws_ssh_key_name: myuser_key

# This will ensure these users are created
#openshift_aws_users:
#- key_name: myuser_key
#  username: myuser
#  pub_key: |
#         ssh-rsa AAAA
```

If customization is required for the instances, scale groups, or any other configurable option please see the ['openshift_aws/defaults/main.yml'](../../roles/openshift_aws/defaults/main.yml) for variables and overrides. These overrides can be placed in the `provisioning_vars.yml`, `inventory`, or `group_vars`.

In order to create the bootstrap-able AMI we need to create an openshift-ansible inventory file.  This file enables us to create the AMI using the openshift-ansible node roles. The exception here is that there will be no hosts specified by the inventory file.  Here is an example:

```ini
[OSEv3:children]
masters
nodes
etcd

[OSEv3:children]
masters
nodes
etcd

[OSEv3:vars]
################################################################################
# Ensure these variables are set for bootstrap
################################################################################
# openshift_deployment_type is required for installation
openshift_deployment_type=origin
openshift_master_bootstrap_enabled=True

openshift_hosted_router_wait=False
openshift_hosted_registry_wait=False

# Repository for installation
openshift_additional_repos=[{'name': 'openshift-repo', 'id': 'openshift-repo',  'baseurl': 'https://mirror.openshift.com/enterprise/enterprise-3.6/latest/x86_64/os/', 'enabled': 'yes', 'gpgcheck': 0, 'sslverify': 'no', 'sslclientcert': '/var/lib/yum/client-cert.pem', 'sslclientkey': '/var/lib/yum/client-key.pem', 'gpgkey': 'https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-release https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-beta https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-openshifthosted'}]

################################################################################
# cluster specific settings maybe be placed here

[masters]

[etcd]

[nodes]
```

There are more examples of cluster inventory settings [`here`](../../inventory/byo/).

#### Step 1

Once the `inventory` and the `provisioning_vars.yml` file has been updated with the correct settings for the desired AWS account then we are ready to build an AMI.

```
$ ansible-playbook -i inventory.yml build_ami.yml -e @provisioning_vars.yml
```

1. This script will build a VPC. Default name will be clusterid if not specified.
2. Create an ssh key required for the instance.
3. Create a security group.
4. Create an instance using the key from step 2 or a specified key.
5. Run openshift-ansible setup roles to ensure packages and services are correctly configured.
6. Create the AMI.
7. If encryption is desired
  - A KMS key is created with the name of $clusterid
  - An encrypted AMI will be produced with $clusterid KMS key
8. Terminate the instance used to configure the AMI.

More AMI specific options can be found in ['openshift_aws/defaults/main.yml'](../../roles/openshift_aws/defaults/main.yml).  When creating an encrypted AMI please specify use_encryption:
```
# openshift_aws_ami_encrypt: True  # defaults to false
```

**Note**:  This will ensure to take the recently created AMI and encrypt it to be used later.  If encryption is not desired then set the value to false (defaults to false). The AMI id will be fetched and used according to its most recent creation date.

#### Step 2

Now that we have created an AMI for our Openshift installation, there are two ways to use the AMI.

1. In the default behavior, the AMI id will be found and used in the last created fashion.
2. The `openshift_aws_ami` option can be specified.  This will allow the user to override the behavior of the role and use a custom AMI specified in the `openshift_aws_ami` variable.

We are now ready to provision and install the cluster.  This can be accomplished by calling all of the following steps at once or one-by-one.  The all in one can be called like this:
```
$ ansible-playbook -i inventory.yml provision_install.yml -e @provisioning_vars.yml
```

If this is the first time running through this process, please attempt the following steps one-by-one and ensure the setup works correctly.

#### Step 3

We are ready to create the master instances.

```
$ ansible-playbook provision.yml -e @provisioning_vars.yml
```

This playbook runs through the following steps:
1. Ensures a VPC is created.
2. Ensures a SSH key exists.
3. Creates an s3 bucket for the registry named $clusterid-docker-registry
4. Create master security groups.
5. Create a master launch config.
6. Create the master auto scaling groups.
7. If certificates are desired for ELB, they will be uploaded.
8. Create internal and external master ELBs.
9. Add newly created masters to the correct groups.
10. Set a couple of important facts for the masters.

At this point we have successfully created the infrastructure including the master nodes.

#### Step 4

Now it is time to install Openshift using the openshift-ansible installer.  This can be achieved by running the following playbook:

```
$ ansible-playbook -i inventory.yml install.yml @provisioning_vars.yml
```
This playbook accomplishes the following:
1. Builds a dynamic inventory file by querying AWS.
2. Runs the [`byo`](../../common/openshift-cluster/config.yml)

Once this playbook completes, the cluster masters should be installed and configured.

#### Step 5

Now that we have a cluster deployed it will be more interesting to create some node types.  This can be done easily with the following playbook:

```
$ ansible-playbook provision_nodes.yml -e @provisioning_vars.yml
```

Once this playbook completes, it should create the compute and infra node scale groups.  These nodes will attempt to register themselves to the cluster.  These requests must be approved by an administrator.

#### Step 6

To facilitate the node registration process, nodes may be registered by running the following script `accept.yml`.  This script can register in a few different ways.
- approve_all - **Note**: this option is for development and test environments.  Security is bypassed
- nodes - A list of node names that will be accepted into the cluster

```yaml
 oc_adm_csr:
   #approve_all: True
   nodes: < list of nodes here >
   timeout: 0
```

Once the desired accept method is chosen, run the following playbook `accept.yml`:
1. Run the following playbook.
```
$ ansible-playbook accept.yml -e @provisioning_vars.yml
```

Login to a master and run the following command:
```
ssh root@<master ip address>
$ oc --config=/etc/origin/master/admin.kubeconfig get csr
node-bootstrapper-client-ip-172-31-49-148-ec2-internal   1h       system:serviceaccount:openshift-infra:node-bootstrapper   Approved,Issued
node-bootstrapper-server-ip-172-31-49-148-ec2-internal   1h       system:node:ip-172-31-49-148.ec2.internal                 Approved,Issued
```

Verify the `CONDITION` is `Approved,Issued` on the `csr` objects.  There are two for each node required.
1. `node-bootstrapper-client` is a request to access the api/controllers.
2. `node-bootstrapper-server` is a request to join the cluster.

Once this is complete, verify the nodes have joined the cluster and are `ready`.

```
$ oc --config=/etc/origin/master/admin.kubeconfig get nodes
NAME                            STATUS                     AGE       VERSION
ip-172-31-49-148.ec2.internal   Ready                      1h       v1.6.1+5115d708d7
```

### Ready To Work!

At this point your cluster should be ready for workloads.  Proceed to deploy applications on your cluster.

### Still to come

There are more enhancements that are arriving for provisioning.  These will include more playbooks that enhance the provisioning capabilities.
