# This FROM gives us the proper oo-rhui certs, basic runtime env vars, basic repos, etc.
# Otherwise we can't install anything
FROM rhel6ops

MAINTAINER Thomas Wiest <twiest@redhat.com>

RUN yum -y update ; yum clean all

# Container Specific RPMs
RUN yum -y install ruby193-rubygem-zbxapi cronie zabbix-sender ruby openshift-origin-util-scl ruby193-facter socat ; yum clean all

# Setup ctr-ipc dir
RUN ln -s /shared/var/run/ctr-ipc /var/run/ctr-ipc

# Container specific files
ADD start.rb /start.rb
ADD register-with-zabbix.rb /register-with-zabbix.rb

# TEMP WORKAROUND: until cron-send-haproxy-status.rb doesn't check service to see if haproxy is running
RUN ln -sf /bin/true /etc/init.d/haproxy

CMD ["/start.rb"]
