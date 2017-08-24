# Repository structure

### Ansible

```
.
├── inventory           Contains dynamic inventory scripts, and examples of
│                       Ansible inventories.
├── library             Contains Python modules used by the playbooks.
├── playbooks           Contains Ansible playbooks targeting multiple use cases.
└── roles               Contains Ansible roles, units of shared behavior among
                        playbooks.
```

#### Ansible plugins

These are plugins used in playbooks and roles:

```
.
├── ansible-profile
├── callback_plugins
├── filter_plugins
└── lookup_plugins
```

### Scripts

```
.
└── utils               Contains the `atomic-openshift-installer` command, an
                        interactive CLI utility to install OpenShift across a
                        set of hosts.
```

### Documentation

```
.
└── docs                Contains documentation for this repository.
```

### Tests

```
.
└── test                Contains tests.
```

### CI

These files are used by [PAPR](https://github.com/projectatomic/papr),
It is very similar in workflow to Travis, with the test
environment and test scripts defined in a YAML file.

```
.
├── .papr.yml
├── .papr.sh
└── .papr.inventory
```
