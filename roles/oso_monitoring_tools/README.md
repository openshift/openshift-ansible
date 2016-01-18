Role Name
=========

This role will install the Openshift Monitoring Utilities

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

osomt_zagg_client_config

from vars/main.yml:

osomt_zagg_client_config:
  host:
    name: "{{ osomt_host_name }}"
  zagg:
    url: "{{ osomt_zagg_url }}"
    user: "{{ osomt_zagg_user }}"
    pass: "{{ osomt_zagg_password }}"
    ssl_verify: "{{ osomt_zagg_ssl_verify }}"
    verbose: "{{ osomt_zagg_verbose }}"
    debug: "{{ osomt_zagg_debug }}"

Dependencies
------------

None

Example Playbook
----------------

- role: "oso_monitoring_tools"
  osomt_host_name: hostname
  osomt_zagg_url: http://path.to/zagg_web
  osomt_zagg_user: admin
  osomt_zagg_password: password
  osomt_zagg_ssl_verify: True
  osomt_zagg_verbose: False
  osomt_zagg_debug: False

License
-------

BSD

Author Information
------------------

Openshift Operations
