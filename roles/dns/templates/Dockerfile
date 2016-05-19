FROM {{ base_docker_image }}
MAINTAINER Jan Provaznik <jprovazn@redhat.com>

# install main packages:
RUN yum -y update; yum clean all;
RUN yum -y install bind-utils bind

EXPOSE 53

# start services:
CMD ["/usr/sbin/named", "-f"]
