#!/bin/bash

set -euxo pipefail

# DNS
(
dns_zone="{{ dns_managed_zone | default(openshift_gcp_prefix + 'managed-zone') }}"
if gcloud --project "{{ openshift_gcp_project }}" dns managed-zones describe "${dns_zone}" &>/dev/null; then
    # Retry DNS changes until they succeed since this may be a shared resource
    while true; do
        dns="${TMPDIR:-/tmp}/dns.yaml"
        rm -f "${dns}"

        # export all dns records that match into a zone format, and turn each line into a set of args for
        # record-sets transaction.
        gcloud dns record-sets export --project "{{ openshift_gcp_project }}" -z "${dns_zone}" --zone-file-format "${dns}"

        # Remove etcd discovery record
        ETCD_DNS_NAME="_etcd-server-ssl._tcp.{{ lookup('env', 'INSTANCE_PREFIX') | mandatory }}.{{ public_hosted_zone }}."
        grep -F -e "${ETCD_DNS_NAME}" "${dns}" | awk '{ print "--name", $1, "--ttl", $2, "--type", $4, "\x27"$5" "$6" "$7" "$8"\x27"; }'  >> "${dns}.input" || true

        if [ -s "${dns}.input" ]; then
            rm -f "${dns}"
            gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
            cat "${dns}.input" | xargs -L1 gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file="${dns}" remove -z "${dns_zone}"

            # Commit all DNS changes, retrying if preconditions are not met
            if ! out="$( gcloud --project "{{ openshift_gcp_project }}" dns record-sets transaction --transaction-file=$dns execute -z "${dns_zone}" 2>&1 )"; then
                rc=$?
                if [[ "${out}" == *"HTTPError 412: Precondition not met"* ]]; then
                    continue
                fi
                exit $rc
            fi
        fi
        rm "${dns}.input"
        break
    done
fi
) &

for i in `jobs -p`; do wait $i; done
