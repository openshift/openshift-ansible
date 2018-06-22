Keepalived
=========

This role installs keepalived and configures it according to the variables you'll pass to the role.

Requirements
------------

No fancy requirements. Only package and file management in the role.

Role Variables
--------------

By default, this role doesn't configure keepalived, it barely installs it. This way keepalived is fully flexible based on what you give as input.
Examples are given in the vars folder. Don't try them immediately, they won't work! (You need to define VIPs, passwords, etc.). The examples are only a source of inspiration.

The main variables are:

* keepalived_instances: This is a mandatory dict. It gathers information about the vips, the prefered state (master/backup), the VRRIP IDs and priorities, the password used for authentication... This is where things like nopreempt are configured. nopreempt allows to stay in backup state (instead of preempting to configured master) on a master return of availability, after its failure. Please check the template for additional settings support, and original keepalived documentation for their configuration.
* keepalived_sync_groups: This is a mandatory dict. It groups items defined in keepalived_instances, and (if desired) allow the configuration of notifications scripts per group of keepalived_instances. Notification scripts are triggered on keepalived's state change and are facultative.
* keepalived_virtual_servers: This is an optional dict. It sets up a virtual server + port and balances traffic over real_servers given in a sub dict. Checkout the _example.yaml files in vars/ to see a sample on how to use this dict. The official documentation for keepalived's virtual_server can be found [here](https://github.com/acassen/keepalived/blob/master/doc/keepalived.conf.SYNOPSIS#L393).
* keepalived_scripts: This is an optional dict where you could have checking scripts that can trigger the notifications scripts.
* keepalived_bind_on_non_local: This variable (defaulted to "False") determines whether the system that host keepalived will allow its apps to bind on non-local addresses. If you set it to true, this allows apps to bind (and start) even if they don't currently have the VIP for example.

Please check the examples for more explanations on how these dicts must be configured.

Other editable variables are listed in the defaults/main.yml. Please read the explanation there if you want to override them.
An example of a notification script is also given, in the files folder.

Antoher good source of informations is the official keepalived [GIT repo](https://github.com/acassen/keepalived) where you can find a fully commented [keepalived.conf](https://github.com/acassen/keepalived/blob/master/doc/keepalived.conf.SYNOPSIS). Also various official samples are [provided](https://github.com/acassen/keepalived/tree/master/doc/samples).

Dependencies
------------

No dependency

Example Playbook
----------------

Here is how you could use the role:

    - hosts: keepalived_hosts[0]
      vars_files:
        - roles/keepalived/tests/keepalived_haproxy_master_example.yml
      roles:
         - keepalived
    - hosts: keepalived_hosts:!keepalived_hosts[0]
      vars_files:
        - roles/keepalived/tests/keepalived_haproxy_backup_example.yml
      roles:
         - keepalived

Or more simply:

    - hosts: keepalived_hosts
      vars_files:
        - roles/keepalived/tests/keepalived_haproxy_combined_example.yml
      roles:
         - keepalived

You could also replace the vars_files by proper group_vars, host_vars.

License
-------

Apache2

Author Information
------------------

Jean-Philippe Evrard


Forked from https://github.com/evrardjp/ansible-keepalived
