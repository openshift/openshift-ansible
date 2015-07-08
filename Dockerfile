FROM rhel7

MAINTAINER Aaron Weitekamp <aweiteka@redhat.com>

RUN yum -y install http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# Not sure if all of these packages are necessary
# only git and ansible are known requirements
RUN yum install -y --enablerepo rhel-7-server-extras-rpms net-tools bind-utils tmux git ansible

# Not sure if this repo is required
RUN curl -o /etc/yum.repos.d/atomic-enterprise.repo http://mirror.ops.rhcloud.com/atomic/mirror/.atomic-enterprise-early-1/atomic-enterprise.repo

RUN git clone https://github.com/projectatomic/atomic-enterprise-training.git \
              /opt/training && \
    git clone https://github.com/projectatomic/atomic-enterprise-ansible.git \
              /opt/atomic-enterprise-ansible

CMD ansible-playbook /opt/atomic-enterprise-ansible/playbooks/byo/config.yml

LABEL RUN docker run -it --rm --net=host -v ~/.ssh/id_rsa:/root/.ssh/id_rsa -v /etc/ansible/hosts:/etc/ansible/hosts --name NAME -e NAME=NAME -e IMAGE=IMAGE IMAGE

