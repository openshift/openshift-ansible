# Setup local prometheus development environment

1. Start development cluster

        oc cluster up
1. Authenticate as admin

        oc login -u system:admin
1. Create symlink

        sudo mkdir -p /etc/origin/master
        sudo ln -s ~/.kube/config /etc/origin/master/admin.kubeconfig
1. Run playbook

        ansible-playbook playbooks/adhoc/prometheus/prometheus.yml
