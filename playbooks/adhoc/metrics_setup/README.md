## Playbook for adding [Metrics](https://github.com/openshift/origin-metrics) to Openshift

See OSE Ansible [readme](https://github.com/openshift/openshift-ansible/blob/master/README_OSE.md) for general install instructions.  Playbook has been tested on OSE 3.1/RHEL7.2 cluster


Add the following vars to `[OSEv3:vars]` section of your inventory file
```
[OSEv3:vars]
# Enable cluster metrics
use_cluster_metrics=true
metrics_external_service=< external service name for metrics >
metrics_image_prefix=rcm-img-docker01.build.eng.bos.redhat.com:5001/openshift3/
metrics_image_version=3.1.0
```

Run playbook
```
ansible-playbook -i $INVENTORY_FILE playbooks/install.yml
```

## Contact
Email: hawkular-dev@lists.jboss.org

## Credits
Playbook adapted from install shell scripts by Matt Mahoney
