"""
Ansible action plugin to ensure inventory variables are set
appropriately and no conflicting options have been provided.
"""
from ansible.plugins.action import ActionBase
from ansible import errors

# Tuple of variable names and default values if undefined.
NET_PLUGIN_LIST = (('openshift_use_openshift_sdn', True),
                   ('openshift_use_flannel', False),
                   ('openshift_use_nuage', False),
                   ('openshift_use_contiv', False),
                   ('openshift_use_calico', False))


def to_bool(var_to_check):
    """Determine a boolean value given the multiple
       ways bools can be specified in ansible."""
    yes_list = (True, 1, "True", "1", "true", "Yes", "yes")
    return var_to_check in yes_list


class ActionModule(ActionBase):
    """Action plugin to execute sanity checks."""
    def template_var(self, hostvars, host, varname):
        """Retrieve a variable from hostvars and template it.
           If undefined, return None type."""
        res = hostvars[host].get(varname)
        if res is None:
            return None
        return self._templar.template(res)

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

    def run_checks(self, hostvars, host):
        """Execute the hostvars validations against host"""
        # msg = hostvars[host]['ansible_default_ipv4']
        self.network_plugin_check(hostvars, host)
        self.check_hostname_vars(hostvars, host)

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        # self.task_vars holds all in-scope variables.
        # Ignore settting self.task_vars outside of init.
        # pylint: disable=W0201
        self.task_vars = task_vars or {}

        # self._task.args holds task parameters.
        # check_hosts is a parameter to this plugin, and should provide
        # a list of hosts.
        check_hosts = self._task.args.get('check_hosts')
        if not check_hosts:
            msg = "check_hosts is required"
            raise errors.AnsibleModuleError(msg)

        # We need to access each host's variables
        hostvars = self.task_vars.get('hostvars')
        if not hostvars:
            msg = hostvars
            raise errors.AnsibleModuleError(msg)

        # We loop through each host in the provided list check_hosts
        for host in check_hosts:
            self.run_checks(hostvars, host)

        result["changed"] = False
        result["failed"] = False
        result["msg"] = "Sanity Checks passed"

        return result
