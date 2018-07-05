OpenShift ImageStreamTags
================

Tags new images into image streams in the openshift namespace

Requirements
------------

Facts
-----


Role Variables
--------------

| Name                                | Default value                                                  |                                          |
|-------------------------------------|----------------------------------------------------------------|------------------------------------------|
| docker_image_url      | Needs to be passed in | The docker registry url to the image that serves as the source for the tag operation                |
| openshift_ist        | Needs to be passed in    | The image stream name and image stream tag ID                  |


Dependencies
------------

Example Playbook
----------------

License
-------

Apache License, Version 2.0

Author Information
------------------

Gabe Montero (gmontero@redhat.com)
