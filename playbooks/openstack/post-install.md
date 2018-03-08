# Post-Install

* [Configure DNS](#configure-dns)
* [Get the `oc` Client](#get-the-oc-client)
* [Log in Using the Command Line](#log-in-using-the-command-line)
* [Access the UI](#access-the-ui)
* [Run Custom Post-Provision Actions](#run-custom-post-provision-actions)


## Configure DNS

OpenShift requires two public DNS records to function fully. The first one points to
the master/load balancer and provides the UI/API access. The other one is a
wildcard domain that resolves app route requests to the infra node. A private DNS
server and records are not required and not managed here.

If you followed the default installation from the README section, there is no
DNS configured. You should add two entries to the `/etc/hosts` file on the
Ansible host (where you to do a quick validation. A real deployment will
however require a DNS server with the following entries set.

First, run the `openstack server list` command and note the floating IP
addresses of the *master* and *infra* nodes (we will use `10.40.128.130` for
master and `10.40.128.134` for infra here).

Then add the following entries to your `/etc/hosts`:

```
10.40.128.130 console.openshift.example.com
10.40.128.134 cakephp-mysql-example-test.apps.openshift.example.com
```

This points the cluster domain (as defined in the
`openshift_master_cluster_public_hostname` Ansible variable in `OSEv3`) to the
master node and any routes for deployed apps to the infra node.

If you deploy another app, it will end up with a different URL (e.g.
myapp-test.apps.openshift.example.com) and you will need to add that too.  This
is why a real deployment should always run a DNS where the second entry will be
a wildcard `*.apps.openshift.example.com).

This will be sufficient to validate the cluster here.

Take a look at the [External DNS][external-dns] section for
configuring a DNS service.


## Get the `oc` Client

The OpenShift command line client (called `oc`) can be downloaded and extracted
from `openshift-origin-client-tools` on the OpenShift release page:

https://github.com/openshift/origin/releases/latest/

You can also copy it from the master node:

    $ ansible -i inventory masters[0] -m fetch -a "src=/bin/oc dest=oc"

Once you obtain the `oc` binary, remember to put it in your `PATH`.


## Log in Using the Command Line

Once the `oc` client is available, you can login using the URLs specified in `/etc/hosts`:

```
oc login --insecure-skip-tls-verify=true https://console.openshift.example.com:8443 -u user -p password
oc new-project test
oc new-app --template=cakephp-mysql-example
oc status -v
curl http://cakephp-mysql-example-test.apps.openshift.example.com
```

This will trigger an image build. You can run `oc logs -f
bc/cakephp-mysql-example` to follow its progress.

Wait until the build has finished and both pods are deployed and running:

```
$ oc status -v
In project test on server https://master-0.openshift.example.com:8443

http://cakephp-mysql-example-test.apps.openshift.example.com (svc/cakephp-mysql-example)
  dc/cakephp-mysql-example deploys istag/cakephp-mysql-example:latest <-
    bc/cakephp-mysql-example source builds https://github.com/openshift/cakephp-ex.git on openshift/php:7.0
    deployment #1 deployed about a minute ago - 1 pod

svc/mysql - 172.30.144.36:3306
  dc/mysql deploys openshift/mysql:5.7
    deployment #1 deployed 3 minutes ago - 1 pod

Info:
  * pod/cakephp-mysql-example-1-build has no liveness probe to verify pods are still running.
    try: oc set probe pod/cakephp-mysql-example-1-build --liveness ...
View details with 'oc describe <resource>/<name>' or list everything with 'oc get all'.

```

You can now look at the deployed app using its route:

```
$ curl http://cakephp-mysql-example-test.apps.openshift.example.com
```

Its `title` should say: "Welcome to OpenShift".


## Access the UI

You can access the OpenShift cluster with a web browser by going to:

https://master-0.openshift.example.com:8443

Note that for this to work, the OpenShift nodes must be accessible
from your computer and its DNS configuration must use the cluster's
DNS.


## Run Custom Post-Provision Actions

A custom playbook can be run like this:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml
```

If you'd like to limit the run to one particular host, you can do so as follows:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml -l app-node-0.openshift.example.com
```

You can also create your own custom playbook. Here are a few examples:

### Add Additional YUM Repositories

```
---
- hosts: app
  tasks:

  # enable EPL
  - name: Add repository
    yum_repository:
      name: epel
      description: EPEL YUM repo
      baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/
```

This example runs against app nodes. The list of options include:

  - cluster_hosts (all hosts: app, infra, masters, dns, lb)
  - OSEv3 (app, infra, masters)
  - app
  - dns
  - masters
  - infra_hosts

### Attach Additional RHN Pools

```
---
- hosts: cluster_hosts
  tasks:
  - name: Attach additional RHN pool
    become: true
    command: "/usr/bin/subscription-manager attach --pool=<pool ID>"
    register: attach_rhn_pool_result
    until: attach_rhn_pool_result.rc == 0
    retries: 10
    delay: 1
```

This playbook runs against all cluster nodes. In order to help prevent slow connectivity
problems, the task is retried 10 times in case of initial failure.
Note that in order for this example to work in your deployment, your servers must use the RHEL image.

### Add Extra Docker Registry URLs

This playbook is located in the [custom-actions](https://github.com/openshift/openshift-ansible-contrib/tree/master/playbooks/provisioning/openstack/custom-actions) directory.

It adds URLs passed as arguments to the docker configuration program.
Going into more detail, the configuration program (which is in the YAML format) is loaded into an ansible variable
([lines 27-30](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L27-L30))
and in its structure, `registries` and `insecure_registries` sections are expanded with the newly added items
([lines 56-76](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L56-L76)).
The new content is then saved into the original file
([lines 78-82](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L78-L82))
and docker is restarted.

Example usage:
```
ansible-playbook -i <inventory> openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml  --extra-vars '{"registries": "reg1", "insecure_registries": ["ins_reg1","ins_reg2"]}'
```

### Add Extra CAs to the Trust Chain

This playbook is also located in the [custom-actions](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions) directory.
It copies passed CAs to the trust chain location and updates the trust chain on each selected host.

Example usage:
```
ansible-playbook -i <inventory> openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/add-cas.yml --extra-vars '{"ca_files": [<absolute path to ca1 file>, <absolute path to ca2 file>]}'
```

Please consider contributing your custom playbook back to openshift-ansible!

A library of custom post-provision actions exists in `openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions`. Playbooks include:

* [add-yum-repos.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-yum-repos.yml): adds a list of custom yum repositories to every node in the cluster
* [add-rhn-pools.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-rhn-pools.yml): attaches a list of additional RHN pools to every node in the cluster
* [add-docker-registry.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml): adds a list of docker registries to the docker configuration on every node in the cluster
* [add-cas.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-rhn-pools.yml): adds a list of CAs to the trust chain on every node in the cluster


[external-dns]: ./configuration.md#dns-configuration
