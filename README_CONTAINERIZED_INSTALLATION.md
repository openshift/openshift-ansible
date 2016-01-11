# Overview

Users may now deploy containerized versions of OpenShift Origin, OpenShift
Enterprise, or Atomic Enterprise Platform on Atomic
Host[https://projectatomic.io] or RHEL, Centos, and Fedora. This includes
OpenvSwitch based SDN.


## Installing on Atomic Host

When installing on Atomic Host you will automatically have containerized
installation methods selected for you based on detection of _/run/ostree-booted_

## Installing on RHEL, Centos, or Fedora

Currently the default installation method for traditional operating systems is
via RPMs. If you wish to deploy using containerized installation you may set the
ansible variable 'containerized=true' on a per host basis. This means that you
may easily deploy environments mixing containerized and RPM based installs. At
this point we suggest deploying heterogeneous environments.

## CLI Wrappers

When using containerized installations openshift-ansible will deploy a wrapper
script on each master located in _/usr/local/bin/openshift_ and a set of
symbolic links _/usr/local/bin/oc_, _/usr/local/bin/oadm_, and
_/usr/local/bin/kubectl_ to ease administrative tasks. The wrapper script spawns
a new container on each invocation so you may notice it's slightly slower than
native clients.

The wrapper scripts mount a limited subset of paths, _~/.kube_, _/etc/origin/_,
and _/tmp_. Be mindful of this when passing in files to be processed by `oc` or
 `oadm`. You may find it easier to redirect input like this :
 
 `oc create -f - < my_file.json`

## Technical Notes

### Requisite Images

Based on your deployment_type the installer will make use of the following
images. Because you may make use of a private repository we've moved the
configuration of docker additional, insecure, and blocked registries to the
beginning of the installation process ensuring that these settings are applied
before attempting to pull any of the following images.

    Origin
        openshift/origin
        openshift/node (node + openshift-sdn + openvswitch rpm for client tools)
        openshift/openvswitch (centos7 + openvswitch rpm, runs ovsdb ovsctl processes)
        registry.access.redhat.com/rhel7/etcd
    OpenShift Enterprise
        openshift3/ose
        openshift3/node
        openshift3/openvswitch
        registry.access.redhat.com/rhel7/etcd
    Atomic Enterprise Platform
        aep3/aep
        aep3/node
        aep3/openvswitch
        registry.access.redhat.com/rhel7/etcd
        
  * note openshift3/* and aep3/* images come from registry.access.redhat.com and
rely on the --additional-repository flag being set appropriately.

### Starting and Stopping Containers

The installer will create relevant systemd units which can be used to start,
stop, and poll services via normal systemctl commands. These unit names match
those of an RPM installation with the exception of the etcd service which will
be named 'etcd_container'. This change is necessary as currently Atomic Host
ships with etcd package installed as part of Atomic Host and we will instead use
a containerized version. The installer will disable the built in etcd service.
etcd is slated to be removed from os-tree in the future.

### File Paths

All configuration files are placed in the same locations as RPM based
installations and will survive os-tree upgrades.

The examples are installed into _/etc/origin/examples_ rather than
_/usr/share/openshift/examples_ because that is read-only on Atomic Host.


### Storage Requirements

Atomic Host installs normally have a very small root filesystem. However the
etcd, master, and node containers will persist data in /var/lib. Please ensure
that you have enough space on the root filesystem.

### OpenvSwitch SDN Initialization

OpenShift SDN initialization requires that the docker bridge be reconfigured and
docker is restarted. This complicates the situation when the node is running
within a container. When using the OVS SDN you'll see the node start,
reconfigure docker, restart docker which will restart all containers, and
finally start successfully.

The node service may fail to start and be restarted a few times because the
master services are also restarted along with docker. We currently work around
this by relying on Restart=always in the docker based systemd units.
