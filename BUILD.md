# openshift-ansible build instructions

## Build openshift-ansible RPMs

We use tito to make building and tracking revisions easy.

For more information on tito, please see the [Tito home page](https://github.com/dgoodwin/tito "Tito home page").

- Change into openshift-ansible
```
cd openshift-ansible
```
- Build a test package (no tagging needed)
```
tito build --test --rpm
```
- Tag a new build (bumps version number and adds log entries)
```
tito tag
```
- Follow the on screen tito instructions to push the tags
- Build a new package based on the latest tag information
```
tito build --rpm
```

## Build an openshift-ansible container image

**NOTE**: the examples below use "openshift-ansible" as the name of the image to build for simplicity and illustration purposes, and also to prevent potential confusion between custom built images and official releases. See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for details about the released container images for openshift-ansible.

To build a container image of `openshift-ansible` using standalone **Docker**:

        cd openshift-ansible
        docker build -f images/installer/Dockerfile -t openshift-ansible .

## Build the Atomic System Container

A system container runs using runC instead of Docker and it is managed
by the [atomic](https://github.com/projectatomic/atomic/) tool.  As it
doesn't require Docker to run, the installer can run on a node of the
cluster without interfering with the Docker daemon that is configured
by the installer itself.

The first step is to build the [container image](#build-an-openshift-ansible-container-image)
as described before.  The container image already contains all the
required files to run as a system container.

Once the container image is built, we can import it into the OSTree
storage:

```
atomic pull --storage ostree docker:openshift-ansible:latest
```
