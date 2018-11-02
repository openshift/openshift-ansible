#!/bin/bash

set -euxo pipefail

dns_zone="{{ dns_managed_zone | default(openshift_gcp_prefix + 'managed-zone') }}"
# configure DNS
(
# Retry DNS changes until they succeed since this may be a shared resource
while true; do
    dns="${TMPDIR:-/tmp}/dns.yaml"
    rm -f $dns

    # DNS records for etcd servers
    {% for master in master_instances %}
      MASTER_DNS_NAME="{{ openshift_gcp_prefix }}etcd-{{ loop.index-1 }}.{{ public_hosted_zone }}."
      IP="{{ master.networkInterfaces[0].networkIP }}"
      if ! gcloud --project "{{ openshift_gcp_project }}" dns record-sets list -z "${dns_zone}" --name "{{ openshift_master_cluster_hostname }}" 2>/dev/null | grep -q "${MASTER_DNS_NAME}"; then
          if [[ ! -f $dns ]]; then
              gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
          fi
          gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl {{ openshift_gcp_master_dns_ttl }} --name "${MASTER_DNS_NAME}" --type A "$IP"
      else
          echo "DNS record for '${MASTER_DNS_NAME}' already exists"
      fi
    {% endfor %}

    # DNS records for etcd discovery
    ETCD_DNS_NAME="_etcd-server-ssl._tcp.{{ lookup('env', 'INSTANCE_PREFIX') | mandatory }}.{{ public_hosted_zone }}."
    if ! gcloud --project "{{ openshift_gcp_project }}" dns record-sets list -z "${dns_zone}" --name "${ETCD_DNS_NAME}" 2>/dev/null | grep -q "${ETCD_DNS_NAME}"; then
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl {{ openshift_gcp_master_dns_ttl }} --name "${ETCD_DNS_NAME}" --type SRV {{ etcd_discovery_targets }}
    else
        echo "DNS record for '${ETCD_DNS_NAME}' already exists"
    fi

    # Roundrobin masters and bootstrap
    if ! gcloud --project "{{ openshift_gcp_project }}" dns record-sets list -z "${dns_zone}" --name "{{ openshift_master_cluster_public_hostname }}" 2>/dev/null | grep -q "{{ openshift_master_cluster_public_hostname }}"; then
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl {{ openshift_gcp_master_dns_ttl }} --name "{{ openshift_master_cluster_public_hostname }}" --type A {{ bootstrap_instance.networkInterfaces[0].accessConfigs[0].natIP }} {{ master_external_ips }}
    else
        echo "DNS record for '{{ openshift_master_cluster_public_hostname }}' already exists"
    fi

    # Commit all DNS changes, retrying if preconditions are not met
    if [[ -f $dns ]]; then
        if ! out="$( gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns execute -z "${dns_zone}" 2>&1 )"; then
            rc=$?
            if [[ "${out}" == *"HTTPError 412: Precondition not met"* ]]; then
                continue
            fi
            exit $rc
        fi
    fi
    break
done
) &

# Add groups to target pools
# Add bootstrap
# gcloud --project "{{ openshift_gcp_project }}" compute instance-groups managed set-target-pools "{{ openshift_gcp_prefix }}ig-b" --target-pools "{{ openshift_gcp_prefix }}master-lb-pool" --zone "{{ openshift_gcp_zone }}"

# # Add masters
# gcloud --project "{{ openshift_gcp_project }}" compute instance-groups managed set-target-pools "{{ openshift_gcp_prefix }}ig-m" --target-pools "{{ openshift_gcp_prefix }}master-lb-pool" --zone "{{ openshift_gcp_zone }}"

# wait until all node groups are stable
{% for node_group in openshift_gcp_node_group_config %}
{% if node_group.wait_for_stable | default(False) %}
# wait for stable {{ node_group.name }}
( gcloud --project "{{ openshift_gcp_project }}" compute instance-groups managed wait-until-stable "{{ openshift_gcp_prefix }}ig-{{ node_group.suffix }}" --zone "{{ openshift_gcp_zone }}" --timeout=600 ) &
{% else %}
# not waiting for {{ node_group.name }} due to bootstrapping
{% endif %}
{% endfor %}

for i in `jobs -p`; do wait $i; done
