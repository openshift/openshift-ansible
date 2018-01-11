# AWS playbooks

With recent desire for provisioning from customers and developers alike, the AWS
 playbook directory now supports a limited set of ansible playbooks to achieve a
 complete cluster setup. These playbooks bring into alignment our desire to
 deploy highly scalable Openshift clusters utilizing AWS auto scale groups and
 custom AMIs.

To speed in the provisioning of medium and large clusters, openshift-node
instances are created using a pre-built AMI.  A list of pre-built AMIs will
be available soon.

If the deployer wishes to build their own AMI for provisioning, instructions
to do so are provided here.

### High-level overview
- prerequisites.yml - Provision VPC, Security Groups, SSH keys, if needed.  See PREREQUISITES.md for more information.
- build_ami.yml - Builds a custom AMI.  See BUILD_AMI.md for more information.
- provision.yml - Create a vpc, elbs, security groups, launch config, asg's, etc.
- install.yml - Calls the openshift-ansible installer on the newly created instances
- provision_nodes.yml - Creates the infra and compute node scale groups
- accept.yml - This is a playbook to accept infra and compute nodes into the cluster
- provision_install.yml - This is a combination of all 3 of the above playbooks. (provision, install, and provision_nodes as well as accept.yml)

The current expected work flow should be to provide an AMI with access to Openshift repositories.  There should be a repository specified in the `openshift_additional_repos` parameter of the inventory file. The next expectation is a minimal set of values in the `provisioning_vars.yml` file to configure the desired settings for cluster instances.  These settings are AWS specific and should be tailored to the consumer's AWS custom account settings.

## How do I begin?

### Ansible configuration
The Ansible rpm shipped /etc/ansible/ansible.cfg handles aws provision and openshift-ansible plays and tasks correctly.  There is no need to modify it further.

It is common to execute installer as an unpriviledged user.  That user will not have access to /etc/ansible.  The installer will cache facts locally.  To avoid permissions issues set an env variable to tell Ansible where to cache facts.
```
$ cd ~/git/openshift-ansible
$ export FACT_PATH=${HOME}
```

### AWS Credentials

Before any provisioning may occur, AWS account credentials must be present in the environment.  This can be done in two ways:

- Create the following file `~/.aws/credentials` with the contents (substitute your access key and secret key):
   ```
   [myprofile]
   aws_access_key_id = <Your access_key here>
   aws_secret_access_key = <Your secret acces key here>
   ```
   From the shell:
   ```
   $ export AWS_PROFILE=myprofile
   ```
 ---
- Alternatively to using a profile you can export your AWS credentials as environment variables.
   ```
  $ export AWS_ACCESS_KEY_ID=AKIXXXXXX
  $ export AWS_SECRET_ACCESS_KEY=XXXXXX
   ```

### provisioning_vars file

The following are the minimum mandatory provisioning variables
```yaml
---
# Minimum mandatory provisioning variables.
# See provisioning_vars.yml.example for more information.
openshift_aws_clusterid: # example: example
openshift_aws_ssh_key_name: # example: myuser_key
openshift_aws_base_ami: # example: ami-12345678
# These are required when doing SSL on the ELBs
openshift_aws_iam_cert_path: # example: '/path/to/wildcard.<clusterid>.example.com.crt'
openshift_aws_iam_cert_key_path: # example: '/path/to/wildcard.<clusterid>.example.com.key'
# Mandatory csv list of docker devices
container_runtime_docker_storage_setup_device: '/dev/xvdb'
# These are required when doing an openshift-enterprise installation
rhsub_user: # example: 'myrhsub_user@example.com'
rhsub_pass: # example: 'myrhsub_password'
rhsub_pool: # example: 'abcd1234abcd1234abcd1234abcd1234'
```

Values specified in provisioning_vars.yml may instead be specified in your inventory group_vars
under the appropriate groups.  Most variables can exist in the 'all' group.

If customization is required for the instances, scale groups, or any other configurable option please see the ['openshift_aws/defaults/main.yml'](../../roles/openshift_aws/defaults/main.yml) for variables and overrides. These overrides can be placed in the `provisioning_vars.yml`, `inventory`, or `group_vars`.

### inventory file

In order to create the bootstrap-able AMI we need to create a basic openshift-ansible inventory.  This enables us to create the AMI using the openshift-ansible node roles.  Certain plays and tasks should execute on the local host as the local user.  It is highly recommended adding the folloing line to the inventory file.
```
localhost ansible_become=false ansible_connection=local
```

For instances in AWS it highly recommended to use the Ansible dynamic inventory and use the following pattern for dynamically created instances.
```
[masters]

[masters:children]
security_group_<cluster_id>_master

[etcd]

[etcd:children]
security_group_<cluster_id>_etcd

[lb]

[lb:children]
security_group_<cluster_id>_infra

[nodes]

[nodes:children]
security_group_<cluster_id>_compute

[security_group_<cluster_id>_master]
[security_group_<cluster_id>_etcd]
[security_group_<cluster_id>_infra]
[security_group_<cluster_id>_compute]
```

Once inventory is set correctly export it as an environment file.  This helps avoiding the -i arg to the ansible command
```
export ANSIBLE_INVENTORY=$HOME/git/openshift-ansible/inventory/hosts
```

There are more examples of cluster inventory settings [`openshift-ansible/inventory/`](../../inventory/).

### Required DNS entries
blah

## Let's Provision!

Warning:  Running these plays will provision items in your AWS account (if not
present), and you may incur billing charges.  These plays are not suitable
for the free-tier.

### Step 0 (optional)

You may provision a VPC, Security Group, and SSH keypair to build the AMI.
```
$ ansible-playbook playbooks/aws/openshift-cluster/prerequisites.yml -e @playbooks/aws/provisioning_vars.yml
```
See [`PREREQUISITES.md`](PREREQUISITES.md) for more information.

### Step 1

Once the `inventory` and the `provisioning_vars.yml` file has been updated with the correct minimal settings then we are ready to build an AMI.

```
$ ansible-playbook playbooks/aws/openshift-cluster/build_ami.yml -e @playbooks/aws/provisioning_vars.yml
```
See [`BUILD_AMI.md`](BUILD_AMI.md) for more information.

### Step 2

Now that we have created an AMI for our Openshift installation there are two ways to use the AMI.

1. In the default behavior, the AMI id will be found and used in the last created fashion.
2. The `openshift_aws_ami` option can be specified.  This will allow the user to override the behavior of the role and use a custom AMI specified in the `openshift_aws_ami` variable.

We are now ready to provision and install the cluster.  This can be accomplished by calling all of the following steps at once or one-by-one.  The all in one can be called like this:
```
$ ansible-playbook playbooks/aws/openshift-cluster/provision_install.yml -e @playbooks/aws/provisioning_vars.yml
```

If this is the first time running through this process, please attempt the following steps one-by-one and ensure the setup works correctly.

### Step 3

We are ready to create the master instances.

```
$ ansible-playbook playbooks/aws/openshift-cluster/provision.yml -e @playbooks/aws/provisioning_vars.yml
```

This playbook runs through the following steps:
1. Creates an s3 bucket for the registry named $clusterid-docker-registry
2. Create master security groups.
3. Create a master launch config.
4. Create the master auto scaling groups.
5. If certificates are desired for ELB, they will be uploaded.
6. Create internal and external master ELBs.
7. Add newly created masters to the correct groups.
8. Set a couple of important facts for the masters.

At this point we have successfully created the infrastructure including the master nodes.

### Step 4

Now it is time to install Openshift using the openshift-ansible installer.  This can be achieved by running the following playbook:

```
$ ansible-playbook playbooks/aws/openshift-cluster/install.yml -e @playbooks/aws/provisioning_vars.yml
```
This playbook accomplishes the following:
1. Builds a dynamic inventory file by querying AWS.
2. Runs the [`deploy_cluster.yml`](../deploy_cluster.yml)

Once this playbook completes, the cluster masters should be installed and configured.

### Step 5

Now that we have the cluster masters deployed, we need to deploy our infrastructure and compute nodes:

```
$ ansible-playbook playbooks/aws/openshift-cluster/provision_nodes.yml -e @playbooks/aws/provisioning_vars.yml

Once this playbook completes, it should create the compute and infra node scale groups.  These nodes will attempt to register themselves to the cluster.  These requests must be approved by an administrator in Step 6.

### Step 6

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
$ ansible-playbook accept.yml -e @playbooks/aws/provisioning_vars.yml
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

## Ready To Work!

At this point your cluster should be ready for workloads.  Proceed to deploy applications on your cluster.

## Still to come

There are more enhancements that are arriving for provisioning.  These will include more playbooks that enhance the provisioning capabilities.
