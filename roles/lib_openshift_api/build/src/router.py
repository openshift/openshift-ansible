# pylint: skip-file

import time

class RouterConfig(object):
    ''' RouterConfig is a DTO for the router.  '''
    def __init__(self, rname, kubeconfig, router_options):
        self.name = rname
        self.kubeconfig = kubeconfig
        self._router_options = router_options

    @property
    def router_options(self):
        ''' return router options '''
        return self._router_options

    def to_option_list(self):
        ''' return all options as a string'''
        return RouterConfig.stringify(self.router_options)

    @staticmethod
    def stringify(options):
        ''' return hash as list of key value pairs '''
        rval = []
        for key, data in options.items():
            if data['include'] and data['value']:
                rval.append('--%s=%s' % (key.replace('_', '-'), data['value']))

        return rval

class Router(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''
    def __init__(self,
                 router_config,
                 verbose=False):
        ''' Constructor for OpenshiftOC

           a router consists of 3 or more parts
           - dc/router
           - svc/router
           - endpoint/router
        '''
        super(Router, self).__init__('default', router_config.kubeconfig, verbose)
        self.rconfig = router_config
        self.verbose = verbose
        self.router_parts = [{'kind': 'dc', 'name': self.rconfig.name},
                             {'kind': 'svc', 'name': self.rconfig.name},
                             #{'kind': 'endpoints', 'name': self.rconfig.name},
                            ]
    def get(self, filter_kind=None):
        ''' return the self.router_parts '''
        rparts = self.router_parts
        parts = []
        if filter_kind:
            rparts = [part for part in self.router_parts if filter_kind == part['kind']]

        for part in rparts:
            parts.append(self._get(part['kind'], rname=part['name']))

        return parts

    def exists(self):
        '''return a deploymentconfig by name '''
        parts = self.get()
        for part in parts:
            if part['returncode'] != 0:
                return False

        return True

    def delete(self):
        '''return all pods '''
        parts = []
        for part in self.router_parts:
            parts.append(self._delete(part['kind'], part['name']))

        return parts

    def create(self, dryrun=False, output=False, output_type='json'):
        '''Create a deploymentconfig '''
        # We need to create the pem file
        router_pem = '/tmp/router.pem'
        with open(router_pem, 'w') as rfd:
            rfd.write(open(self.rconfig.router_options['cert_file']['value']).read())
            rfd.write(open(self.rconfig.router_options['key_file']['value']).read())

        atexit.register(Utils.cleanup, [router_pem])
        self.rconfig.router_options['default_cert']['value'] = router_pem

        options = self.rconfig.to_option_list()

        cmd = ['router']
        cmd.extend(options)
        if dryrun:
            cmd.extend(['--dry-run=True', '-o', 'json'])

        results = self.openshift_cmd(cmd, oadm=True, output=output, output_type=output_type)

        return results

    def update(self):
        '''run update for the router.  This performs a delete and then create '''
        parts = self.delete()
        if any([part['returncode'] != 0 for part in parts]):
            return parts

        # Ugly built in sleep here.
        time.sleep(15)

        return self.create()

    def needs_update(self, verbose=False):
        ''' check to see if we need to update '''
        dc_inmem = self.get(filter_kind='dc')[0]
        if dc_inmem['returncode'] != 0:
            return dc_inmem

        user_dc = self.create(dryrun=True, output=True, output_type='raw')
        if user_dc['returncode'] != 0:
            return user_dc

        # Since the output from oadm_router is returned as raw
        # we need to parse it.  The first line is the stats_password
        user_dc_results = user_dc['results'].split('\n')
        # stats_password = user_dc_results[0]

        # Load the string back into json and get the newly created dc
        user_dc = json.loads('\n'.join(user_dc_results[1:]))['items'][0]

        # Router needs some exceptions.
        # We do not want to check the autogenerated password for stats admin
        if not self.rconfig.router_options['stats_password']['value']:
            for idx, env_var in enumerate(user_dc['spec']['template']['spec']['containers'][0]['env']):
                if env_var['name'] == 'STATS_PASSWORD':
                    env_var['value'] = \
                      dc_inmem['results'][0]['spec']['template']['spec']['containers'][0]['env'][idx]['value']

        # dry-run doesn't add the protocol to the ports section.  We will manually do that.
        for idx, port in enumerate(user_dc['spec']['template']['spec']['containers'][0]['ports']):
            if not port.has_key('protocol'):
                port['protocol'] = 'TCP'

        # These are different when generating
        skip = ['dnsPolicy',
                'terminationGracePeriodSeconds',
                'restartPolicy', 'timeoutSeconds',
                'livenessProbe', 'readinessProbe',
                'terminationMessagePath',
                'rollingParams',
               ]

        return not Utils.check_def_equal(user_dc, dc_inmem['results'][0], skip_keys=skip, debug=verbose)
