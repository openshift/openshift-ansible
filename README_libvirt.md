:warning: **WARNING** :warning: This feature is community supported and has not been tested by Red Hat. Visit [docs.openshift.com](https://docs.openshift.com) for [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/index.html) or [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/index.html) supported installation docs.

LIBVIRT Setup instructions
==========================

`libvirt` is an `openshift-ansible` provider that uses `libvirt` to create local Fedora VMs that are provisioned exactly the same way that cloud VMs would be provisioned.

This makes `libvirt` useful to develop, test and debug OpenShift and openshift-ansible locally on the developer’s workstation before going to the cloud.

Install dependencies
--------------------

1.	Install [ansible](http://www.ansible.com/)
2.	Install [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html)
3.	Install [ebtables](http://ebtables.netfilter.org/)
4.	Install [qemu and qemu-system-x86](http://wiki.qemu.org/Main_Page)
5.	Install [libvirt-python and libvirt](http://libvirt.org/)
6.	Install [genisoimage](http://cdrkit.org/)
7.	Enable and start the libvirt daemon, e.g:
	-	`systemctl enable libvirtd`
	-	`systemctl start libvirtd`
8.	[Grant libvirt access to your user¹](https://libvirt.org/aclpolkit.html)
9.	Check that your `$HOME` is accessible to the qemu user²
10.	Configure dns resolution on the host³

#### ¹ Depending on your distribution, libvirt access may be denied by default or may require a password at each access.

You can test it with the following command:

```
virsh -c qemu:///system pool-list
```

If you have access error messages, please read https://libvirt.org/acl.html and https://libvirt.org/aclpolkit.html .

In short, if your libvirt has been compiled with Polkit support (ex: Arch, Fedora 21), you can create `/etc/polkit-1/rules.d/50-org.libvirt.unix.manage.rules` as follows to grant full access to libvirt to `$USER`

```
sudo /bin/sh -c "cat - > /etc/polkit-1/rules.d/50-org.libvirt.unix.manage.rules" << EOF
polkit.addRule(function(action, subject) {
        if (action.id == "org.libvirt.unix.manage" &&
            subject.user == "$USER") {
                return polkit.Result.YES;
                polkit.log("action=" + action);
                polkit.log("subject=" + subject);
        }
});
EOF
```

If your libvirt has not been compiled with Polkit (ex: Ubuntu 14.04.1 LTS), check the permissions on the libvirt unix socket:

```
ls -l /var/run/libvirt/libvirt-sock
srwxrwx--- 1 root libvirtd 0 févr. 12 16:03 /var/run/libvirt/libvirt-sock

usermod -a -G libvirtd $USER
# $USER needs to logout/login to have the new group be taken into account
```

(Replace `$USER` with your login name)

#### ² Qemu will run with a specific user. It must have access to the VMs drives

All the disk drive resources needed by the VMs (Fedora disk image, cloud-init files) are put inside `~/libvirt-storage-pool-openshift/`.

As we’re using the `qemu:///system` instance of libvirt, qemu will run with a specific `user:group` distinct from your user. It is configured in `/etc/libvirt/qemu.conf`. That qemu user must have access to that libvirt storage pool.

If your `$HOME` is world readable, everything is fine. If your `$HOME` is private, `ansible` will fail with an error message like:

```
error: Cannot access storage file '$HOME/libvirt-storage-pool-openshift/lenaic-master-216d8.qcow2' (as uid:99, gid:78): Permission denied
```

In order to fix that issue, you have several possibilities:
 * set `libvirt_storage_pool_path` inside `playbooks/libvirt/openshift-cluster/launch.yml` and `playbooks/libvirt/openshift-cluster/terminate.yml` to a directory:
   * backed by a filesystem with a lot of free disk space
   * writable by your user;
   * accessible by the qemu user.
 * Grant the qemu user access to the storage pool.

On Arch or Fedora 22+:

```
setfacl -m g:kvm:--x ~
```

#### ³ Enabling DNS resolution to your guest VMs with NetworkManager

-	Verify NetworkManager is configured to use dnsmasq:

```sh
$ sudo vi /etc/NetworkManager/NetworkManager.conf
[main]
dns=dnsmasq
```

-	Configure dnsmasq to use the Virtual Network router for example.com:

```sh
sudo vi /etc/NetworkManager/dnsmasq.d/libvirt_dnsmasq.conf
server=/example.com/192.168.55.1
```

Test The Setup
--------------

1.	cd openshift-ansible/
2.	Try to list all instances (Passing an empty string as the cluster_id argument will result in all libvirt instances being listed)

```
  bin/cluster list libvirt ''
```

Configuration
-------------

The following options can be passed via the `-o` flag of the `create` command or as environment variables:

* `image_url` (default to `http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2.xz`): URL of the QCOW2 image to download
* `image_name` (default to `CentOS-7-x86_64-GenericCloud.qcow2`): Name of the QCOW2 image to boot the VMs on
* `image_compression` (default to `xz`): Source QCOW2 compression (only xz supported at this time)
* `image_sha256` (default to `dd0f5e610e7c5ffacaca35ed7a78a19142a588f4543da77b61c1fb0d74400471`): Expected SHA256 checksum of the downloaded image
* `libvirt_storage_pool` (default to `openshift-ansible`): name of the libvirt storage pool for the VM images. It will be created if it does not exist
* `libvirt_storage_pool_path` (default to `$HOME/libvirt-storage-pool-openshift-ansible`): path to `libvirt_storage_pool`, i.e. where the VM images are stored
* `libvirt_network` (default to `openshift-ansible`): name of the libvirt network that the VMs will use. It will be created if it does not exist
* `libvirt_instance_memory_mib` (default to `1024`): memory of the VMs in MiB
* `libvirt_instance_vcpu` (default to `2`): number of vCPUs of the VMs
* `skip_image_download` (default to `no`): Skip QCOW2 image download. This requires the `image_name` QCOW2 image to be already present in `$HOME/libvirt-storage-pool-openshift-ansible`

Creating a cluster
------------------

1.	To create a cluster with one master and two nodes

```
  bin/cluster create libvirt lenaic
```

Updating a cluster
------------------

1.	To update the cluster

```
  bin/cluster update libvirt lenaic
```

Terminating a cluster
---------------------

1.	To terminate the cluster

```
  bin/cluster terminate libvirt lenaic
```
