# Do Not Use

Anything contained in this directory is unsupported and should not be used
to provision any OpenShift clusters.  Please refer to official documentation
for supported installation methods.

## How to use
Don't use it.

## RHEL specific steps
clone https://github.com/openshift/aos-ansible/pull/74 to ~/git/aos-ansible
(Red Hat use only)

# Setup

Ensure openshift-install and terraform are in your path. You also need to install terraform-libvirt-provider from https://github.com/dmacvicar/terraform-provider-libvirt/releases:
```
mkdir -p ~/.terraform.d/plugins
cd ~/.terraform.d/plugins
get wget https://github.com/dmacvicar/terraform-provider-libvirt/releases/download/v0.5.1/terraform-provider-libvirt-0.5.1.CentOS_7.x86_64.tar.gz
tar zxvf terraform-provider-libvirt-0.5.1.CentOS_7.x86_64.tar.gz
```

cd to this directory.

## One time scripts
You should run the following once ever.
```sh
./ssh_config.sh
sudo ./dnsmasq_setup.sh
```

This will configure ~/.ssh/config to ensure entries aren't added to know hosts
and configure dnsmasq to route dns requests to the right interface.

## Source environment variables.

source installrc; export variables you want to override.  You'll need to at least
update what image you want to use unless you have that exact image in that exact
place.

If installing with CentOS, you can source installrc_centos after sourcing
installrc.  This will setup image URI and ssh user.

Only CentOS or RHEL is supported at this time, you cannot deploy both at the
same time using these scripts.

## Install RHEL
./deploy.sh
This will generate install assets (inventory, install-config.yml, tfvars),
provision instances via terraform and start installation of
openshift-ansible.

## Install CentOS
Image: https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1809.qcow2.xz
Be sure to save that to ~/images/ and xz -d.

./deploy_centos.sh

## Console Access / Ingress
The console relies on a route exposed via the ingress operator which installs by
default assuming cloud provider support for service type loadbalancers. Reconfigure it.

`oc patch clusteringresses/default -n openshift-ingress-operator -p '{"spec":{"highAvailability":{"type":"UserDefined"}}}' --type merge`

And until https://github.com/openshift/cluster-ingress-operator/pull/94 merges
delete all the objects in openshift-ingress namespace so the operator recreates them.
`oc delete all --all -n openshift-ingress`

## Cleanup
Afterwards, you can cleanup with ./cleanup.sh
