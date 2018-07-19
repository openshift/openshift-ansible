        ansible-playbook --user root \
            -i playbooks/openstack/inventory.py \
            -i playbooks/openstack/sample-inventory \
            --private-key ./openshift \
            playbooks/openstack/openshift-cluster/provision.yml

        ansible-playbook --user root \
            -i playbooks/openstack/inventory.py \
            -i playbooks/openstack/sample-inventory \
            --private-key ./openshift \
            playbooks/openstack/openshift-cluster/install.yml

	openstack stack delete --wait --yes openshift.example.com

