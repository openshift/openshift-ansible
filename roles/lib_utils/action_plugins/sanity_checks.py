"""
Ansible action plugin to ensure inventory variables are set
appropriately and no conflicting options have been provided.
"""
import re

from ansible.plugins.action import ActionBase
from ansible import errors

# Valid values for openshift_deployment_type
VALID_DEPLOYMENT_TYPES = ('origin', 'openshift-enterprise')

# Tuple of variable names and default values if undefined.
NET_PLUGIN_LIST = (('openshift_use_openshift_sdn', True),
                   ('openshift_use_flannel', False),
                   ('openshift_use_nuage', False),
                   ('openshift_use_contiv', False),
                   ('openshift_use_calico', False))

ENTERPRISE_TAG_REGEX_ERROR = """openshift_image_tag must be in the format
v#.#[.#[.#]]. Examples: v1.2, v3.4.1, v3.5.1.3,
v3.5.1.3.4, v1.2-1, v1.2.3-4, v1.2.3-4.5, v1.2.3-4.5.6
You specified openshift_image_tag={}"""

ORIGIN_TAG_REGEX_ERROR = """openshift_image_tag must be in the format
v#.#.#[-optional.#]. Examples: v1.2.3, v3.5.1-alpha.1
You specified openshift_image_tag={}"""

ORIGIN_TAG_REGEX = {'re': '(^v?\\d+\\.\\d+\\.\\d+(-[\\w\\-\\.]*)?$)',
                    'error_msg': ORIGIN_TAG_REGEX_ERROR}
ENTERPRISE_TAG_REGEX = {'re': '(^v\\d+\\.\\d+(\\.\\d+)*(-\\d+(\\.\\d+)*)?$)',
                        'error_msg': ENTERPRISE_TAG_REGEX_ERROR}
IMAGE_TAG_REGEX = {'origin': ORIGIN_TAG_REGEX,
                   'openshift-enterprise': ENTERPRISE_TAG_REGEX}

CONTAINERIZED_NO_TAG_ERROR_MSG = """To install a containerized Origin release,
you must set openshift_release or openshift_image_tag in your inventory to
specify which version of the OpenShift component images to use.
(Suggestion: add openshift_release="x.y" to inventory.)"""

SDN_NETWORK_VARIABLES_ERROR_MSG = """Detected change in sdn network variables.
inventory variables must match existing cluster deployment. Please adjust
variables as follows:
osm_cluster_network_cidr={},
osm_host_subnet_length={},
openshift_portal_net={}
"""


def to_bool(var_to_check):
    """Determine a boolean value given the multiple
       ways bools can be specified in ansible."""
    # http://yaml.org/type/bool.html
    yes_list = (True, 1, "True", "1", "true", "TRUE",
                "Yes", "yes", "Y", "y", "YES",
                "on", "ON", "On")
    return var_to_check in yes_list


class ActionModule(ActionBase):
    """Action plugin to execute sanity checks."""

    def template_var(self, hostvars, host, varname):
        """Retrieve a variable from hostvars and template it.
           If undefined, return None type."""
        # We will set the current host and variable checked for easy debugging
        # if there are any unhandled exceptions.
        # pylint: disable=W0201
        self.last_checked_var = varname
        # pylint: disable=W0201
        self.last_checked_host = host
        res = hostvars[host].get(varname)
        if res is None:
            return None
        return self._templar.template(res)

    def get_first_master_vars(self, hostvars):
        """Get existing values from master to save time later"""
        host = self.groups['oo_first_master'][0]

        m_net_cidr = self.template_var(
            hostvars, host,
            'oo_first_master_osm_cluster_network_cidr')
        m_subnet_len = self.template_var(
            hostvars, host,
            'oo_first_master_osm_host_subnet_length')
        m_portal_net = self.template_var(
            hostvars, host,
            'oo_first_master_openshift_portal_net')

        # pylint: disable=W0201
        self.fm_vars_templated = {
            'm_net_cidr': m_net_cidr,
            'm_subnet_len': m_subnet_len,
            'm_portal_net': m_portal_net}

    def check_openshift_deployment_type(self, hostvars, host):
        """Ensure a valid openshift_deployment_type is set"""
        openshift_deployment_type = self.template_var(hostvars, host,
                                                      'openshift_deployment_type')
        if openshift_deployment_type not in VALID_DEPLOYMENT_TYPES:
            type_strings = ", ".join(VALID_DEPLOYMENT_TYPES)
            msg = "openshift_deployment_type must be defined and one of {}".format(type_strings)
            raise errors.AnsibleModuleError(msg)
        return openshift_deployment_type

    def check_python_version(self, hostvars, host, distro):
        """Ensure python version is 3 for Fedora and python 2 for others"""
        ansible_python = self.template_var(hostvars, host, 'ansible_python')
        if distro == "Fedora":
            if ansible_python['version']['major'] != 3:
                msg = "openshift-ansible requires Python 3 for {};".format(distro)
                msg += " For information on enabling Python 3 with Ansible,"
                msg += " see https://docs.ansible.com/ansible/python_3_support.html"
                raise errors.AnsibleModuleError(msg)
        else:
            if ansible_python['version']['major'] != 2:
                msg = "openshift-ansible requires Python 2 for {};".format(distro)

    def check_image_tag_format(self, hostvars, host, openshift_deployment_type):
        """Ensure openshift_image_tag is formatted correctly"""
        openshift_image_tag = self.template_var(hostvars, host, 'openshift_image_tag')
        if not openshift_image_tag or openshift_image_tag == 'latest':
            return None
        regex_to_match = IMAGE_TAG_REGEX[openshift_deployment_type]['re']
        res = re.match(regex_to_match, str(openshift_image_tag))
        if res is None:
            msg = IMAGE_TAG_REGEX[openshift_deployment_type]['error_msg']
            msg = msg.format(str(openshift_image_tag))
            raise errors.AnsibleModuleError(msg)

    def no_origin_image_version(self, hostvars, host, openshift_deployment_type):
        """Ensure we can determine what image version to use with origin
          fail when:
          - openshift_is_containerized
          - openshift_deployment_type == 'origin'
          - openshift_release is not defined
          - openshift_image_tag is not defined"""
        if not openshift_deployment_type == 'origin':
            return None
        oic = self.template_var(hostvars, host, 'openshift_is_containerized')
        if not to_bool(oic):
            return None
        orelease = self.template_var(hostvars, host, 'openshift_release')
        oitag = self.template_var(hostvars, host, 'openshift_image_tag')
        if not orelease and not oitag:
            raise errors.AnsibleModuleError(CONTAINERIZED_NO_TAG_ERROR_MSG)

    def network_plugin_check(self, hostvars, host):
        """Ensure only one type of network plugin is enabled"""
        res = []
        # Loop through each possible network plugin boolean, determine the
        # actual boolean value, and append results into a list.
        for plugin, default_val in NET_PLUGIN_LIST:
            res_temp = self.template_var(hostvars, host, plugin)
            if res_temp is None:
                res_temp = default_val
            res.append(to_bool(res_temp))

        if sum(res) != 1:
            plugin_str = list(zip([x[0] for x in NET_PLUGIN_LIST], res))

            msg = "Host Checked: {} Only one of must be true. Found: {}".format(host, plugin_str)
            raise errors.AnsibleModuleError(msg)

    def check_hostname_vars(self, hostvars, host):
        """Checks to ensure openshift_hostname
           and openshift_public_hostname
           conform to the proper length of 63 characters or less"""
        for varname in ('openshift_public_hostname', 'openshift_hostname'):
            var_value = self.template_var(hostvars, host, varname)
            if var_value and len(var_value) > 63:
                msg = '{} must be 63 characters or less'.format(varname)
                raise errors.AnsibleModuleError(msg)

    def check_network_variables(self, hostvars, host):
        """Check network variables are correct if defined"""
        failure = 0

        # Check that all variables are defined.
        net_cidr = self.template_var(hostvars, host, 'osm_cluster_network_cidr')
        subnet_len = self.template_var(hostvars, host, 'osm_host_subnet_length')
        portal_net = self.template_var(hostvars, host, 'openshift_portal_net')

        m_net_cidr = self.fm_vars_templated['m_net_cidr']
        m_subnet_len = self.fm_vars_templated['m_subnet_len']
        m_portal_net = self.fm_vars_templated['m_portal_net']

        if self.fm_vars_templated['m_portal_net'] is None:
            # No existing cluster variables found, we can continue.
            return None

        failure += ((net_cidr is not None) and (net_cidr != m_net_cidr))
        failure += ((subnet_len is not None) and (subnet_len != m_subnet_len))
        failure += ((portal_net is not None) and (portal_net != m_portal_net))

        if failure > 0:
            msg = SDN_NETWORK_VARIABLES_ERROR_MSG.format(
                m_net_cidr,
                m_subnet_len,
                m_portal_net)
            raise errors.AnsibleModuleError(msg)

    def run_master_checks(self, hostvars, host):
        """Execute master-specific checks"""
        self.check_network_variables(hostvars, host)

    def run_checks(self, hostvars, host):
        """Execute the hostvars validations against host"""
        distro = self.template_var(hostvars, host, 'ansible_distribution')
        odt = self.check_openshift_deployment_type(hostvars, host)
        self.check_python_version(hostvars, host, distro)
        self.check_image_tag_format(hostvars, host, odt)
        self.no_origin_image_version(hostvars, host, odt)
        self.network_plugin_check(hostvars, host)
        self.check_hostname_vars(hostvars, host)
        if host in self.groups['oo_masters_to_config']:
            self.run_master_checks(hostvars, host)

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        # self.task_vars holds all in-scope variables.
        # Ignore settting self.task_vars outside of init.
        # pylint: disable=W0201
        self.task_vars = task_vars or {}

        # pylint: disable=W0201
        self.last_checked_host = "none"
        # pylint: disable=W0201
        self.last_checked_var = "none"

        # self._task.args holds task parameters.
        # check_hosts is a parameter to this plugin, and should provide
        # a list of hosts.
        check_hosts = self._task.args.get('check_hosts')
        if not check_hosts:
            msg = "check_hosts is required"
            raise errors.AnsibleModuleError(msg)

        # ansible groups to determine group membership of checked hosts.
        # pylint: disable=W0201
        self.groups = self._task.args.get('groups')

        # We need to access each host's variables
        hostvars = self.task_vars.get('hostvars')
        if not hostvars:
            msg = hostvars
            raise errors.AnsibleModuleError(msg)

        # first master vars might need to be compared to another host's vars,
        # first master always has facts run against it.
        # template some first_master_vars now to save time in loop later.
        self.get_first_master_vars(hostvars)

        # We loop through each host in the provided list check_hosts
        for host in check_hosts:
            try:
                self.run_checks(hostvars, host)
            except Exception as uncaught_e:
                msg = "last_checked_host: {}, last_checked_var: {};"
                msg = msg.format(self.last_checked_host, self.last_checked_var)
                msg += str(uncaught_e)
                raise errors.AnsibleModuleError(msg)

        result["changed"] = False
        result["failed"] = False
        result["msg"] = "Sanity Checks passed"

        return result
