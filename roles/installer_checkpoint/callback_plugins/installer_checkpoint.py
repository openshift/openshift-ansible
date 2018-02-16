"""Ansible callback plugin to print a summary completion status of installation
phases.
"""
from datetime import datetime
from ansible.plugins.callback import CallbackBase
from ansible import constants as C


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
            'installer_phase_health',
            'installer_phase_etcd',
            'installer_phase_nfs',
            'installer_phase_loadbalancer',
            'installer_phase_master',
            'installer_phase_master_additional',
            'installer_phase_node',
            'installer_phase_glusterfs',
            'installer_phase_hosted',
            'installer_phase_web_console',
            'installer_phase_metrics',
            'installer_phase_logging',
            'installer_phase_prometheus',
            'installer_phase_servicecatalog',
            'installer_phase_management',
        ]

        # Define the attributes of the installer phases
        phase_attributes = {
            'installer_phase_initialize': {
                'title': 'Initialization',
                'playbook': ''
            },
            'installer_phase_health': {
                'title': 'Health Check',
                'playbook': 'playbooks/openshift-checks/pre-install.yml'
            },
            'installer_phase_etcd': {
                'title': 'etcd Install',
                'playbook': 'playbooks/openshift-etcd/config.yml'
            },
            'installer_phase_nfs': {
                'title': 'NFS Install',
                'playbook': 'playbooks/openshift-nfs/config.yml'
            },
            'installer_phase_loadbalancer': {
                'title': 'Load balancer Install',
                'playbook': 'playbooks/openshift-loadbalancer/config.yml'
            },
            'installer_phase_master': {
                'title': 'Master Install',
                'playbook': 'playbooks/openshift-master/config.yml'
            },
            'installer_phase_master_additional': {
                'title': 'Master Additional Install',
                'playbook': 'playbooks/openshift-master/additional_config.yml'
            },
            'installer_phase_node': {
                'title': 'Node Install',
                'playbook': 'playbooks/openshift-node/config.yml'
            },
            'installer_phase_glusterfs': {
                'title': 'GlusterFS Install',
                'playbook': 'playbooks/openshift-glusterfs/config.yml'
            },
            'installer_phase_hosted': {
                'title': 'Hosted Install',
                'playbook': 'playbooks/openshift-hosted/config.yml'
            },
            'installer_phase_web_console': {
                'title': 'Web Console Install',
                'playbook': 'playbooks/openshift-web-console/config.yml'
            },
            'installer_phase_metrics': {
                'title': 'Metrics Install',
                'playbook': 'playbooks/openshift-metrics/config.yml'
            },
            'installer_phase_logging': {
                'title': 'Logging Install',
                'playbook': 'playbooks/openshift-logging/config.yml'
            },
            'installer_phase_prometheus': {
                'title': 'Prometheus Install',
                'playbook': 'playbooks/openshift-prometheus/config.yml'
            },
            'installer_phase_servicecatalog': {
                'title': 'Service Catalog Install',
                'playbook': 'playbooks/openshift-service-catalog/config.yml'
            },
            'installer_phase_management': {
                'title': 'Management Install',
                'playbook': 'playbooks/openshift-management/config.yml'
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
                    phase_status = stats.custom['_run'][phase]['status']
                    phase_time = phase_time_delta(stats.custom['_run'][phase])
                    self._display.display(
                        '{}{}: {} ({})'.format(phase_title, ' ' * padding, phase_status, phase_time),
                        color=self.phase_color(phase_status))
                    if phase_status == 'In Progress' and phase != 'installer_phase_initialize':
                        self._display.display(
                            '\tThis phase can be restarted by running: {}'.format(
                                phase_attributes[phase]['playbook']))
                    if 'message' in stats.custom['_run'][phase]:
                        self._display.display(
                            '\t{}'.format(
                                stats.custom['_run'][phase]['message']))

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


def phase_time_delta(phase):
    """ Calculate the difference between phase start and end times """
    time_format = '%Y%m%d%H%M%SZ'
    phase_start = datetime.strptime(phase['start'], time_format)
    if 'end' not in phase:
        # The phase failed so set the end time to now
        phase_end = datetime.now()
    else:
        phase_end = datetime.strptime(phase['end'], time_format)
    delta = str(phase_end - phase_start).split(".")[0]  # Trim microseconds

    return delta
