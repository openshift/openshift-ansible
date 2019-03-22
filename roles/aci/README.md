## Cisco ACI

Install Cisco ACI CNI plugin

## Requirements

* Generate deployment file using cisco aci acc-provision tool and copy to first master node. 
  Refer to https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/kb/b_Cisco_ACI_and_OpenShift_Integration.html


## Key Ansible inventory configuration parameters

* ``openshift_use_aci=True``
* ``openshift_use_openshift_sdn=False``
* ``os_sdn_network_plugin_name='cni'``
* ``aci_deployment_yaml_file=<deployment file path>``
