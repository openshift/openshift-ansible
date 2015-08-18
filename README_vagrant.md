Requirements
------------
- vagrant (tested against version 1.7.2)
- vagrant-hostmanager plugin (tested against version 1.5.0)
- vagrant-registration plugin (only required for enterprise deployment type)
- vagrant-libvirt (tested against version 0.0.26)
  - Only required if using libvirt instead of virtualbox

For ``enterprise`` deployment types the base RHEL box has to be added to Vagrant:

1. Download the RHEL7 vagrant image (libvirt or virtualbox) available from the [Red Hat Container Development Kit downloads in the customer portal](https://access.redhat.com/downloads/content/293/ver=1/rhel---7/1.0.1/x86_64/product-downloads)

2. Install it into vagrant

   ``$ vagrant box add --name rhel-7 /path/to/rhel-server-libvirt-7.1-3.x86_64.box``

3. (optional, recommended) Increase the disk size of the image to 20GB - This is a two step process. (these instructions are specific to libvirt)

    Resize the actual qcow2 image:

	``$ qemu-img resize ~/.vagrant.d/boxes/rhel-7/0/libvirt/box.img 20GB``

    Edit `~/.vagrant.d/boxes/rhel-7/0/libvirt/metadata.json` to reflect the new size.  A corrected metadata.json looks like this:

	``{"provider": "libvirt", "format": "qcow2", "virtual_size": 20}``

Usage
-----
```
vagrant up --no-provision
vagrant provision
```

Using libvirt:
```
vagrant up --provider=libvirt --no-provision
vagrant provision
```

Environment Variables
---------------------
The following environment variables can be overriden:
- ``OPENSHIFT_DEPLOYMENT_TYPE`` (defaults to origin, choices: origin, enterprise, online)
- ``OPENSHIFT_NUM_NODES`` (the number of nodes to create, defaults to 2)

For ``enterprise`` deployment types these env variables should also be specified:
- ``rhel_subscription_user``: rhsm user
- ``rhel_subscription_pass``: rhsm password
- (optional) ``rhel_subscription_pool``: poolID to attach a specific subscription besides what auto-attach detects
