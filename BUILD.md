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

To build a container image of `openshift-ansible` using standalone **Docker**:

        cd openshift-ansible
        docker build -t openshift/openshift-ansible .

Alternatively this can be built using on **OpenShift** using a [build and image stream](https://docs.openshift.org/latest/architecture/core_concepts/builds_and_image_streams.html) with this command:

        oc new-build docker.io/aweiteka/playbook2image~https://github.com/openshift/openshift-ansible

The progress of the build can be monitored with:

        oc logs -f bc/openshift-ansible

Once built, the image will be visible in the Image Stream created by the same command:

        oc describe imagestream openshift-ansible
