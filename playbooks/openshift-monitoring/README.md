# OpenShift Monitoring

This playbook installs the OpenShift Monitoring stack.

## GCP Development

1. [Launch a GCP cluster](https://github.com/openshift/release/tree/master/cluster/test-deploy).

2. Hack on the installer locally.

3. Make changes, and then build a new openshift-ansible image.

```shell
# in openshift-ansible
docker build -f images/installer/Dockerfile -t openshift-ansible .
```

4. Run the openshift-monitoring GCP installer against the cluster.

```shell
# in test-deploy
make WHAT=dmacedev OPENSHIFT_ANSIBLE_IMAGE=openshift-ansible sh

# in the resulting container shell
ansible-playbook playbooks/openshift-monitoring/install-gcp.yml
```
