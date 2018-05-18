#!/bin/bash

set -euo pipefail

if [[ -n "{{ openshift_gcp_ssh_private_key }}" ]]; then
    # Create SSH key for GCE
    if [ ! -f "{{ openshift_gcp_ssh_private_key }}" ]; then
        ssh-keygen -t rsa -f "{{ openshift_gcp_ssh_private_key }}" -C gce-provision-cloud-user -N ''
        ssh-add "{{ openshift_gcp_ssh_private_key }}" || true
    fi

    # Check if the public key is in the project metadata, and if not, add it there
    if [ -f "{{ openshift_gcp_ssh_private_key }}.pub" ]; then
        pub_file="{{ openshift_gcp_ssh_private_key }}.pub"
        pub_key=$(cut -d ' ' -f 2 < "{{ openshift_gcp_ssh_private_key }}.pub")
    else
        keyfile="${HOME}/.ssh/google_compute_engine"
        pub_file="${keyfile}.pub"
        mkdir -p "${HOME}/.ssh"
        cp "{{ openshift_gcp_ssh_private_key }}" "${keyfile}"
        chmod 0600 "${keyfile}"
        ssh-keygen -y -f "${keyfile}" >  "${pub_file}"
        pub_key=$(cut -d ' ' -f 2 <  "${pub_file}")
    fi
    key_tmp_file='/tmp/ocp-gce-keys'
    echo -n 'cloud-user:' >> "$key_tmp_file"
    cat "${pub_file}" >> "$key_tmp_file"

    # Set up ssh keys for the builder instance.
    (
        build_instance="{{ openshift_gcp_prefix }}build-image-instance"
        if ! metadata=$(gcloud --project "{{ openshift_gcp_project }}" compute instances describe "${build_instance}" --zone "{{ openshift_gcp_zone }}" --format='value[](metadata.items.ssh-keys)'); then
            exit 0
        fi
        if ! echo "${metadata}" | grep -q "${pub_key}"; then
            gcloud --project "{{ openshift_gcp_project }}" compute instances add-metadata "${build_instance}" --zone "{{ openshift_gcp_zone }}" --metadata-from-file ssh-keys="${key_tmp_file}"
        fi
    ) &

    # Set up ssh keys for all instances in all groups.
    {% for node_group in openshift_gcp_node_group_config %}
    (
        if ! instances=($( gcloud --project "{{ openshift_gcp_project }}" compute instance-groups managed list-instances "{{ openshift_gcp_prefix }}ig-{{ node_group.suffix }}" --zone "{{ openshift_gcp_zone }}" --format='value[terminator=" "](instance)' 2>/dev/null )); then
            exit 0
        fi
        for instance in ${instances[@]+"${instances[@]}"}; do
            if ! gcloud --project "{{ openshift_gcp_project }}" compute instances describe "${instance}" --zone "{{ openshift_gcp_zone }}" --format='value[](metadata.items.ssh-keys)' | grep -q "${pub_key}"; then
                gcloud --project "{{ openshift_gcp_project }}" compute instances add-metadata "${instance}" --zone "{{ openshift_gcp_zone }}" --metadata-from-file ssh-keys="${key_tmp_file}" &
            fi
        done
        for i in `jobs -p`; do wait $i; done
    ) &
    {% endfor %}
    for i in `jobs -p`; do wait $i; done
    rm -f "$key_tmp_file"
fi
