"""Ansible callback plugin to print a summary completion status of installation
phases.
"""
from ansible.plugins.callback import CallbackBase
from ansible import constants as C

DOCUMENTATION = '''

'''

EXAMPLES = '''
---------------------------------------------
Example display of a successful playbook run:

PLAY RECAP *********************************************************************
master01.example.com : ok=158  changed=16   unreachable=0    failed=0
node01.example.com   : ok=469  changed=74   unreachable=0    failed=0
node02.example.com   : ok=157  changed=17   unreachable=0    failed=0
localhost            : ok=24   changed=0    unreachable=0    failed=0


INSTALLER STATUS ***************************************************************
Initialization             : Complete
etcd Install               : Complete
NFS Install                : Not Started
Load balancer Install      : Not Started
Master Install             : Complete
Master Additional Install  : Complete
Node Install               : Complete
GlusterFS Install          : Not Started
Hosted Install             : Complete
Metrics Install            : Not Started
Logging Install            : Not Started
Service Catalog Install    : Not Started

-----------------------------------------------------
Example display if a failure occurs during execution:

INSTALLER STATUS ***************************************************************
Initialization             : Complete
etcd Install               : Complete
NFS Install                : Not Started
Load balancer Install      : Not Started
Master Install             : In Progress
     This phase can be restarted by running: playbooks/byo/openshift-master/config.yml
Master Additional Install  : Not Started
Node Install               : Not Started
GlusterFS Install          : Not Started
Hosted Install             : Not Started
Metrics Install            : Not Started
Logging Install            : Not Started
Service Catalog Install    : Not Started

'''


class CallbackModule(CallbackBase):
    """This callback summarizes installation phase status."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'installer_checkpoint'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_playbook_on_stats(self, stats):

        # Set the order of the installer phases
        installer_phases = [
            'installer_phase_initialize',
            'installer_phase_etcd',
            'installer_phase_nfs',
            'installer_phase_loadbalancer',
            'installer_phase_master',
            'installer_phase_master_additional',
            'installer_phase_node',
            'installer_phase_glusterfs',
            'installer_phase_hosted',
            'installer_phase_metrics',
            'installer_phase_logging',
            'installer_phase_servicecatalog',
            'installer_phase_management',
        ]

        # Define the attributes of the installer phases
        phase_attributes = {
            'installer_phase_initialize': {
                'title': 'Initialization',
                'playbook': ''
            },
            'installer_phase_etcd': {
                'title': 'etcd Install',
                'playbook': 'playbooks/byo/openshift-etcd/config.yml'
            },
            'installer_phase_nfs': {
                'title': 'NFS Install',
                'playbook': 'playbooks/byo/openshift-nfs/config.yml'
            },
            'installer_phase_loadbalancer': {
                'title': 'Load balancer Install',
                'playbook': 'playbooks/byo/openshift-loadbalancer/config.yml'
            },
            'installer_phase_master': {
                'title': 'Master Install',
                'playbook': 'playbooks/byo/openshift-master/config.yml'
            },
            'installer_phase_master_additional': {
                'title': 'Master Additional Install',
                'playbook': 'playbooks/byo/openshift-master/additional_config.yml'
            },
            'installer_phase_node': {
                'title': 'Node Install',
                'playbook': 'playbooks/byo/openshift-node/config.yml'
            },
            'installer_phase_glusterfs': {
                'title': 'GlusterFS Install',
                'playbook': 'playbooks/byo/openshift-glusterfs/config.yml'
            },
            'installer_phase_hosted': {
                'title': 'Hosted Install',
                'playbook': 'playbooks/byo/openshift-cluster/openshift-hosted.yml'
            },
            'installer_phase_metrics': {
                'title': 'Metrics Install',
                'playbook': 'playbooks/byo/openshift-cluster/openshift-metrics.yml'
            },
            'installer_phase_logging': {
                'title': 'Logging Install',
                'playbook': 'playbooks/byo/openshift-cluster/openshift-logging.yml'
            },
            'installer_phase_servicecatalog': {
                'title': 'Service Catalog Install',
                'playbook': 'playbooks/byo/openshift-cluster/service-catalog.yml'
            },
            'installer_phase_management': {
                'title': 'Management Install',
                'playbook': 'playbooks/common/openshift-cluster/openshift_management.yml'
            },
        }

        # Find the longest phase title
        max_column = 0
        for phase in phase_attributes:
            max_column = max(max_column, len(phase_attributes[phase]['title']))

        if '_run' in stats.custom:
            self._display.banner('INSTALLER STATUS')
            for phase in installer_phases:
                phase_title = phase_attributes[phase]['title']
                padding = max_column - len(phase_title) + 2
                if phase in stats.custom['_run']:
                    phase_status = stats.custom['_run'][phase]
                    self._display.display(
                        '{}{}: {}'.format(phase_title, ' ' * padding, phase_status),
                        color=self.phase_color(phase_status))
                    if phase_status == 'In Progress' and phase != 'installer_phase_initialize':
                        self._display.display(
                            '\tThis phase can be restarted by running: {}'.format(
                                phase_attributes[phase]['playbook']))
                else:
                    # Phase was not found in custom stats
                    self._display.display(
                        '{}{}: {}'.format(phase_title, ' ' * padding, 'Not Started'),
                        color=C.COLOR_SKIP)

        self._display.display("", screen_only=True)

    def phase_color(self, status):
        """ Return color code for installer phase"""
        valid_status = [
            'In Progress',
            'Complete',
        ]

        if status not in valid_status:
            self._display.warning('Invalid phase status defined: {}'.format(status))

        if status == 'Complete':
            phase_color = C.COLOR_OK
        elif status == 'In Progress':
            phase_color = C.COLOR_ERROR
        else:
            phase_color = C.COLOR_WARN

        return phase_color
