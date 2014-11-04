# This FROM gives us the proper oo-rhui certs, basic runtime env vars, basic repos, etc.
# Otherwise we can't install anything
FROM rhel6ops

MAINTAINER Thomas Wiest <twiest@redhat.com>

RUN yum -y update ; yum clean all

# Container Specific RPMs
RUN yum -y install puppet3 crontabs cronie-anacron cronie system-config-firewall-base httpd mod_ssl ruby193-rubygem-zbxapi mod_security rhc-site-static; yum clean all

# BEGIN: These are to fake out puppet

RUN rm /usr/sbin/lokkit ; ln -s /bin/true /usr/sbin/lokkit

# this is needed so that we can run puppet without running the start script
RUN mkdir -p /etc/haproxy

# END: These are to fake out puppet

# Container specific files
ADD start.rb /usr/local/sbin/start.rb
ADD service.rb /sbin/service

# Ensure the scripts are executable
RUN chmod 755 /sbin/service /usr/local/sbin/start.rb

RUN yum -y install strace ; yum clean all

# Get rid of puppet deprecation warnings
RUN sed -i 's/^.*manifest =.*$//' /etc/puppet/puppet.conf ; \
    sed -i 's/^.*manifestdir =.*$//' /etc/puppet/puppet.conf ; \
    sed -i 's/^.*modulepath =.*$//' /etc/puppet/puppet.conf

CMD ["/usr/local/sbin/start.rb"]
