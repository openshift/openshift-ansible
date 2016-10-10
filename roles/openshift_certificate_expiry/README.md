OpenShift Certificate Expiration Checker
========================================

OpenShift certificate expiration checking. Be warned of certificates
expiring within a configurable window of days, and notified of
certificates which have already expired. Certificates examined
include:

* Master/Node Service Certificates
* Router/Registry Service Certificates from etcd secrets
* Master/Node/Router/Registry/Admin `kubeconfig`s
* Etcd certificates

This role pairs well with the redeploy certificates playbook:

* [Redeploying Certificates Documentation](https://docs.openshift.com/container-platform/latest/install_config/redeploying_certificates.html)

Just like the redeploying certificates playbook, this role is intended
to be used with an inventory that is representative of the
cluster. For best results run `ansible-playbook` with the `-v` option.



Role Variables
--------------

Core variables in this role:

| Name                                                  | Default value                  | Description                                                           |
|-------------------------------------------------------|--------------------------------|-----------------------------------------------------------------------|
| `openshift_certificate_expiry_config_base`            | `/etc/origin`                  | Base openshift config directory                                       |
| `openshift_certificate_expiry_warning_days`           | `30`                           | Flag certificates which will expire in this many days from now        |
| `openshift_certificate_expiry_show_all`               | `no`                           | Include healthy (non-expired and non-warning) certificates in results |

Optional report/result saving variables in this role:

| Name                                                  | Default value                  | Description                                                           |
|-------------------------------------------------------|--------------------------------|-----------------------------------------------------------------------|
| `openshift_certificate_expiry_generate_html_report`   | `no`                           | Generate an HTML report of the expiry check results                   |
| `openshift_certificate_expiry_html_report_path`       | `/tmp/cert-expiry-report.html` | The full path to save the HTML report as                              |
| `openshift_certificate_expiry_save_json_results`      | `no`                           | Save expiry check results as a json file                              |
| `openshift_certificate_expiry_json_results_path`      | `/tmp/cert-expiry-report.json` | The full path to save the json report as                              |


Example Playbook
----------------

Default behavior:

```yaml
---
- name: Check cert expirys
  hosts: nodes:masters:etcd
  become: yes
  gather_facts: no
  roles:
    - role: openshift_certificate_expiry
```

Generate HTML and JSON artifacts in their default paths:

```yaml
---
- name: Check cert expirys
  hosts: nodes:masters:etcd
  become: yes
  gather_facts: no
  vars:
    openshift_certificate_expiry_generate_html_report: yes
    openshift_certificate_expiry_save_json_results: yes
  roles:
    - role: openshift_certificate_expiry
```

Change the expiration warning window to 1500 days (good for testing
the module out):

```yaml
---
- name: Check cert expirys
  hosts: nodes:masters:etcd
  become: yes
  gather_facts: no
  vars:
    openshift_certificate_expiry_warning_days: 1500
  roles:
    - role: openshift_certificate_expiry
```

Change the expiration warning window to 1500 days (good for testing
the module out) and save the results as a JSON file:

```yaml
---
- name: Check cert expirys
  hosts: nodes:masters:etcd
  become: yes
  gather_facts: no
  vars:
    openshift_certificate_expiry_warning_days: 1500
    openshift_certificate_expiry_save_json_results: yes
  roles:
    - role: openshift_certificate_expiry
```


JSON Output
-----------

There are two top-level keys in the saved JSON results, `data` and
`summary`.

The `data` key is a hash where the keys are the names of each host
examined and the values are the check results for each respective
host.

The `summary` key is a hash that summarizes the number of certificates
expiring within the configured warning window and the number of
already expired certificates.

The example below is abbreviated to save space:

```json
{
    "data": {
        "192.168.124.148": {
            "etcd": [
                {
                    "cert_cn": "CN:etcd-signer@1474563722",
                    "days_remaining": 350,
                    "expiry": "2017-09-22 17:02:25",
                    "health": "warning",
                    "path": "/etc/etcd/ca.crt"
                },
            ],
            "kubeconfigs": [
                {
                    "cert_cn": "O:system:nodes, CN:system:node:m01.example.com",
                    "days_remaining": 715,
                    "expiry": "2018-09-22 17:08:57",
                    "health": "warning",
                    "path": "/etc/origin/node/system:node:m01.example.com.kubeconfig"
                },
                {
                    "cert_cn": "O:system:cluster-admins, CN:system:admin",
                    "days_remaining": 715,
                    "expiry": "2018-09-22 17:04:40",
                    "health": "warning",
                    "path": "/etc/origin/master/admin.kubeconfig"
                }
            ],
            "meta": {
                "checked_at_time": "2016-10-07 15:26:47.608192",
                "show_all": "True",
                "warn_before_date": "2020-11-15 15:26:47.608192",
                "warning_days": 1500
            },
            "ocp_certs": [
                {
                    "cert_cn": "CN:172.30.0.1, DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local, DNS:m01.example.com, DNS:openshift, DNS:openshift.default, DNS:openshift.default.svc, DNS:openshift.default.svc.cluster.local, DNS:172.30.0.1, DNS:192.168.124.148, IP Address:172.30.0.1, IP Address:192.168.124.148",
                    "days_remaining": 715,
                    "expiry": "2018-09-22 17:04:39",
                    "health": "warning",
                    "path": "/etc/origin/master/master.server.crt"
                },
                {
                    "cert_cn": "CN:openshift-signer@1474563878",
                    "days_remaining": 1810,
                    "expiry": "2021-09-21 17:04:38",
                    "health": "ok",
                    "path": "/etc/origin/node/ca.crt"
                }
            ],
            "registry": [
                {
                    "cert_cn": "CN:172.30.101.81, DNS:docker-registry-default.router.default.svc.cluster.local, DNS:docker-registry.default.svc.cluster.local, DNS:172.30.101.81, IP Address:172.30.101.81",
                    "days_remaining": 728,
                    "expiry": "2018-10-05 18:54:29",
                    "health": "warning",
                    "path": "/api/v1/namespaces/default/secrets/registry-certificates"
                }
            ],
            "router": [
                {
                    "cert_cn": "CN:router.default.svc, DNS:router.default.svc, DNS:router.default.svc.cluster.local",
                    "days_remaining": 715,
                    "expiry": "2018-09-22 17:48:23",
                    "health": "warning",
                    "path": "/api/v1/namespaces/default/secrets/router-certs"
                }
            ]
        }
    },
    "summary": {
        "warning": 6,
        "expired": 0
    }
}
```

The `summary` from the json data can be easily checked for
warnings/expirations using a variety of command-line tools.

For exampe, using `grep` we can look for the word `summary` and print
out the 2 lines **after** the match (`-A2`):

```
$ grep -A2 summary /tmp/cert-expiry-report.json
    "summary": {
        "warning": 16,
        "expired": 0
```

If available, the [jq](https://stedolan.github.io/jq/) tool can also
be used to pick out specific values. Example 1 and 2 below show how to
select just one value, either `warning` or `expired`. Example 3 shows
how to select both values at once:

```
$ jq '.summary.warning' /tmp/cert-expiry-report.json
16
$ jq '.summary.expired' /tmp/cert-expiry-report.json
0
$ jq '.summary.warning,.summary.expired' /tmp/cert-expiry-report.json
16
0
```


Requirements
------------

* None


Dependencies
------------

* None


License
-------

Apache License, Version 2.0

Author Information
------------------

Tim Bielawa (tbielawa@redhat.com)
