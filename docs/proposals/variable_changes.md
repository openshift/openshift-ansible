# Goal
Give users the ability to create a deterministic inventory

By this I mean, anything that is placed in the inventory with regards to role
and play behavior is honored and not overridden by our plays, whenever possible.

inventory group_vars and host_vars are implied when I say "inventory variables"

This allows the consumption of roles outside of using any one specific play,
where practical.

# Current Situation

First, openshift.common.use_calico is set.  This is created from the inventory
variable "openshift_use_calico" by openshift_facts

So, anywhere you see openshift.common.use_calico, it is really just a 1 to 1 reference
to openshift_use_calico, which the user sets in the inventory, default value of false.

Needless to say, this depends on openshift_facts being available.  It also
depends on ensure that a role or play has called openshift_facts to set
the values up.

```yaml
# roles/openshift_common/tasks/main.yml
...
- name: Set common Cluster facts
  openshift_facts:
    role: common
    local_facts:
      install_examples: "{{ openshift_install_examples | default(True) }}"
      use_openshift_sdn: "{{ openshift_use_openshift_sdn | default(None) }}"
      sdn_network_plugin_name: "{{ os_sdn_network_plugin_name | default(None) }}"
      use_flannel: "{{ openshift_use_flannel | default(None) }}"
      use_calico: "{{openshift_use_calico | default(None) }}"
...
```

Next, here's where we call openshift_hosted.  Currently, this play depends on
openshift_facts having been run.

What we have now:
```sh
r_openshift_hosted_use_calico == openshift.common.use_calico ==   openshift_use_calico
```

```yaml
# playbooks/common/openshift-cluster/openshift_hosted.yml

- name: Create Hosted Resources
  hosts: oo_first_master
  tags:
  - hosted
  pre_tasks:
  - set_fact:
      openshift_hosted_router_registryurl: "{{ hostvars[groups.oo_first_master.0].openshift.master.registry_url }}"
      openshift_hosted_registry_registryurl: "{{ hostvars[groups.oo_first_master.0].openshift.master.registry_url }}"
    when: "'master' in hostvars[groups.oo_first_master.0].openshift and 'registry_url' in hostvars[groups.oo_first_master.0].openshift.master"
  - set_fact:
      logging_hostname: "{{ openshift_hosted_logging_hostname | default('kibana.' ~ (openshift_master_default_subdomain | default('router.default.svc.cluster.local', true))) }}"
      logging_ops_hostname: "{{ openshift_hosted_logging_ops_hostname | default('kibana-ops.' ~ (openshift_master_default_subdomain | default('router.default.svc.cluster.local', true))) }}"
      logging_master_public_url: "{{ openshift_hosted_logging_master_public_url | default(openshift.master.public_api_url) }}"
      logging_elasticsearch_cluster_size: "{{ openshift_hosted_logging_elasticsearch_cluster_size | default(1) }}"
      logging_elasticsearch_ops_cluster_size: "{{ openshift_hosted_logging_elasticsearch_ops_cluster_size | default(1) }}"
  roles:
  - role: openshift_default_storage_class
    when: openshift_cloudprovider_kind is defined and (openshift_cloudprovider_kind == 'aws' or openshift_cloudprovider_kind == 'gce')
  - role: openshift_hosted
    r_openshift_hosted_use_calico: "{{ openshift.common.use_calico | default(false) | bool }}"

    ## Mike comment:  Ironically, we're defaulting this to false in the play
    ## because we either don't trust openshift_facts, or it's just not clear.
...
```

We include this openshift.common.use_calico variable in a variety of plays and roles,
sometimes directly, sometimes indirectly.

Here's an example where we're consuming this directly inside a role, without a
corresponding 'role variable'

```yaml
# roles/openshift_node/defaults/main.yml
...
r_openshift_node_os_firewall_allow:
- service: Kubernetes kubelet
  port: 10250/tcp
- service: http
  port: 80/tcp
- service: https
  port: 443/tcp
- service: OpenShift OVS sdn
  port: 4789/udp
  cond: openshift.common.use_openshift_sdn | default(true) | bool
- service: Calico BGP Port
  port: 179/tcp
  cond: "{{ openshift.common.use_calico | bool }}"
```

This is inconsistent, nobody spent the effort to correct this role, even though
it's a one-line change, or maybe it was just missed.

If it was just missed, why?  Because developers have to grep for 3 different
values, which may be unknown to them unless they spend time detangling the
relationships.  And the case of openshift.common.use_calico is a very generous
example; other variables have more inconsistencies, like cluster_id.

Let's take a look inside the role in question, openshift_hosted

Where is 'r_openshift_hosted_use_calico' defined?

Right here!
```yaml
# entire contents of roles/openshift_hosted/defaults.yml
---
r_openshift_hosted_router_firewall_enabled: "{{ os_firewall_enabled | default(True) }}"
r_openshift_hosted_router_use_firewalld: "{{ os_firewall_use_firewalld | default(False) }}"

r_openshift_hosted_registry_firewall_enabled: "{{ os_firewall_enabled | default(True) }}"
r_openshift_hosted_registry_use_firewalld: "{{ os_firewall_use_firewalld | default(False) }}"

openshift_hosted_router_wait: True
openshift_hosted_registry_wait: True

registry_volume_claim: 'registry-claim'

openshift_hosted_router_edits:
- key: spec.strategy.rollingParams.intervalSeconds
  value: 1
  action: put
- key: spec.strategy.rollingParams.updatePeriodSeconds
  value: 1
  action: put
- key: spec.strategy.activeDeadlineSeconds
  value: 21600
  action: put

openshift_hosted_routers:
- name: router
  replicas: "{{ replicas | default(1) }}"
  namespace: default
  serviceaccount: router
  selector: "{{ openshift_hosted_router_selector | default(None) }}"
  images: "{{ openshift_hosted_router_image | default(None)  }}"
  edits: "{{ openshift_hosted_router_edits }}"
  stats_port: 1936
  ports:
  - 80:80
  - 443:443
  certificate: "{{ openshift_hosted_router_certificate | default({}) }}"

openshift_hosted_router_certificate: {}
openshift_hosted_registry_cert_expire_days: 730
openshift_hosted_router_create_certificate: True

r_openshift_hosted_router_os_firewall_deny: []
r_openshift_hosted_router_os_firewall_allow: []

r_openshift_hosted_registry_os_firewall_deny: []
r_openshift_hosted_registry_os_firewall_allow:
- service: Docker Registry Port
  port: 5000/tcp
cond: "{{ r_openshift_hosted_use_calico }}"
```

Except, it's not defined.  It's only referenced, and no default is provided.
That means this role will fail without providing that value either through
inventory, or as we're currently doing in openshift-ansible, via a play that
provides the value explicitly.

## Impact
This means that this role is 100% dependent on a play passing in a value.
It is currently not sufficient to provide a value in your inventory for this variable
directly because as soon as you run one of the aforementioned plays, the value
the user sets in their inventory is overridden.

If you wanted this role to work both with and without our plays, you'd need to
set the following in your inventory/group_vars:
```yaml
r_openshift_hosted_use_calico: True
openshift_use_calico: True
```
The first line, because that's what the role's expecting, if you don't set it,
the role will fail without our plays.
The second line, because that's what openshift-ansible common expects and
that is the value that is going to be provided to r_openshift_hosted_use_calico
no matter what you set in the inventory for r_openshift_hosted_use_calico.

Should this role fail without this specific variable?  In this case, no it shouldn't.
Installing calico is a special case, not the default case.  The default value
should definitely be false.

Can this role exist in a vacuum?  Possibly, after we remove all the meta
dependencies, this role might have meaningful use outside of openshift-ansible.
I think it's desirable to strive for this goal.  But, in reality, this role
is very much specific to openshift, it's even got openshift in the name.  We
shouldn't try to pretend that this role is completely independent of outside
input from our project.  What we can do, is try to properly define defaults in
the role, and remove as much 'magic' from the variables as we can.

This means *Not* setting variable values in plays, and *Not* using openshift_facts,
wherever possible.

This does not mean we can't share sensible variable names across roles.

## Scenario
I'm running this role outside of openshift-ansible plays, but in cunjunction with
openshift-ansible.  I write a small play to consume this role, outside of
the openshift-ansible tree.

The role fails to run due to this missing variable.  Ok, no problem.  Where is it
defined? This leads down the openshift.common rabbit hole.

# Proposed Solution

- Remove as many variables from plays as practical.
- No dogmatic approach: if we need to set a variable in a play, do it.
- Allow for the use of setting as much in inventory as possible.
 - This is most easily done when removing variables from plays.
 - See 'workaround' section for a nice compromise for other situations.

# Why defining things in inventory/group_vars is superior to plays.

Allowing users to specific variables in inventory is both desired and expected.
We should architect openshift-ansible to allow variables to be honored from inventory.

This will help to aid in reducing the amount of in-tree changes each user of our
project needs to make to get the desired results.  The net effect of this is
smoother upgrades, especially for RPM users, because RPM users aren't going to
get a nice pretty diff when they upgrade packages.

## Scenario
I have two different clusters, completely separate inventories.
If I can place all variables in my inventory/group_vars, that allows the most
reuse of plays and roles.

If I set variables on a per-cluster basis, in plays and include_vars files,
then I must also maintain a separate set of plays per cluster.
If I want to make a change to a play, I have to refactor every cluster's set of
plays.  This reduces overall reusability.

# Workaround
```yaml
# roles/openshift_hosted/defaults/main.yml
---
...
r_openshift_hosted_router_firewall_enabled: "{{ os_firewall_enabled | default(True) }}"
...
```

If you didn't notice earlier, this is currently in master in openshift_hosted/defaults/main.yml

We are performing what I call a 'back-reference'.  Or, a variable that refers to
another variable in the defaults.  This is both clear and useful.

This pattern allows a user to specify r_openshift_hosted_router_firewall_enabled
directly if they wish to affect only this role's behavior; if they wish to
affect the behavior project wide, they can set os_firewall_enabled.

Obviously, we're already consuming 'external variables' inside our roles, albeit
in this case inside role defaults.

In some instances, I'm proposing that it's sane, reasonable, and logical to
cut out this role-specific incarnation of the variable.  This is not always
practical or desirable, but in many (most) cases it is.  At the end of the day,
the end user still has to peak inside role/defaults/main.yml to figure out
how to control the role.

I do agree that the less experienced users may want to just set 'os_firewall_enabled' to false for this role, and not understand the
wide-spread impact of that particular boolean.  This is part of the learning
curve of ansible: if you see a variable that is not namespaced to the role
specifically, you definitely need to grep and see what it's hitting.

Sometimes this overlap is unintentional, those role variables should be fixed.
In the case of os_firewall_enabled, it's likely VERY intentional, and things
won't function correctly if they are set differently across different roles.

## One step further
The above example only allows r_openshift_hosted_router_firewall_enabled to be
set in inventory, it does nothing to prevent our plays from assigning a value
to that variable and not honoring what's in inventory.  For cases where we can't
avoid setting variables in plays (which should be very few cases IMO),
we can do the following:

```yaml
# roles/openshift_hosted/defaults/main.yml
---
r_openshift_hosted_router_firewall_enabled_default: "{{ os_firewall_enabled | default(True) }}"
r_openshift_hosted_router_firewall_enabled: "{{ r_openshift_hosted_router_firewall_enabled_default }}"

```
And in the plays:
```yaml
- role:
  r_openshift_hosted_router_firewall_enabled_default: XXX
```

And in the role tasks:
```yaml
- command: "echo {{ r_openshift_hosted_router_firewall_enabled }}"
```
This allows openshift-ansible to make sound decisions where necessary, and still allow
users to have a deterministic inventory.

Obviously, this case is more verbose, and may be a little more intimidating for
less experienced users to grok.  But, the end state, respecting the deterministic
variables provided in inventory/group_vars, it's worth the effort.

# A word on variable scope

> Variable Precedence: Where Should I Put A Variable?

> A lot of folks may ask about how variables override another. Ultimately it’s Ansible’s philosophy that it’s better you know where to put a variable, and then you have to think about it a lot less.

> Avoid defining the variable “x” in 47 places and then ask the question “which x gets used”. Why? Because that’s not Ansible’s Zen philosophy of doing things.

> There is only one Empire State Building. One Mona Lisa, etc. Figure out where to define a variable, and don’t make it complicated.

- http://docs.ansible.com/ansible/latest/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable
