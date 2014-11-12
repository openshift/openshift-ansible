# This FROM gives us the proper oo-rhui certs, basic runtime env vars, basic repos, etc.
# Otherwise we can't install anything
FROM rhel6ops

MAINTAINER Thomas Wiest <twiest@redhat.com>

RUN yum -y update ; yum clean all

# Container Specific RPMs
RUN yum -y install rsyslog rhc-server-common httpd mod_security mod_ssl haproxy15 supervisor ruby ruby193-ruby openshift-origin-util-scl ; yum clean all
# this needs to be on it's own line, otherwise the libra_user group isn't setup properly yet
RUN yum -y install rhc-site-static ; yum clean all

# WORKKAROUND: for a bug in supervisor that causes it to use 100% cpu
RUN yum -y install https://kojipkgs.fedoraproject.org//work/tasks/8506/7818506/supervisor-2.1-9.el6.noarch.rpm ; yum clean all

# Setup libra_user group with correct members
RUN usermod -a -G libra_user apache

# Setup libra_ops group for compatibility with host puppet
RUN groupadd libra_ops

# Setup ctr-ipc dir
RUN ln -s /shared/var/run/ctr-ipc /var/run/ctr-ipc

# common
ADD supervisord.conf /etc/supervisord.conf
ADD start.sh /usr/local/sbin/start.sh
ADD ipc-watcher.rb /usr/local/sbin/ipc-watcher.rb

EXPOSE 80 443 4999

CMD ["/usr/local/sbin/start.sh"]
