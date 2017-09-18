#!/bin/bash

set -euo pipefail

# Create SSH key for GCE
if [ ! -f "{{ gce_ssh_private_key }}" ]; then
    ssh-keygen -t rsa -f "{{ gce_ssh_private_key }}" -C gce-provision-cloud-user -N ''
    ssh-add "{{ gce_ssh_private_key }}" || true
fi

# Check if the ~/.ssh/google_compute_engine.pub key is in the project metadata, and if not, add it there
pub_key=$(cut -d ' ' -f 2 < "{{ gce_ssh_private_key }}.pub")
key_tmp_file='/tmp/ocp-gce-keys'
if ! gcloud --project "{{ gce_project_id }}" compute project-info describe | grep -q "$pub_key"; then
    if gcloud --project "{{ gce_project_id }}" compute project-info describe | grep -q ssh-rsa; then
        gcloud --project "{{ gce_project_id }}" compute project-info describe | grep ssh-rsa | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/value: //' > "$key_tmp_file"
    fi
    echo -n 'cloud-user:' >> "$key_tmp_file"
    cat "{{ gce_ssh_private_key }}.pub" >> "$key_tmp_file"
    gcloud --project "{{ gce_project_id }}" compute project-info add-metadata --metadata-from-file "sshKeys=${key_tmp_file}"
    rm -f "$key_tmp_file"
fi

metadata=""
if [[ -n "{{ provision_gce_startup_script_file }}" ]]; then
    if [[ ! -f "{{ provision_gce_startup_script_file }}" ]]; then
        echo "Startup script file missing at {{ provision_gce_startup_script_file }} from=$(pwd)"
        exit 1
    fi
    metadata+="--metadata-from-file=startup-script={{ provision_gce_startup_script_file }}"
fi
if [[ -n "{{ provision_gce_user_data_file }}" ]]; then
    if [[ ! -f "{{ provision_gce_user_data_file }}" ]]; then
        echo "User data file missing at {{ provision_gce_user_data_file }}"
        exit 1
    fi
    if [[ -n "${metadata}" ]]; then
        metadata+=","
    else
        metadata="--metadata-from-file="
    fi
    metadata+="user-data={{ provision_gce_user_data_file }}"
fi

# Select image or image family
image="{{ provision_gce_registered_image }}"
if ! gcloud --project "{{ gce_project_id }}" compute images describe "${image}" &>/dev/null; then
    if ! gcloud --project "{{ gce_project_id }}" compute images describe-from-family "${image}" &>/dev/null; then
        echo "No compute image or image-family found, create an image named '{{ provision_gce_registered_image }}' to continue'"
        exit 1
    fi
    image="family/${image}"
fi

### PROVISION THE INFRASTRUCTURE ###

dns_zone="{{ dns_managed_zone | default(provision_prefix + 'managed-zone') }}"

# Check the DNS managed zone in Google Cloud DNS, create it if it doesn't exist and exit after printing NS servers
if ! gcloud --project "{{ gce_project_id }}" dns managed-zones describe "${dns_zone}" &>/dev/null; then
    echo "DNS zone '${dns_zone}' doesn't exist. Must be configured prior to running this script"
    exit 1
fi

# Create network
if ! gcloud --project "{{ gce_project_id }}" compute networks describe "{{ gce_network_name }}" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute networks create "{{ gce_network_name }}" --mode "auto"
else
    echo "Network '{{ gce_network_name }}' already exists"
fi

# Firewall rules in a form:
# ['name']='parameters for "gcloud compute firewall-rules create"'
# For all possible parameters see: gcloud compute firewall-rules create --help
range=""
if [[ -n "{{ openshift_node_port_range }}" ]]; then
    range=",tcp:{{ openshift_node_port_range }},udp:{{ openshift_node_port_range }}"
fi
declare -A FW_RULES=(
  ['icmp']='--allow icmp'
  ['ssh-external']='--allow tcp:22'
  ['ssh-internal']='--allow tcp:22 --source-tags bastion'
  ['master-internal']="--allow tcp:2224,tcp:2379,tcp:2380,tcp:4001,udp:4789,udp:5404,udp:5405,tcp:8053,udp:8053,tcp:8444,tcp:10250,tcp:10255,udp:10255,tcp:24224,udp:24224 --source-tags ocp --target-tags ocp-master"
  ['master-external']="--allow tcp:80,tcp:443,tcp:1936,tcp:8080,tcp:8443${range} --target-tags ocp-master"
  ['node-internal']="--allow udp:4789,tcp:10250,tcp:10255,udp:10255 --source-tags ocp --target-tags ocp-node,ocp-infra-node"
  ['infra-node-internal']="--allow tcp:5000 --source-tags ocp --target-tags ocp-infra-node"
  ['infra-node-external']="--allow tcp:80,tcp:443,tcp:1936${range} --target-tags ocp-infra-node"
)
for rule in "${!FW_RULES[@]}"; do
    ( if ! gcloud --project "{{ gce_project_id }}" compute firewall-rules describe "{{ provision_prefix }}$rule" &>/dev/null; then
        gcloud --project "{{ gce_project_id }}" compute firewall-rules create "{{ provision_prefix }}$rule" --network "{{ gce_network_name }}" ${FW_RULES[$rule]}
    else
        echo "Firewall rule '{{ provision_prefix }}${rule}' already exists"
    fi ) &
done


# Master IP
( if ! gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-ssl-lb-ip" --global &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute addresses create "{{ provision_prefix }}master-ssl-lb-ip" --global
else
    echo "IP '{{ provision_prefix }}master-ssl-lb-ip' already exists"
fi ) &

# Internal master IP
( if ! gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-network-lb-ip" --region "{{ gce_region_name }}" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute addresses create "{{ provision_prefix }}master-network-lb-ip" --region "{{ gce_region_name }}"
else
    echo "IP '{{ provision_prefix }}master-network-lb-ip' already exists"
fi ) &

# Router IP
( if ! gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}router-network-lb-ip" --region "{{ gce_region_name }}" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute addresses create "{{ provision_prefix }}router-network-lb-ip" --region "{{ gce_region_name }}"
else
    echo "IP '{{ provision_prefix }}router-network-lb-ip' already exists"
fi ) &


{% for node_group in provision_gce_node_groups %}
# configure {{ node_group.name }}
(
    if ! gcloud --project "{{ gce_project_id }}" compute instance-templates describe "{{ provision_prefix }}instance-template-{{ node_group.name }}" &>/dev/null; then
        gcloud --project "{{ gce_project_id }}" compute instance-templates create "{{ provision_prefix }}instance-template-{{ node_group.name }}" \
                --machine-type "{{ node_group.machine_type }}" --network "{{ gce_network_name }}" \
                --tags "{{ provision_prefix }}ocp,ocp,{{ node_group.tags }}" \
                --boot-disk-size "{{ node_group.boot_disk_size }}" --boot-disk-type "pd-ssd" \
                --scopes "logging-write,monitoring-write,useraccounts-ro,service-control,service-management,storage-ro,compute-rw" \
                --image "${image}" ${metadata}
    else
        echo "Instance template '{{ provision_prefix }}instance-template-{{ node_group.name }}' already exists"
    fi

    # Create instance group
    if ! gcloud --project "{{ gce_project_id }}" compute instance-groups managed describe "{{ provision_prefix }}ig-{{ node_group.suffix }}" --zone "{{ gce_zone_name }}" &>/dev/null; then
        gcloud --project "{{ gce_project_id }}" compute instance-groups managed create "{{ provision_prefix }}ig-{{ node_group.suffix }}" \
                --zone "{{ gce_zone_name }}" --template "{{ provision_prefix }}instance-template-{{ node_group.name }}" --size "{{ node_group.scale }}"
    else
        echo "Instance group '{{ provision_prefix }}ig-{{ node_group.suffix }}' already exists"
    fi
) &
{% endfor %}

for i in `jobs -p`; do wait $i; done


# Configure the master external LB rules
(
# Master health check
if ! gcloud --project "{{ gce_project_id }}" compute health-checks describe "{{ provision_prefix }}master-ssl-lb-health-check" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute health-checks create https "{{ provision_prefix }}master-ssl-lb-health-check" --port "{{ internal_console_port }}" --request-path "/healthz"
else
    echo "Health check '{{ provision_prefix }}master-ssl-lb-health-check' already exists"
fi

gcloud --project "{{ gce_project_id }}" compute instance-groups managed set-named-ports "{{ provision_prefix }}ig-m" \
        --zone "{{ gce_zone_name }}" --named-ports "{{ provision_prefix }}port-name-master:{{ internal_console_port }}"

# Master backend service
if ! gcloud --project "{{ gce_project_id }}" compute backend-services describe "{{ provision_prefix }}master-ssl-lb-backend" --global &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute backend-services create "{{ provision_prefix }}master-ssl-lb-backend" --health-checks "{{ provision_prefix }}master-ssl-lb-health-check" --port-name "{{ provision_prefix }}port-name-master" --protocol "TCP" --global --timeout="{{ provision_gce_master_https_timeout | default('2m') }}"
    gcloud --project "{{ gce_project_id }}" compute backend-services add-backend "{{ provision_prefix }}master-ssl-lb-backend" --instance-group "{{ provision_prefix }}ig-m" --global --instance-group-zone "{{ gce_zone_name }}"
else
    echo "Backend service '{{ provision_prefix }}master-ssl-lb-backend' already exists"
fi

# Master tcp proxy target
if ! gcloud --project "{{ gce_project_id }}" compute target-tcp-proxies describe "{{ provision_prefix }}master-ssl-lb-target" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute target-tcp-proxies create "{{ provision_prefix }}master-ssl-lb-target" --backend-service "{{ provision_prefix }}master-ssl-lb-backend"
else
    echo "Proxy target '{{ provision_prefix }}master-ssl-lb-target' already exists"
fi

# Master forwarding rule
if ! gcloud --project "{{ gce_project_id }}" compute forwarding-rules describe "{{ provision_prefix }}master-ssl-lb-rule" --global &>/dev/null; then
    IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-ssl-lb-ip" --global --format='value(address)')
    gcloud --project "{{ gce_project_id }}" compute forwarding-rules create "{{ provision_prefix }}master-ssl-lb-rule" --address "$IP" --global --ports "{{ console_port }}" --target-tcp-proxy "{{ provision_prefix }}master-ssl-lb-target"
else
    echo "Forwarding rule '{{ provision_prefix }}master-ssl-lb-rule' already exists"
fi
) &


# Configure the master internal LB rules
(
# Internal master health check
if ! gcloud --project "{{ gce_project_id }}" compute http-health-checks describe "{{ provision_prefix }}master-network-lb-health-check" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute http-health-checks create "{{ provision_prefix }}master-network-lb-health-check" --port "8080" --request-path "/healthz"
else
    echo "Health check '{{ provision_prefix }}master-network-lb-health-check' already exists"
fi

# Internal master target pool
if ! gcloud --project "{{ gce_project_id }}" compute target-pools describe "{{ provision_prefix }}master-network-lb-pool" --region "{{ gce_region_name }}" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute target-pools create "{{ provision_prefix }}master-network-lb-pool" --http-health-check "{{ provision_prefix }}master-network-lb-health-check" --region "{{ gce_region_name }}"
else
    echo "Target pool '{{ provision_prefix }}master-network-lb-pool' already exists"
fi

# Internal master forwarding rule
if ! gcloud --project "{{ gce_project_id }}" compute forwarding-rules describe "{{ provision_prefix }}master-network-lb-rule" --region "{{ gce_region_name }}" &>/dev/null; then
    IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-network-lb-ip" --region "{{ gce_region_name }}" --format='value(address)')
    gcloud --project "{{ gce_project_id }}" compute forwarding-rules create "{{ provision_prefix }}master-network-lb-rule" --address "$IP" --region "{{ gce_region_name }}" --target-pool "{{ provision_prefix }}master-network-lb-pool"
else
    echo "Forwarding rule '{{ provision_prefix }}master-network-lb-rule' already exists"
fi
) &


# Configure the infra node rules
(
# Router health check
if ! gcloud --project "{{ gce_project_id }}" compute http-health-checks describe "{{ provision_prefix }}router-network-lb-health-check" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute http-health-checks create "{{ provision_prefix }}router-network-lb-health-check" --port "1936" --request-path "/healthz"
else
    echo "Health check '{{ provision_prefix }}router-network-lb-health-check' already exists"
fi

# Router target pool
if ! gcloud --project "{{ gce_project_id }}" compute target-pools describe "{{ provision_prefix }}router-network-lb-pool" --region "{{ gce_region_name }}" &>/dev/null; then
    gcloud --project "{{ gce_project_id }}" compute target-pools create "{{ provision_prefix }}router-network-lb-pool" --http-health-check "{{ provision_prefix }}router-network-lb-health-check" --region "{{ gce_region_name }}"
else
    echo "Target pool '{{ provision_prefix }}router-network-lb-pool' already exists"
fi

# Router forwarding rule
if ! gcloud --project "{{ gce_project_id }}" compute forwarding-rules describe "{{ provision_prefix }}router-network-lb-rule" --region "{{ gce_region_name }}" &>/dev/null; then
    IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}router-network-lb-ip" --region "{{ gce_region_name }}" --format='value(address)')
    gcloud --project "{{ gce_project_id }}" compute forwarding-rules create "{{ provision_prefix }}router-network-lb-rule" --address "$IP" --region "{{ gce_region_name }}" --target-pool "{{ provision_prefix }}router-network-lb-pool"
else
    echo "Forwarding rule '{{ provision_prefix }}router-network-lb-rule' already exists"
fi
) &

for i in `jobs -p`; do wait $i; done

# set the target pools
(
if [[ "ig-m" == "{{ provision_gce_router_network_instance_group }}" ]]; then
    gcloud --project "{{ gce_project_id }}" compute instance-groups managed set-target-pools "{{ provision_prefix }}ig-m" --target-pools "{{ provision_prefix }}master-network-lb-pool,{{ provision_prefix }}router-network-lb-pool" --zone "{{ gce_zone_name }}"
else
    gcloud --project "{{ gce_project_id }}" compute instance-groups managed set-target-pools "{{ provision_prefix }}ig-m" --target-pools "{{ provision_prefix }}master-network-lb-pool" --zone "{{ gce_zone_name }}"
    gcloud --project "{{ gce_project_id }}" compute instance-groups managed set-target-pools "{{ provision_prefix }}{{ provision_gce_router_network_instance_group }}" --target-pools "{{ provision_prefix }}router-network-lb-pool" --zone "{{ gce_zone_name }}"
fi
) &

# configure DNS
(
# Retry DNS changes until they succeed since this may be a shared resource
while true; do
    dns="${TMPDIR:-/tmp}/dns.yaml"
    rm -f $dns

    # DNS record for master lb
    if ! gcloud --project "{{ gce_project_id }}" dns record-sets list -z "${dns_zone}" --name "{{ openshift_master_cluster_public_hostname }}" 2>/dev/null | grep -q "{{ openshift_master_cluster_public_hostname }}"; then
        IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-ssl-lb-ip" --global --format='value(address)')
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl 3600 --name "{{ openshift_master_cluster_public_hostname }}." --type A "$IP"
    else
        echo "DNS record for '{{ openshift_master_cluster_public_hostname }}' already exists"
    fi

    # DNS record for internal master lb
    if ! gcloud --project "{{ gce_project_id }}" dns record-sets list -z "${dns_zone}" --name "{{ openshift_master_cluster_hostname }}" 2>/dev/null | grep -q "{{ openshift_master_cluster_hostname }}"; then
        IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}master-network-lb-ip" --region "{{ gce_region_name }}" --format='value(address)')
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl 3600 --name "{{ openshift_master_cluster_hostname }}." --type A "$IP"
    else
        echo "DNS record for '{{ openshift_master_cluster_hostname }}' already exists"
    fi

    # DNS record for router lb
    if ! gcloud --project "{{ gce_project_id }}" dns record-sets list -z "${dns_zone}" --name "{{ wildcard_zone }}" 2>/dev/null | grep -q "{{ wildcard_zone }}"; then
        IP=$(gcloud --project "{{ gce_project_id }}" compute addresses describe "{{ provision_prefix }}router-network-lb-ip" --region "{{ gce_region_name }}" --format='value(address)')
        if [[ ! -f $dns ]]; then
            gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns start -z "${dns_zone}"
        fi
        gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl 3600 --name "{{ wildcard_zone }}." --type A "$IP"
        gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns add -z "${dns_zone}" --ttl 3600 --name "*.{{ wildcard_zone }}." --type CNAME "{{ wildcard_zone }}."
    else
        echo "DNS record for '{{ wildcard_zone }}' already exists"
    fi

    # Commit all DNS changes, retrying if preconditions are not met
    if [[ -f $dns ]]; then
        if ! out="$( gcloud --project "{{ gce_project_id }}" dns record-sets transaction --transaction-file=$dns execute -z "${dns_zone}" 2>&1 )"; then
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

# Create bucket for registry
( 
if ! gsutil ls -p "{{ gce_project_id }}" "gs://{{ openshift_hosted_registry_storage_gcs_bucket }}" &>/dev/null; then
    gsutil mb -p "{{ gce_project_id }}" -l "{{ gce_region_name }}" "gs://{{ openshift_hosted_registry_storage_gcs_bucket }}"
else
    echo "Bucket '{{ openshift_hosted_registry_storage_gcs_bucket }}' already exists"
fi 
) &

# wait until all node groups are stable
{% for node_group in provision_gce_node_groups %}
# wait for stable {{ node_group.name }}
( gcloud --project "{{ gce_project_id }}" compute instance-groups managed wait-until-stable "{{ provision_prefix }}ig-{{ node_group.suffix }}" --zone "{{ gce_zone_name }}" --timeout=300) &
{% endfor %}


for i in `jobs -p`; do wait $i; done
