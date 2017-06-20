OpenShift Prometheus
====================

OpenShift Prometheus Installation

Requirements
------------


Role Variables
--------------

For default values, see [`defaults/main.yaml`](defaults/main.yaml).

- `openshift_prometheus_state`: present - install/update. absent - uninstall.

- `openshift_prometheus_namespace`: project (i.e. namespace) where the components will be
  deployed.

- `openshift_prometheus_replicas`: The number of replicas for prometheus deployment.

- `openshift_prometheus_node_selector`: Selector for the nodes prometheus will be deployed on.

- `openshift_prometheus_image_<COMPONENT>`: specify image for the component 

## Storage related variables
Each prometheus component (prometheus, alertmanager, alert-buffer, oauth-proxy) can set pv claim by setting corresponding role variable:
```
openshift_prometheus_<COMPONENT>_storage_type: <VALUE>
openshift_prometheus_<COMPONENT>_pvc_(name|size|access_modes|pv_selector): <VALUE>
```
e.g
```
openshift_prometheus_storage_type: pvc
openshift_prometheus_alertmanager_pvc_name: alertmanager
openshift_prometheus_alertbuffer_pvc_size: 10G
openshift_prometheus_pvc_access_modes: [ReadWriteOnce]
```

## Additional Alert Rules file variable
An external file with alert rules can be added by setting path to additional rules variable: 
```
openshift_prometheus_additional_rules_file: <PATH> 
```

File content should be in prometheus alert rules format.
Following example sets rule to fire an alert when one of the cluster nodes is down:

```
groups:
- name: example-rules
  interval: 30s # defaults to global interval
  rules:
  - alert: Node Down
    expr: up{job="kubernetes-nodes"} == 0
    annotations:
      miqTarget: "ContainerNode"
      severity: "HIGH"
      message: "{{ '{{' }}{{ '$labels.instance' }}{{ '}}' }} is down"
```


## Additional variables to control resource limits
Each prometheus component (prometheus, alertmanager, alert-buffer, oauth-proxy) can specify a cpu and memory limits and requests by setting
the corresponding role variable:
```
openshift_prometheus_<COMPONENT>_(limits|requests)_(memory|cpu): <VALUE>
```
e.g
```
openshift_prometheus_alertmanager_limits_memory: 1Gi
openshift_prometheus_oath_proxy_requests_cpu: 100
```

Dependencies
------------

openshift_facts


Example Playbook
----------------

```
- name: Configure openshift-prometheus
  hosts: oo_first_master
  roles:
  - role: openshift_prometheus
```

License
-------

Apache License, Version 2.0

