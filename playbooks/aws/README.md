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
- build_ami.yml
- provision.yml

The current expected work flow should be to provide the `vars.yml` file with the
desired settings for cluster instances.  These settings are AWS specific and should
be tailored to the consumer's AWS custom account settings.

```yaml
clusterid: mycluster
region: us-east-1

provision:
  clusterid: "{{ clusterid }}"
  region: "{{ region }}"

  build:
    base_image: ami-bdd5d6ab # base image for AMI to build from
    # when creating an encrypted AMI please specify use_encryption
    use_encryption: False

    yum_repositories: # this is an example repository but it requires sslclient info.  Use a valid yum repository for openshift rpms
    - name: openshift-repo
      file: openshift-repo
      description: OpenShift Builds
      baseurl: https://mirror.openshift.com/enterprise/online-int/latest/x86_64/os/
      enabled: yes
      gpgcheck: no
      sslverify: no
      # client cert and key required for this repository
      sslclientcert: "/var/lib/yum/client-cert.pem"
      sslclientkey: "/var/lib/yum/client-key.pem"
      gpgkey: "https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-release https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-beta https://mirror.ops.rhcloud.com/libra/keys/RPM-GPG-KEY-redhat-openshifthosted"

  # for s3 registry backend
  openshift_registry_s3: True

  # if using custom certificates these are required for the ELB
  iam_cert_ca:
    name: test_openshift
    cert_path: '/path/to/wildcard.<clusterid>.example.com.crt'
    key_path: '/path/to/wildcard.<clusterid>.example.com.key'
    chain_path: '/path/to/cert.ca.crt'

  instance_users:
  - key_name: myuser_key
    username: myuser
    pub_key: |
           ssh-rsa aaa<place public ssh key here>aaaaa user@<clusterid>

  node_group_config:
    tags:
      clusterid: "{{ clusterid }}"
      environment: stg
    ssh_key_name: myuser_key # name of the ssh key from above

    # configure master settings here
    master:
      instance_type: m4.xlarge
      ami: ami-cdeec8b6 # if using an encrypted AMI this will be replaced
      volumes:
      - device_name: /dev/sdb
        volume_size: 100
        device_type: gp2
        delete_on_termination: False
      health_check:
        period: 60
        type: EC2
      # Set the following number to be the same for masters.
      min_size: 3
      max_size: 3
      desired_size: 3
      tags:
        host-type: master
        sub-host-type: default
      wait_for_instances: True
...
  vpc:
    # name: mycluster  # If missing; will default to clusterid
    cidr: 172.31.0.0/16
    subnets:
      us-east-1:  # These are us-east-1 region defaults. Ensure this matches your region
      - cidr: 172.31.48.0/20
        az: "us-east-1c"
      - cidr: 172.31.32.0/20
        az: "us-east-1e"
      - cidr: 172.31.16.0/20
        az: "us-east-1a"

```

Repeat the following setup for the infra and compute node groups.  This most likely
 will not need editing but if further customization is required these parameters
 can be updated.

#### Step 1

Once the vars.yml file has been updated with the correct settings for the desired AWS account then we are ready to build an AMI.

```
$ ansible-playbook build_ami.yml
```

1. This script will build a VPC. Default name will be clusterid if not specified.
2. Create an ssh key required for the instance.
3. Create an instance.
4. Run some setup roles to ensure packages and services are correctly configured.
5. Create the AMI.
6. If encryption is desired
  - A KMS key is created with the name of $clusterid
  - An encrypted AMI will be produced with $clusterid KMS key
7. Terminate the instance used to configure the AMI.

#### Step 2

Now that we have created an AMI for our Openshift installation, that AMI id needs to be placed in the `vars.yml` file.  To do so update the following fields (The AMI can be captured from the output of the previous step or found in the ec2 console under AMIs):

```
  # when creating an encrypted AMI please specify use_encryption
  use_encryption: False # defaults to false
```

**Note**: If using encryption, specify with `use_encryption: True`.  This will ensure to take the recently created AMI and encrypt it to be used later.  If encryption is not desired then set the value to false. The AMI id will be fetched and used according to its most recent creation date. 

#### Step 3

Create an openshift-ansible inventory file to use for a byo installation.  The exception here is that there will be no hosts specified by the inventory file.  Here is an example:

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
# cluster specific settings maybe be placed here
openshift_hosted_router_wait=False
openshift_hosted_registry_wait=False

[masters]

[etcd]

[nodes]
```

There are more examples of cluster inventory settings [`here`](../../inventory/byo/).

#### Step 4

We are ready to create the master instances and install Openshift.

```
$ ansible-playbook -i <inventory from step 3> provision.yml
```

This playbook runs through the following steps:
1. Ensures a VPC is created
2. Ensures a SSH key exists
3. Creates an s3 bucket for the registry named $clusterid
4. Create master security groups
5. Create a master launch config
6. Create the master auto scaling groups
7. If certificates are desired for ELB, they will be uploaded
8. Create internal and external master ELBs
9. Add newly created masters to the correct groups
10. Set a couple of important facts for the masters
11. Run the [`byo`](../../common/openshift-cluster/config.yml)

At this point we have created a successful cluster with only the master nodes.


#### Step 5

Now that we have a cluster deployed it might be more interesting to create some node types.  This can be done easily with the following playbook:

```
$ ansible-playbook provision_nodes.yml
```

Once this playbook completes, it should create the compute and infra node scale groups.  These nodes will attempt to register themselves to the cluster.  These requests must be approved by an administrator.

#### Step 6

The registration of our nodes can be automated by running the following script `accept.yml`.  This script can handle the registration in a few different ways.
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
$ ansible-playbook accept.yml
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

### Still to compute

There are more enhancements that are arriving for provisioning.  These will include more playbooks that enhance the provisioning capabilities.
