## Cisco ACI

Install Cisco ACI CNI plugin

## Requirements

* Ansible 2.2
* Centos/ RHEL
* Generate deployment file using cisco aci acc-provision tool and copy to first master node. 
  Refer to https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/kb/b_Cisco_ACI_and_OpenShift_Integration.html


## Key Ansible inventory configuration parameters

* ``openshift_use_aci=True``
* ``openshift_use_openshift_sdn=False``
* ``os_sdn_network_plugin_name='cni'``
* ``aci_deployment_yaml_file=<deployment file path>``


## Overrding master-config parameters

* The external IP used for the LoadBalancer service type is automatically chosen from the subnet pool specified in the ingressIPNetworkCIDR configuration in the /etc/origin/master/master-config.yaml file. This subnet should match the extern_dynamic property configured in the input file provided to acc_provision script. If a specific IP is desired from this subnet pool, it can be assigned to the "loadBalancerIP" property in the LoadBalancer service spec. For more details refer to OpenShift documentation here:
  https://docs.openshift.com/container-platform/3.9/admin_guide/tcp_ingress_external_ports.html#unique-external-ips-ingress-traffic-configure-cluster
