# Containerized openshift-ansible to run playbooks

The [Dockerfile](images/installer/Dockerfile) in this repository uses the [playbook2image](https://github.com/openshift/playbook2image) source-to-image base image to containerize `openshift-ansible`. The resulting image can run any of the provided playbooks. See [BUILD.md](BUILD.md) for image build instructions.

The image is designed to **run as a non-root user**. The container's UID is mapped to the username `default` at runtime. Therefore, the container's environment reflects that user's settings, and the configuration should match that. For example `$HOME` is `/opt/app-root/src`, so ssh keys are expected to be under `/opt/app-root/src/.ssh`. If you ran a container as `root` you would have to adjust the container's configuration accordingly, e.g. by placing ssh keys under `/root/.ssh` instead. Nevertheless, the expectation is that containers will be run as non-root; for example, this container image can be run inside OpenShift under the default `restricted` [security context constraint](https://docs.openshift.org/latest/architecture/additional_concepts/authorization.html#security-context-constraints).

**Note**: at this time there are known issues that prevent to run this image for installation/upgrade purposes (i.e. run one of the config/upgrade playbooks) from within one of the hosts that is also an installation target at the same time: if the playbook you want to run attempts to manage the docker daemon and restart it (like install/upgrade playbooks do) this would kill the container itself during its operation.

## A note about the name of the image

The released container images for openshift-ansible follow the naming scheme determined by OpenShift's `imageConfig.format` configuration option. This means that the released image name is `openshift/origin-ansible` instead of `openshift/openshift-ansible`.

This provides consistency with other images used by the platform and it's also a requirement for some use cases like using the image from [`oc cluster up`](https://github.com/openshift/origin/blob/master/docs/cluster_up_down.md).

## Usage

The `playbook2image` base image provides several options to control the behaviour of the containers. For more details on these options see the [playbook2image](https://github.com/openshift/playbook2image) documentation.

At the very least, when running a container you must specify:

1. An **inventory**. This can be a location inside the container (possibly mounted as a volume) with a path referenced via the `INVENTORY_FILE` environment variable. Alternatively you can serve the inventory file from a web server and use the `INVENTORY_URL` environment variable to fetch it, or `DYNAMIC_SCRIPT_URL` to download a script that provides a dynamic inventory.

1. **ssh keys** so that Ansible can reach your hosts. These should be mounted as a volume under `/opt/app-root/src/.ssh` under normal usage (i.e. when running the container as non-root).

1. The **playbook** to run. This is set using the `PLAYBOOK_FILE` environment variable. If you don't specify a playbook the [`openshift_facts`](playbooks/byo/openshift_facts.yml) playbook will be run to collect and show facts about your OpenShift environment.

Here is an example of how to run a containerized `openshift-ansible` playbook that will check the expiration dates of OpenShift's internal certificates using the [`openshift_certificate_expiry` role](roles/openshift_certificate_expiry):

    docker run -u `id -u` \
           -v $HOME/.ssh/id_rsa:/opt/app-root/src/.ssh/id_rsa:Z \
           -v /etc/ansible/hosts:/tmp/inventory \
           -e INVENTORY_FILE=/tmp/inventory \
           -e PLAYBOOK_FILE=playbooks/byo/openshift-checks/certificate_expiry/default.yaml \
           -e OPTS="-v" -t \
           openshift/origin-ansible

You might want to adjust some of the options in the example to match your environment and/or preferences. For example: you might want to create a separate directory on the host where you'll copy the ssh key and inventory files prior to invocation to avoid unwanted SELinux re-labeling of the original files or paths (see below).

Here is a detailed explanation of the options used in the command above:

* ``-u `id -u` `` makes the container run with the same UID as the current user, which is required for permissions so that the ssh key can be read inside the container (ssh private keys are expected to be readable only by their owner). Usually you would invoke `docker run` as a non-root user that has privileges to run containers and leave that option as is.

* `-v $HOME/.ssh/id_rsa:/opt/app-root/src/.ssh/id_rsa:Z` mounts your ssh key (`$HOME/.ssh/id_rsa`) under the `default` user's `$HOME/.ssh` in the container (as explained above, `/opt/app-root/src` is the `$HOME` of the `default` user in the container). If you mount the ssh key into a non-standard location you can add an environment variable with `-e ANSIBLE_PRIVATE_KEY_FILE=/the/mount/point` or set `ansible_ssh_private_key_file=/the/mount/point` as a variable in the inventory to point Ansible at it.

  Note that the ssh key is mounted with the `:Z` flag: this is also required so that the container can read the ssh key from its restricted SELinux context; this means that *your original ssh key file will be re-labeled* to something like `system_u:object_r:container_file_t:s0:c113,c247`. For more details about `:Z` please check the `docker-run(1)` man page. Please keep this in mind when providing these volume mount specifications because this could have unexpected consequences: for example, if you mount (and therefore re-label) your whole `$HOME/.ssh` directory you will block `sshd` from accessing your keys. This is a reason why you might want to work on a separate copy of the ssh key, so that the original file's labels remain untouched.

* `-v /etc/ansible/hosts:/tmp/inventory` and `-e INVENTORY_FILE=/tmp/inventory` mount the Ansible inventory file into the container as `/tmp/inventory` and set the corresponding environment variable to point at it respectively. The example uses `/etc/ansible/hosts` as the inventory file as this is a default location, but your inventory is likely to be elsewhere so please adjust as needed. Note that depending on the file you point to you might have to handle SELinux labels in a similar way as with the ssh keys, e.g. by adding a `:z` flag to the volume mount, so again you might prefer to copy the inventory to a dedicated location first.

* `-e PLAYBOOK_FILE=playbooks/byo/openshift-checks/certificate_expiry/default.yaml` specifies the playbook to run as a relative path from the top level directory of openshift-ansible.

* `-e OPTS="-v"` and `-t` make the output look nicer: the `default.yaml` playbook does not generate results and runs quietly unless we add the `-v` option to the `ansible-playbook` invocation, and a TTY is allocated via `-t` so that Ansible adds color to the output.

Further usage examples are available in the [examples directory](examples/) with samples of how to use the image from within OpenShift.

Additional usage information for images built from `playbook2image` like this one can be found in the [playbook2image examples](https://github.com/openshift/playbook2image/tree/master/examples).

## Running openshift-ansible as a System Container

Building the System Container: See the [BUILD.md](BUILD.md).

Copy ssh public key of the host machine to master and nodes machines in the cluster.

If the inventory file needs additional files then it can use the path `/var/lib/openshift-installer` in the container as it is bind mounted from the host (controllable with `VAR_LIB_OPENSHIFT_INSTALLER`).

Run the ansible system container:

```sh
atomic install --system --set INVENTORY_FILE=$(pwd)/inventory.origin openshift/origin-ansible
systemctl start origin-ansible
```

The `INVENTORY_FILE` variable says to the installer what inventory file on the host will be bind mounted inside the container.  In the example above, a file called `inventory.origin` in the current directory is used as the inventory file for the installer.

And to finally cleanup the container:

```
atomic uninstall origin-ansible
```
