#!/bin/bash

set -euxo pipefail

dns_zone="{{ dns_managed_zone | default(openshift_gcp_prefix + 'managed-zone') }}"
# configure DNS
(
# Retry DNS changes until they succeed since this may be a shared resource
while true; do
    dns="${TMPDIR:-/tmp}/dns.yaml"
    rm -f $dns

    # DNS records for etcd discovery
    ETCD_DNS_NAME="_etcd-server-ssl._tcp.{{ lookup('env', 'INSTANCE_PREFIX') | mandatory }}.{{ public_hosted_zone }}."
    if ! gcloud --project "{{ openshift_gcp_project }}" dns record-sets list -z "${dns_zone}" --name "${ETCD_DNS_NAME}" 2>/dev/null | grep -q "${ETCD_DNS_NAME}"; then
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl {{ openshift_gcp_master_dns_ttl }} --name "${ETCD_DNS_NAME}" --type SRV {% for etcd in etcd_discovery_targets %}'{{ etcd }}' {% endfor %}

    else
        echo "DNS record for '${ETCD_DNS_NAME}' already exists"
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

for i in `jobs -p`; do wait $i; done
