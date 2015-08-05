# Couchbase Server

## Customization

### Couchbase Installation RPM
#### Installation from local RPM (default)
Put the couchbase rpm in $HOME/couchbase-rpm/COUCHBASE_VERSION/
For example :
/home/john/couchbase-rpm/3.0.3/couchbase-server-enterprise-3.0.3-centos6.x86_64.rpm

Technical details :
Installation of couchbase server from a local rpm : 
Installation done in : tasks/CentOS.yml
Configuration in : vars/CentOS.yml

#### Installation from couchbase officiel website
In roles/couchbase.couchabse-server/defaults/main.yml :
Uncomment : couchbase_server_edition: "enterprise"
Comment couchbase_server_edition: "local"

### dnsupdate module

Put dnsupdate file of (ansible-m-dnsupdate)[https://github.com/jpmens/ansible-m-dnsupdate] in your ansible modules folder.
For example :
/usr/lib/python2.7/site-packages/ansible/modules/core/network/basics/dnsupdate

## Usage

### Deploy a couchbase cluster :
ansible-playbook -v -i inventory/os/hosts/ -e 'cluster_id=rbox num_cb=2 deployment_type=origin' playbooks/os/couchbase-cluster/launch_couchbase.yml

This command deploys a cluster of 2 couchbase nodes

### Terminate a couchbase cluster :

ansible-playbook -v -i inventory/os/hosts/ -e 'cluster_id=rbox num_cb=2 deployment_type=origin' playbooks/os/couchbase-cluster/terminate.yml
