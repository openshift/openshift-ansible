# openshift-ansible usage examples

The primary use of `openshift-ansible` is to install, configure and upgrade OpenShift clusters.

This is typically done by direct invocation of Ansible tools like `ansible-playbook`. This use case is covered in detail in the [OpenShift advanced installation documentation](https://docs.okd.io/latest/install_config/install/advanced_install.html)

For OpenShift Container Platform there's also an installation utility that wraps `openshift-ansible`. This usage case is covered in the [Quick Installation](https://docs.openshift.com/container-platform/latest/install_config/install/quick_install.html) section of the documentation.

The usage examples below cover use cases other than install/configure/upgrade.

## Container image

The examples below run [openshift-ansible in a container](../README_CONTAINER_IMAGE.md) to perform certificate expiration checks on an OpenShift cluster from pods running on the cluster itself.

You can find more details about the certificate expiration check roles and example playbooks in [the openshift_certificate_expiry role's README](../roles/openshift_certificate_expiry/README.md).

### Job to upload certificate expiration reports

The example `Job` in [certificate-check-upload.yaml](certificate-check-upload.yaml) executes a [Job](https://docs.okd.io/latest/dev_guide/jobs.html) that checks the expiration dates of the internal certificates of the cluster and uploads HTML and JSON reports to `/etc/origin/certificate_expiration_report` in the masters.

This example uses the [`easy-mode-upload.yaml`](../playbooks/openshift-checks/certificate_expiry/easy-mode-upload.yaml) example playbook, which generates reports and uploads them to the masters. The playbook can be customized via environment variables to control the length of the warning period (`CERT_EXPIRY_WARN_DAYS`) and the location in the masters where the reports are uploaded (`COPY_TO_PATH`).

The job expects the inventory to be provided via the *hosts* key of a [ConfigMap](https://docs.okd.io/latest/dev_guide/configmaps.html) named *inventory*, and the passwordless ssh key that allows connecting to the hosts to be availalbe as *ssh-privatekey* from a [Secret](https://docs.okd.io/latest/dev_guide/secrets.html) named *sshkey*, so these are created first:

    oc new-project certcheck
    oc create configmap inventory --from-file=hosts=/etc/ansible/hosts
    oc create secret generic sshkey \
      --from-file=ssh-privatekey=$HOME/.ssh/id_rsa \
      --type=kubernetes.io/ssh-auth

Note that `inventory`, `hosts`, `sshkey` and `ssh-privatekey` are referenced by name from the provided example Job definition. If you use different names for the objects/attributes you will have to adjust the Job accordingly.

To create the Job:

    oc create -f examples/certificate-check-upload.yaml

### Scheduled job for certificate expiration report upload

The example `CronJob` in [scheduled-certcheck-upload.yaml](scheduled-certcheck-upload.yaml) does the same as the `Job` example above, but it is scheduled to automatically run every first day of the month (see the `spec.schedule` value in the example).

The job definition is the same and it expects the same configuration: we provide the inventory and ssh key via a ConfigMap and a Secret respectively:

    oc new-project certcheck
    oc create configmap inventory --from-file=hosts=/etc/ansible/hosts
    oc create secret generic sshkey \
      --from-file=ssh-privatekey=$HOME/.ssh/id_rsa \
      --type=kubernetes.io/ssh-auth

And then we create the CronJob:

    oc create -f examples/scheduled-certcheck-upload.yaml

### Job and CronJob to check certificates using volumes

There are two additional examples:

 - A `Job` [certificate-check-volume.yaml](certificate-check-volume.yaml)
 - A `CronJob` [scheduled-certcheck-upload.yaml](scheduled-certcheck-upload.yaml)

These perform the same work as the two examples above, but instead of uploading the generated reports to the masters they store them in a custom path within the container that is expected to be backed by a [PersistentVolumeClaim](https://docs.okd.io/latest/dev_guide/persistent_volumes.html), so that the reports are actually written to storage external to the container.

These examples assume that there is an existing `PersistentVolumeClaim` called `certcheck-reports` and they use the  [`html_and_json_timestamp.yaml`](../playbooks/openshift-checks/certificate_expiry/html_and_json_timestamp.yaml) example playbook to write timestamped reports into it.

You can later access the reports from another pod that mounts the same volume, or externally via direct access to the backend storage behind the matching `PersistentVolume`.

To run these examples we prepare the inventory and ssh keys as in the other examples:

    oc new-project certcheck
    oc create configmap inventory --from-file=hosts=/etc/ansible/hosts
    oc create secret generic sshkey \
      --from-file=ssh-privatekey=$HOME/.ssh/id_rsa \
      --type=kubernetes.io/ssh-auth

Additionally we allocate a `PersistentVolumeClaim` to store the reports:

    oc create -f - <<PVC
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: certcheck-reports
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
    PVC

With that we can run the `Job` once:

    oc create -f examples/certificate-check-volume.yaml

or schedule it to run periodically as a `CronJob`:

    oc create -f examples/scheduled-certcheck-volume.yaml
