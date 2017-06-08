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

### Building on OpenShift

To build an openshift-ansible image using an **OpenShift** [build and image stream](https://docs.openshift.org/latest/architecture/core_concepts/builds_and_image_streams.html) the straightforward command would be:

        oc new-build registry.centos.org/openshift/playbook2image~https://github.com/openshift/openshift-ansible

However: because the `Dockerfile` for this repository is not in the top level directory, and because we can't change the build context to the `images/installer` path as it would cause the build to fail, the `oc new-app` command above will create a build configuration using the *source to image* strategy, which is the default approach of the [playbook2image](https://github.com/openshift/playbook2image) base image. This does build an image successfully, but unfortunately the resulting image will be missing some customizations that are handled by the [Dockerfile](images/installer/Dockerfile) in this repo.

At the time of this writing there is no straightforward option to [set the dockerfilePath](https://docs.openshift.org/latest/dev_guide/builds/build_strategies.html#dockerfile-path) of a `docker` build strategy with `oc new-build`. The alternatives to achieve this are:

- Use the simple `oc new-build` command above to generate the BuildConfig and ImageStream objects, and then manually edit the generated build configuration to change its strategy to `dockerStrategy` and set `dockerfilePath` to `images/installer/Dockerfile`.

- Download and pass the `Dockerfile` to `oc new-build` with the `-D` option:

```
curl -s https://raw.githubusercontent.com/openshift/openshift-ansible/master/images/installer/Dockerfile |
     oc new-build -D - \
        --docker-image=registry.centos.org/openshift/playbook2image \
	    https://github.com/openshift/openshift-ansible
```

Once a build is started, the progress of the build can be monitored with:

        oc logs -f bc/openshift-ansible

Once built, the image will be visible in the Image Stream created by `oc new-app`:

        oc describe imagestream openshift-ansible

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
