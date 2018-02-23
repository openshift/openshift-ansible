"""
Ansible action plugin to generate pv and pvc dictionaries lists
"""

from ansible.plugins.action import ActionBase
from ansible import errors


class ActionModule(ActionBase):
    """Action plugin to execute health checks."""

    def get_templated(self, var_to_template):
        """Return a properly templated ansible variable"""
        return self._templar.template(self.task_vars.get(var_to_template))

    def build_common(self, varname=None):
        """Retrieve common variables for each pv and pvc type"""
        volume = self.get_templated(str(varname) + '_volume_name')
        size = self.get_templated(str(varname) + '_volume_size')
        labels = self.task_vars.get(str(varname) + '_labels')
        if labels:
            labels = self._templar.template(labels)
        else:
            labels = dict()
        access_modes = self.get_templated(str(varname) + '_access_modes')
        return (volume, size, labels, access_modes)

    def build_pv_nfs(self, varname=None):
        """Build pv dictionary for nfs storage type"""
        host = self.task_vars.get(str(varname) + '_host')
        if host:
            self._templar.template(host)
        elif host is None:
            groups = self.task_vars.get('groups')
            default_group_name = self.get_templated('openshift_persistent_volumes_default_nfs_group')
            if groups and default_group_name and default_group_name in groups and len(groups[default_group_name]) > 0:
                host = groups['oo_nfs_to_config'][0]
            else:
                raise errors.AnsibleModuleError("|failed no storage host detected")
        volume, size, labels, access_modes = self.build_common(varname=varname)
        directory = self.get_templated(str(varname) + '_nfs_directory')
        path = directory + '/' + volume
        return dict(
            name="{0}-volume".format(volume),
            capacity=size,
            labels=labels,
            access_modes=access_modes,
            storage=dict(
                nfs=dict(
                    server=host,
                    path=path)))

    def build_pv_openstack(self, varname=None):
        """Build pv dictionary for openstack storage type"""
        volume, size, labels, access_modes = self.build_common(varname=varname)
        filesystem = self.get_templated(str(varname) + '_openstack_filesystem')
        volume_id = self.get_templated(str(varname) + '_openstack_volumeID')
        return dict(
            name="{0}-volume".format(volume),
            capacity=size,
            labels=labels,
            access_modes=access_modes,
            storage=dict(
                cinder=dict(
                    fsType=filesystem,
                    volumeID=volume_id)))

    def build_pv_glusterfs(self, varname=None):
        """Build pv dictionary for glusterfs storage type"""
        volume, size, labels, access_modes = self.build_common(varname=varname)
        endpoints = self.get_templated(str(varname) + '_glusterfs_endpoints')
        path = self.get_templated(str(varname) + '_glusterfs_path')
        read_only = self.get_templated(str(varname) + '_glusterfs_readOnly')
        return dict(
            name="{0}-volume".format(volume),
            capacity=size,
            labels=labels,
            access_modes=access_modes,
            storage=dict(
                glusterfs=dict(
                    endpoints=endpoints,
                    path=path,
                    readOnly=read_only)))

    def build_pv_dict(self, varname=None):
        """Check for the existence of PV variables"""
        kind = self.task_vars.get(str(varname) + '_kind')
        if kind:
            kind = self._templar.template(kind)
            create_pv = self.task_vars.get(str(varname) + '_create_pv')
            if create_pv and self._templar.template(create_pv):
                if kind == 'nfs':
                    return self.build_pv_nfs(varname=varname)

                elif kind == 'openstack':
                    return self.build_pv_openstack(varname=varname)

                elif kind == 'glusterfs':
                    return self.build_pv_glusterfs(varname=varname)

                elif not (kind == 'object' or kind == 'dynamic'):
                    msg = "|failed invalid storage kind '{0}' for component '{1}'".format(
                        kind,
                        varname)
                    raise errors.AnsibleModuleError(msg)
        return None

    def build_pvc_dict(self, varname=None):
        """Check for the existence of PVC variables"""
        kind = self.task_vars.get(str(varname) + '_kind')
        if kind:
            kind = self._templar.template(kind)
            create_pv = self.task_vars.get(str(varname) + '_create_pv')
            if create_pv:
                create_pv = self._templar.template(create_pv)
                create_pvc = self.task_vars.get(str(varname) + '_create_pvc')
                if create_pvc:
                    create_pvc = self._templar.template(create_pvc)
                    if kind != 'object' and create_pv and create_pvc:
                        volume, size, _, access_modes = self.build_common(varname=varname)
                        storageclass = self.task_vars.get(str(varname) + '_storageclass')
                        if storageclass:
                            storageclass = self._templar.template(storageclass)
                        elif storageclass is None and kind != 'dynamic':
                            storageclass = ''
                        return dict(
                            name="{0}-claim".format(volume),
                            capacity=size,
                            access_modes=access_modes,
                            storageclass=storageclass)
        return None

    def run(self, tmp=None, task_vars=None):
        """Run generate_pv_pvcs_list action plugin"""
        result = super(ActionModule, self).run(tmp, task_vars)
        # Ignore settting self.task_vars outside of init.
        # pylint: disable=W0201
        self.task_vars = task_vars or {}

        result["changed"] = False
        result["failed"] = False
        result["msg"] = "persistent_volumes list and persistent_volume_claims list created"
        vars_to_check = ['openshift_hosted_registry_storage',
                         'openshift_hosted_router_storage',
                         'openshift_hosted_etcd_storage',
                         'openshift_logging_storage',
                         'openshift_loggingops_storage',
                         'openshift_metrics_storage',
                         'openshift_prometheus_storage',
                         'openshift_prometheus_alertmanager_storage',
                         'openshift_prometheus_alertbuffer_storage']
        persistent_volumes = []
        persistent_volume_claims = []
        for varname in vars_to_check:
            pv_dict = self.build_pv_dict(varname)
            if pv_dict:
                persistent_volumes.append(pv_dict)
            pvc_dict = self.build_pvc_dict(varname)
            if pvc_dict:
                persistent_volume_claims.append(pvc_dict)
        result["persistent_volumes"] = persistent_volumes
        result["persistent_volume_claims"] = persistent_volume_claims
        return result
