# pylint: skip-file

# pylint: disable=too-many-public-methods
class ReplicationController(DeploymentConfig):
    ''' Class to wrap the oc command line tools '''
    replicas_path = "spec.replicas"
    env_path = "spec.template.spec.containers[0].env"
    volumes_path = "spec.template.spec.volumes"
    container_path = "spec.template.spec.containers"
    volume_mounts_path = "spec.template.spec.containers[0].volumeMounts"

    def __init__(self, content):
        ''' Constructor for OpenshiftOC '''
        super(ReplicationController, self).__init__(content=content)
