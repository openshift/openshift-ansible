FROM rhel7

MAINTAINER Aaron Weitekamp <aweiteka@redhat.com>

RUN yum -y install http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# Not sure if all of these packages are necessary
# only git and ansible are known requirements
RUN yum install -y --enablerepo rhel-7-server-extras-rpms net-tools bind-utils tmux git ansible

RUN git clone https://github.com/openshift/openshift-ansible.git /opt/openshift-ansible

ENTRYPOINT ["/usr/bin/ansible-playbook", "/opt/openshift-ansible/playbooks/byo/config.yml"]

LABEL RUN docker run -it --rm --privileged --net=host -v ~/.ssh:/root/.ssh -v /etc/ansible:/etc/ansible --name NAME -e NAME=NAME -e IMAGE=IMAGE IMAGE
