# 3.10 upgrade support matrix

## Description
We've got a lot of different potential upgrade paths we need to approach
and prioritize for users going from 3.9 to 3.10.

I'm creating this document so we can discuss what to prioritize and what
to support.

## Known 3.9 install paths

### RPM
openshift services are installed via rpm.  The docker (container runtime)
portion runs the pods; It is possible to containerize some things and not
others (like etcd), but support of this kind of configuration is unknown at
best.

* rpm + docker
* rpm + docker + crio
* rpm + system-container-docker + crio
* rpm + crio only
* rpm + system-container-docker + system-container-crio

### Containerized
Containerized installs are normal RHEL hosts, but openshift services are
installed via docker containers instead of using rpm packages.

* containerized + docker
* containerized + docker + crio
* containerized + system-container-docker
* containerized + system-container-docker + crio
* containerized + crio only?

### Atomic
Similar to containerized, but 100% of items run as containers or system
containers, and there is no alternative.  IMO, this will probably be the
most straight forward group of combinations to migrate, but much of the work
may be unique to atomic and not apply to other systems.

* Atomic
* Atomic + crio
* Atomic + crio + system containers
* Atomic + system containers

### Thoughts
In addition to the above install variants, clusters may be a combination of
one or more of the variants (ie, mixed clusters)

Clusters may also be a mix of bootstrapped and normal nodes, or all
bootstrapped in 3.9.  This is to say nothing of AWS + Scale groups and our
support of openstack specific plays.

## Known 3.10 models
Everyone is getting static pods now, so that's nice.

### RPM
* rpm + docker
* rpm + system-container-docker
* rpm + some amount of crio

* bootstrapped + rpm + docker
* bootstrapped + rpm + system-container-docker
* bootstrapped + rpm + some amount of crio

Do we support a mix of bootstrapped and non bootstrapped nodes?

### Containerized
This install type has been removed in 3.10 but we still need to account
for existing containerized installations and how to move them towards
one of the other methods.

### System Containers
Is this a thing?

### Atomic
A cross between containerized installs, system container installs.

## Design
So, we can't do much about the state of existing installs.  We can however
limit the number of possible places systems can go in 3.10.

### Prioritize
From what 3.9 matrix to 3.10 matrix is the first item to tackle?
Second? Third?  Etc.

## Proposals
### Move everything to bootstrapped
It's currently the default in 3.10, let's make it mandatory in 3.10.  I don't
see a compelling reason not to.  We have to support it for our AWS, GCP and
other cloud platforms anyway, so might as well make this the only option.

### Get rid of RPM installation path
I realize this one is a tough sell.  Doing this will allow us to greatly
converge atomic and rhel install methods.  The exception to this is the
container runtime.  Apparently crio doesn't work as a system container today,
so we need to allow flexibility there.  I think we should ship a crio spin
of atomic or otherwise enable installing crio on atomic in a sane manner.
