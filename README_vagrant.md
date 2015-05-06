Requirements
------------
- vagrant (tested against version 1.7.2)
- vagrant-hostmaster plugin (tested against version 1.5.0)
- vagrant-libvirt (tested against version 0.0.26)
  - Only required if using libvirt instead of virtualbox

Usage
-----
```
vagrant up --no-provision
vagrant provision
```

Using libvirt:
```
vagrant up --provider=libvirt --no-provision
vagrant provision
```

Environment Variables
---------------------
The following environment variables can be overriden:
- OPENSHIFT_DEPLOYMENT_TYPE (defaults to origin, choices: origin, enterprise, online)
- OPENSHIFT_NUM_NODES (the number of nodes to create, defaults to 2)
