# Containerized openshift-ansible to run playbooks

The [Dockerfile](Dockerfile) in this repository uses the [playbook2image](https://github.com/aweiteka/playbook2image) source-to-image base image to containerize `openshift-ansible`. The resulting image can run any of the provided playbooks.

**Note**: at this time there are known issues that prevent to run this image for installation/upgrade purposes from within one of the hosts that is also an installation target at the same time: if the playbook you want to run attempts to manage the docker daemon and restart it (like install/upgrade playbooks do) this would kill the container itself during its operation.

## Build

To build a container image of `openshift-ansible`:

1. Using standalone **Docker**:

        cd openshift-ansible
        docker build -t openshift-ansible .

1. Using an **OpenShift** build:

        oc new-build docker.io/aweiteka/playbook2image~https://github.com/openshift/openshift-ansible
        oc describe imagestream openshift-ansible

## Usage

The base image provides several options to control the behaviour of the containers. For more details on these options see the [playbook2image](https://github.com/aweiteka/playbook2image) documentation.

At the very least, when running a container using an image built this way you must specify:

1. The **playbook** to run. This is set using the `PLAYBOOK_FILE` environment variable.
1. An **inventory** file. This can be mounted inside the container as a volume and specified with the `INVENTORY_FILE` environment variable. Alternatively you can serve the inventory file from a web server and use the `INVENTORY_URL` environment variable to fetch it.
1. **ssh keys** so that Ansible can reach your hosts. These should be mounted as a volume under `/opt/app-root/src/.ssh`

Here is an example of how to run a containerized `openshift-ansible` playbook that will check the expiration dates of OpenShift's internal certificates using the [`openshift_certificate_expiry` role](../../roles/openshift_certificate_expiry). The inventory and ssh keys are mounted as volumes (the latter requires setting the uid in the container and SELinux label in the key file via `:Z` so they can be accessed) and the `PLAYBOOK_FILE` environment variable is set to point to an example certificate check playbook that is already part of the image:

    docker run -u `id -u` \
           -v $HOME/.ssh/id_rsa:/opt/app-root/src/.ssh/id_rsa:Z \
           -v /etc/ansible/hosts:/tmp/inventory \
           -e INVENTORY_FILE=/tmp/inventory \
           -e OPTS="-v" \
           -e PLAYBOOK_FILE=playbooks/certificate_expiry/default.yaml \
           openshift-ansible

The [playbook2image examples](https://github.com/aweiteka/playbook2image/tree/master/examples) provide additional information on how to use a built image.
