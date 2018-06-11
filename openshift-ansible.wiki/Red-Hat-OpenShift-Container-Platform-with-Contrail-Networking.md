# OpenShift Enterprise 3.7

![openshift-contrail-banner](https://github.com/savithruml/openshift-contrail/blob/master/images/openshift-contrail-banner.png)

# Install OpenShift + Contrail SDN

## Launch Instances (Azure/AWS/Baremetal)

    * Master Node   (x1 / x3 for HA)
    
        IMAGE:      RHEL 7.3/7.4 (Centos 7.4)
        CPU/RAM:    4 CPU / 32 GB RAM
        DISK:       250 GB
        SEC GRP:    Allow all traffic from everywhere
    
    * Slave Node    (xN)
    
        IMAGE:      RHEL 7.3/7.4(Centos 7.4)
        CPU/RAM:    8 CPU / 64 GB RAM
        DISK:       250 G
        SEC GRP:    Allow all traffic from everywhere

    * Loadbalancer Node (x1) in case of HA. Ignore this for a single master installation
    
        IMAGE:      RHEL 7.3/7.4(Centos 7.4)
        CPU/RAM:    2 CPU / 16 GB RAM
        DISK:       100 G
        SEC GRP:    Allow all traffic from everywhere

**NOTE:** Make sure to launch the instances in the same subnet

## Host Registration (Only for REDHAT VM's)

* Register all nodes in cluster using Red Hat Subscription Manager (RHSM)
      
       (all-nodes)# subscription-manager register --username <username> --password <password> --force

* List the available subscriptions

       (all-nodes)# subscription-manager list --available --matches '*OpenShift*'

* From the previous command, find the pool ID for OpenShift Container Platform subscription & attach it

       (all-nodes)# subscription-manager attach --pool=<pool-ID>

* Disable all yum respositories

       (all-nodes)# subscription-manager repos --disable="*"

* Enable only the repositories required by OpenShift Container Platform 3.7

       (all-nodes)# subscription-manager repos \
                      --enable="rhel-7-server-rpms" \
                      --enable="rhel-7-server-extras-rpms" \
                      --enable="rhel-7-server-ose-3.7-rpms" \
                      --enable="rhel-7-fast-datapath-rpms"

## Installing Base packages (REDHAT & CENTOS)

* Install EPEL

       (all-nodes)# yum install wget -y && wget -O /tmp/epel-release-latest-7.noarch.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && rpm -ivh /tmp/epel-release-latest-7.noarch.rpm

* Update the system to use the latest packages

       (all-nodes)# yum update -y

* Install the following package, which provides OpenShift Container Platform utilities
      
       (all-nodes)# yum install atomic-openshift-excluder atomic-openshift-utils git python-netaddr -y

* Remove the atomic-openshift packages from the list for the duration of the installation 

       (all-nodes)# atomic-openshift-excluder unexclude -y
       
* Enable SSH access for root user 

       (all-nodes)# sudo su
       (all-nodes)# passwd
       (all-nodes)# sed -i -e 's/#PermitRootLogin yes/PermitRootLogin yes/g' -e 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config 
       (all-nodes)# service sshd restart
       (all-nodes)# logout
    
       Logout & login as root user

* Enforce SELinux security policy

       (all-nodes)# vi /etc/selinux/config

              SELINUX=enforcing

* Add a static entry for master/slaves in /etc/hosts

       (all-nodes)# vi /etc/hosts
                 
              10.84.18.1 master.test.net master
              10.84.18.2 slave.test.net  slave

       (all-nodes)# ping master
       (all-nodes)# ping slave

* Enable passwordless SSH access

       (ansible-node)# ssh-keygen -t rsa
       (ansible-node)# ssh-copy-id root@<master>
       (ansible-node)# ssh-copy-id root@<slave>

  If passwordless SSH doesn't work, make sure to turn set `StrictModes no` in `/etc/ssh/sshd_config` & restart SSH service

* Sync NTP

       (all-nodes)# service ntpd stop
       (all-nodes)# ntpdate -s time.nist.gov
       (all-nodes)# service ntpd start

* Download packages

  1. **For Contrail 4.X**

       Download the package from Juniper site
       Download from [here](https://www.juniper.net/support/downloads/?p=contrail#sw)
  
       IMAGE: Redhat 7 + Kubernetes
     
         (ansible-node)# wget <contrail-container-image>.tgz && tar -xvzf <contrail-container-image>.tgz

  2. **For Contrail 5.X**

       Proceed without downloading any packages

## Install OpenShift with Contrail Networking
METHOD 1: 
* Clone OpenShift-Ansible repo

       (ansible-node)# cd /root
       (ansible-node)# git clone https://github.com/Juniper/openshift-ansible -b release-3.7-contrail
       
       
  METHOD2:
  *Download installer tar ball from Juniper Website (click_here)
       
       Step1:
       Download the Openshift Install package (contrail-openshift-deployer-5.0.0-0.40.tar) from the juniper website.
       
       Step2:
       Copy the downloaded package to the node from where the ansible deployment will be executed
       *Please note: This node will need password less access to Openshift Master and Slave Nodes, Read the Pre-requisites carefully
       eg:  scp contrail-openshift-deployer-5.0.0-0.40.tar <openshift-ansible-node>:/root/.
       
       Step3:
       Untar the package using the command as below
       tar -xvf  contrail-openshift-deployer-5.0.0-0.40.tar -C /root/
       
       Step4:
       Verify the contents of the openshift-ansible directory
       cd /root/openshift-ansible/
       
       Step5
       Modify the inventory file to match your own Openshift environment.  
       cd /root/openshift-ansible/
       vi inventory/byo/ose-install 


* Populate the install file with Contrail related information

   Make sure to add the masters under [nodes] section of the inventory as well. This will ensure that the contrail control pods will come up on the OpenShift masters

   Example for single master, refer [here](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/ose-install)

   Example for HA master, refer [here](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/ose-install-ha)

       (ansible-node)# vi /root/openshift-ansible/inventory/byo/ose-install

              [OSEv3:vars]
              ...
              # Contrail 4.X releases

              #openshift_use_contrail=true
              #contrail_os_release=redhat7
              #contrail_version=4.0
              #analyticsdb_min_diskgb=50
              #configdb_min_diskgb=25
              #vrouter_physical_interface=eno1
              #contrail_docker_images_path=/root/docker_images

              # Contrail 5.X releases
              contrail_version=5.0.0-0.40
              contrail_registry=hub.juniper.net/contrail
              contrail_registry_username=<username-for-contrail-container-registry>
              contrail_registry_password=<password-for-contrail-container-registry>
              vrouter_physical_interface=eth0
              ...

  **NOTE:** To understand each of the above parameters, refer to this [doc](https://github.com/savithruml/openshift-ansible/blob/contrail-openshift/roles/contrail_master/README.md)

* Run the ansible-playbook. This will install OpenShift Container Platform with Contrail Networking

       (ansible-node)# cd /root/openshift-ansible
       (ansible-node)# ansible-playbook -i inventory/byo/ose-install inventory/byo/ose-prerequisites.yml
       (ansible-node)# ansible-playbook -i inventory/byo/ose-install playbooks/byo/openshift_facts.yml
       (ansible-node)# ansible-playbook -i inventory/byo/ose-install playbooks/byo/config.yml

* Verify Contrail SDN came up fine

       (master)# oc get ds -n kube-system
       (master)# oc get pods -n kube-system

*  Create a password for admin user to login to the UI
    
       (master-node)# htpasswd /etc/origin/master/htpasswd admin

*  Assign cluster-admin role to admin user

       (master-node)# oadm policy add-cluster-role-to-user cluster-admin admin
       (master-node)# oc login -u admin

* Check if you can open & login to Contrail & OpenShift Web-UI, else flush iptables

       Contrail: https://<master-node-ip>:8143

       OpenShift: https://<master-node-ip>:8443

* Test by launching pods, services, namespaces, network-policies, ingress, etc., by looking at these [examples](https://github.com/savithruml/openshift-contrail/tree/master/openshift/examples)

# Install Contrail SDN on an existing OpenShift setup

* Remove the existing SDN (OVS, calico, nuage, etc). Refer to respective manuals for help
 For Contrail 4.X

* Download packages

  1. **For Contrail 4.X**

       Download the package from Juniper site
       Download from [here](https://www.juniper.net/support/downloads/?p=contrail#sw)
  
       IMAGE: Redhat 7 + Kubernetes
     
         (ansible-node)# wget <contrail-container-image>.tgz && tar -xvzf <contrail-container-image>.tgz

  2. **For Contrail 5.X**

       Proceed without downloading any packages

* On masters, we need the following docker containers

       1. contrail-controller
       2. contrail-analytics
       3. contrail-analyticsdb
       4. contrail-kube-manager

* On minions, we need the following docker containers

       1. contrail-agent
       2. contrail-kubernetes-agent

* Add contrail, daemon-set-controller to privileged scc

       (master)# oadm policy add-scc-to-user privileged system:serviceaccount:kube-system:contrail
       (master)# oadm policy add-scc-to-user privileged system:serviceaccount:kube-system:daemon-set-controller
 
* Label the masters, so we can launch Contrail pods
 
       (master)# oc label nodes <all-master-nodes> opencontrail.org/controller=true
 
* Make masters schedulable

       (master)# oadm manage <all-master-nodes> --schedulable

* Open relevant Contrail SDN ports in iptables

    1. On master instances, open the [following ports](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/iptables-master)

    2. On node instances, open the [following ports](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/iptables-node)

* Populate the single YAML file based on your setup

  1. **For Contrail 4.X**
 
          (master)# wget https://github.com/Juniper/openshift-ansible/blob/release-3.7-contrail/roles/contrail_master/templates/contrail-installer-4.j2

  2. **For Contrail 5.X**

          (master)# wget https://github.com/Juniper/openshift-ansible/blob/release-3.7-contrail/roles/contrail_master/templates/contrail-installer-5.j2



* Launch the installer

       (master)# mv <contrail-installer-4/5.j2> contrail-installer.yml
       (master)# oc create –f contrail-installer.yml
 
* Verify services are all up & running
 
       (master)# oc get ds –n kube-system
       (master)# oc get pods –n kube-system
       (master)# oc exec <contrail-pod-name> contrail-status –n kube-system

* Create a password for admin user to login to the UI

       (master-node)# htpasswd /etc/origin/master/htpasswd admin

*  Assign cluster-admin role to admin user

       (master-node)# oadm policy add-cluster-role-to-user cluster-admin admin
       (master-node)# oc login -u admin

* Patch restricted SCC

       (master-node)# oc patch scc restricted --patch='{ "runAsUser": { "type": "RunAsAny" } }'

* Check if you can open & login to Contrail & OpenShift Web-UI, else flush iptables

       Contrail: https://<master-node-ip>:8143
       OpenShift: https://<master-node-ip>:8443

* Test by launching pods, services, namespaces, network-policies, ingress, etc., by looking at these [examples](https://github.com/savithruml/openshift-contrail/tree/master/openshift/examples)
