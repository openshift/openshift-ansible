# pylint: skip-file
# flake8: noqa

class RegistryException(Exception):
    ''' Registry Exception Class '''
    pass


class RegistryConfig(OpenShiftCLIConfig):
    ''' RegistryConfig is a DTO for the registry.  '''
    def __init__(self, rname, namespace, kubeconfig, registry_options):
        super(RegistryConfig, self).__init__(rname, namespace, kubeconfig, registry_options)


class Registry(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    volume_mount_path = 'spec.template.spec.containers[0].volumeMounts'
    volume_path = 'spec.template.spec.volumes'
    env_path = 'spec.template.spec.containers[0].env'

    def __init__(self,
                 registry_config,
                 verbose=False):
        ''' Constructor for Registry

           a registry consists of 3 or more parts
           - dc/docker-registry
           - svc/docker-registry

           Parameters:
           :registry_config:
           :verbose:
        '''
        super(Registry, self).__init__(registry_config.namespace, registry_config.kubeconfig, verbose)
        self.version = OCVersion(registry_config.kubeconfig, verbose)
        self.svc_ip = None
        self.portal_ip = None
        self.config = registry_config
        self.verbose = verbose
        self.registry_parts = [{'kind': 'dc', 'name': self.config.name},
                               {'kind': 'svc', 'name': self.config.name},
                              ]

        self.__registry_prep = None
        self.volume_mounts = []
        self.volumes = []
        if self.config.config_options['volume_mounts']['value']:
            for volume in self.config.config_options['volume_mounts']['value']:
                volume_info = {'secret_name': volume.get('secret_name', None),
                               'name':        volume.get('name', None),
                               'type':        volume.get('type', None),
                               'path':        volume.get('path', None),
                               'claimName':   volume.get('claim_name', None),
                               'claimSize':   volume.get('claim_size', None),
                              }

                vol, vol_mount = Volume.create_volume_structure(volume_info)
                self.volumes.append(vol)
                self.volume_mounts.append(vol_mount)

        self.dconfig = None
        self.svc = None

    @property
    def deploymentconfig(self):
        ''' deploymentconfig property '''
        return self.dconfig

    @deploymentconfig.setter
    def deploymentconfig(self, config):
        ''' setter for deploymentconfig property '''
        self.dconfig = config

    @property
    def service(self):
        ''' service property '''
        return self.svc

    @service.setter
    def service(self, config):
        ''' setter for service property '''
        self.svc = config

    @property
    def registry_prep(self):
        ''' registry_prep property '''
        if not self.__registry_prep:
            results = self.prep_registry()
            if not results:
                raise RegistryException('Could not perform registry preparation.')
            self.__registry_prep = results

        return self.__registry_prep

    @registry_prep.setter
    def registry_prep(self, data):
        ''' setter method for registry_prep attribute '''
        self.__registry_prep = data

    def force_registry_prep(self):
        '''force a registry prep'''
        self.registry_prep = None

    def get(self):
        ''' return the self.registry_parts '''
        self.deploymentconfig = None
        self.service = None

        for part in self.registry_parts:
            result = self._get(part['kind'], rname=part['name'])
            if result['returncode'] == 0 and part['kind'] == 'dc':
                self.deploymentconfig = DeploymentConfig(result['results'][0])
            elif result['returncode'] == 0 and part['kind'] == 'svc':
                self.service = Yedit(content=result['results'][0])

        return (self.deploymentconfig, self.service)

    def exists(self):
        '''does the object exist?'''
        self.get()
        if self.deploymentconfig or self.service:
            return True

        return False

    def delete(self, complete=True):
        '''return all pods '''
        parts = []
        for part in self.registry_parts:
            if not complete and part['kind'] == 'svc':
                continue
            parts.append(self._delete(part['kind'], part['name']))

        return parts

    def prep_registry(self):
        ''' prepare a registry for instantiation '''
        # In <= 3.4 credentials are used
        # In >= 3.5 credentials are removed
        versions = self.version.get()
        if '3.5' in versions['oc']:
            self.config.config_options['credentials']['include'] = False

        options = self.config.to_option_list()

        cmd = ['registry', '-n', self.config.namespace]
        cmd.extend(options)
        cmd.extend(['--dry-run=True', '-o', 'json'])

        results = self.openshift_cmd(cmd, oadm=True, output=True, output_type='json')
        # probably need to parse this
        # pylint thinks results is a string
        # pylint: disable=no-member
        if results['returncode'] != 0 and results['results'].has_key('items'):
            return results

        service = None
        deploymentconfig = None
        # pylint: disable=invalid-sequence-index
        for res in results['results']['items']:
            if res['kind'] == 'DeploymentConfig':
                deploymentconfig = DeploymentConfig(res)
            elif res['kind'] == 'Service':
                service = Service(res)

        # Verify we got a service and a deploymentconfig
        if not service or not deploymentconfig:
            return results

        # results will need to get parsed here and modifications added
        deploymentconfig = DeploymentConfig(self.add_modifications(deploymentconfig))

        # modify service ip
        if self.svc_ip:
            service.put('spec.clusterIP', self.svc_ip)
        if self.portal_ip:
            service.put('spec.portalIP', self.portal_ip)

        # need to create the service and the deploymentconfig
        service_file = Utils.create_tmp_file_from_contents('service', service.yaml_dict)
        deployment_file = Utils.create_tmp_file_from_contents('deploymentconfig', deploymentconfig.yaml_dict)

        return {"service": service, "service_file": service_file,
                "deployment": deploymentconfig, "deployment_file": deployment_file}

    def create(self):
        '''Create a registry'''
        results = []
        for config_file in ['deployment_file', 'service_file']:
            results.append(self._create(self.registry_prep[config_file]))

        # Clean up returned results
        rval = 0
        for result in results:
            if result['returncode'] != 0:
                rval = result['returncode']


        return {'returncode': rval, 'results': results}

    def update(self):
        '''run update for the registry.  This performs a delete and then create '''
        # Store the current service IP
        self.force_registry_prep()

        self.get()
        if self.service:
            svcip = self.service.get('spec.clusterIP')
            if svcip:
                self.svc_ip = svcip
            portip = self.service.get('spec.portalIP')
            if portip:
                self.portal_ip = portip

        parts = self.delete(complete=False)
        for part in parts:
            if part['returncode'] != 0:
                if part.has_key('stderr') and 'not found' in part['stderr']:
                    # the object is not there, continue
                    continue
                # something went wrong
                return parts

        # Ugly built in sleep here.
        #time.sleep(10)

        results = []
        results.append(self._create(self.registry_prep['deployment_file']))
        results.append(self._replace(self.registry_prep['service_file']))

        # Clean up returned results
        rval = 0
        for result in results:
            if result['returncode'] != 0:
                rval = result['returncode']

        return {'returncode': rval, 'results': results}

    def add_modifications(self, deploymentconfig):
        ''' update a deployment config with changes '''
        # Currently we know that our deployment of a registry requires a few extra modifications
        # Modification 1
        # we need specific environment variables to be set
        for key, value in self.config.config_options['env_vars']['value'].items():
            if not deploymentconfig.exists_env_key(key):
                deploymentconfig.add_env_value(key, value)
            else:
                deploymentconfig.update_env_var(key, value)

        # Modification 2
        # we need specific volume variables to be set
        for volume in self.volumes:
            deploymentconfig.update_volume(volume)

        for vol_mount in self.volume_mounts:
            deploymentconfig.update_volume_mount(vol_mount)

        # Modification 3
        # Edits
        edit_results = []
        for edit in self.config.config_options['edits'].get('value', []):
            if edit['action'] == 'put':
                edit_results.append(deploymentconfig.put(edit['key'],
                                                         edit['value']))
            if edit['action'] == 'update':
                edit_results.append(deploymentconfig.update(edit['key'],
                                                            edit['value'],
                                                            edit.get('index', None),
                                                            edit.get('curr_value', None)))
            if edit['action'] == 'append':
                edit_results.append(deploymentconfig.append(edit['key'],
                                                            edit['value']))

        if edit_results and not any([res[0] for res in edit_results]):
            return None

        return deploymentconfig.yaml_dict

    def needs_update(self, verbose=False):
        ''' check to see if we need to update '''
        if not self.service or not self.deploymentconfig:
            return True

        exclude_list = ['clusterIP', 'portalIP', 'type', 'protocol']
        if not Utils.check_def_equal(self.registry_prep['service'].yaml_dict,
                                     self.service.yaml_dict,
                                     exclude_list,
                                     verbose):
            return True

        exclude_list = ['dnsPolicy',
                        'terminationGracePeriodSeconds',
                        'restartPolicy', 'timeoutSeconds',
                        'livenessProbe', 'readinessProbe',
                        'terminationMessagePath',
                        'rollingParams',
                        'securityContext',
                        'imagePullPolicy',
                        'protocol', # ports.portocol: TCP
                        'type', # strategy: {'type': 'rolling'}
                        'defaultMode', # added on secrets
                        'activeDeadlineSeconds', # added in 1.5 for timeouts
                       ]

        if not Utils.check_def_equal(self.registry_prep['deployment'].yaml_dict,
                                     self.deploymentconfig.yaml_dict,
                                     exclude_list,
                                     verbose):
            return True

        return False


    @staticmethod
    def run_ansible(params, check_mode):
        '''run idempotent ansible code'''

        rconfig = RegistryConfig(params['name'],
                                 params['namespace'],
                                 params['kubeconfig'],
                                 {'credentials': {'value': params['credentials'], 'include': True},
                                  'default_cert': {'value': None, 'include': True},
                                  'images': {'value': params['images'], 'include': True},
                                  'latest_images': {'value': params['latest_images'], 'include': True},
                                  'labels': {'value': params['labels'], 'include': True},
                                  'ports': {'value': ','.join(params['ports']), 'include': True},
                                  'replicas': {'value': params['replicas'], 'include': True},
                                  'selector': {'value': params['selector'], 'include': True},
                                  'service_account': {'value': params['service_account'], 'include': True},
                                  'registry_type': {'value': params['registry_type'], 'include': False},
                                  'mount_host': {'value': params['mount_host'], 'include': True},
                                  'volume': {'value': params['mount_host'], 'include': True},
                                  'template': {'value': params['template'], 'include': True},
                                  'env_vars': {'value': params['env_vars'], 'include': False},
                                  'volume_mounts': {'value': params['volume_mounts'], 'include': False},
                                  'edits': {'value': params['edits'], 'include': False},
                                 })


        ocregistry = Registry(rconfig)

        state = params['state']

        ########
        # Delete
        ########
        if state == 'absent':
            if not ocregistry.exists():
                return {'changed': False, 'state': state}

            if check_mode:
                return {'changed': True, 'msg': 'CHECK_MODE: Would have performed a delete.'}

            api_rval = ocregistry.delete()

            if api_rval['returncode'] != 0:
                return {'failed': True, 'msg': api_rval}

            return {'changed': True, 'results': api_rval, 'state': state}

        if state == 'present':
            ########
            # Create
            ########
            if not ocregistry.exists():

                if check_mode:
                    return {'changed': True, 'msg': 'CHECK_MODE: Would have performed a delete.'}

                api_rval = ocregistry.create()

                if api_rval['returncode'] != 0:
                    return {'failed': True, 'msg': api_rval}

                return {'changed': True, 'results': api_rval, 'state': state}

            ########
            # Update
            ########
            if not params['force'] and not ocregistry.needs_update():
                return {'changed': False, 'state': state}

            if check_mode:
                return {'changed': True, 'msg': 'CHECK_MODE: Would have performed an update.'}

            api_rval = ocregistry.update()

            if api_rval['returncode'] != 0:
                return {'failed': True, 'msg': api_rval}

            return {'changed': True, 'results': api_rval, 'state': state}

        return {'failed': True, 'msg': 'Unknown state passed. %s' % state}
