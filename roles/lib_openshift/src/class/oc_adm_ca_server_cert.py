# pylint: skip-file
# flake8: noqa

class CAServerCertConfig(OpenShiftCLIConfig):
    ''' CAServerCertConfig is a DTO for the oc adm ca command '''
    def __init__(self, kubeconfig, verbose, ca_options):
        super(CAServerCertConfig, self).__init__('ca', None, kubeconfig, ca_options)
        self.kubeconfig = kubeconfig
        self.verbose = verbose
        self._ca = ca_options


class CAServerCert(OpenShiftCLI):
    ''' Class to wrap the oc adm ca create-server-cert command line'''
    def __init__(self,
                 config,
                 verbose=False):
        ''' Constructor for oadm ca '''
        super(CAServerCert, self).__init__(None, config.kubeconfig, verbose)
        self.config = config
        self.verbose = verbose

    def get(self):
        '''get the current cert file

           If a file exists by the same name in the specified location then the cert exists
        '''
        cert = self.config.config_options['cert']['value']
        if cert and os.path.exists(cert):
            return open(cert).read()

        return None

    def create(self):
        '''run openshift oc adm ca create-server-cert cmd'''

        # Added this here as a safegaurd for stomping on the
        # cert and key files if they exist
        if self.config.config_options['backup']['value']:
            if os.path.exists(self.config.config_options['key']['value']):
                shutil.copy(self.config.config_options['key']['value'],
                            "%s.orig" % self.config.config_options['key']['value'])
            if os.path.exists(self.config.config_options['cert']['value']):
                shutil.copy(self.config.config_options['cert']['value'],
                            "%s.orig" % self.config.config_options['cert']['value'])

        options = self.config.to_option_list()

        cmd = ['ca', 'create-server-cert']
        cmd.extend(options)

        return self.openshift_cmd(cmd, oadm=True)

    def exists(self):
        ''' check whether the certificate exists and has the clusterIP '''

        cert_path = self.config.config_options['cert']['value']
        if not os.path.exists(cert_path):
            return False

        # Would prefer pyopenssl but is not installed.
        # When we verify it is, switch this code
        proc = subprocess.Popen(['openssl', 'x509', '-noout', '-subject', '-in', cert_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        if proc.returncode == 0:
            for var in self.config.config_options['hostnames']['value'].split(','):
                if var in stdout:
                    return True

        return False

    @staticmethod
    def run_ansible(params, check_mode):
        '''run the idempotent ansible code'''

        config = CAServerCertConfig(params['kubeconfig'],
                                    params['debug'],
                                    {'cert':          {'value': params['cert'], 'include': True},
                                     'hostnames':     {'value': ','.join(params['hostnames']), 'include': True},
                                     'overwrite':     {'value': params['overwrite'], 'include': True},
                                     'key':           {'value': params['key'], 'include': True},
                                     'signer_cert':   {'value': params['signer_cert'], 'include': True},
                                     'signer_key':    {'value': params['signer_key'], 'include': True},
                                     'signer_serial': {'value': params['signer_serial'], 'include': True},
                                     'backup':        {'value': params['backup'], 'include': False},
                                    })

        server_cert = CAServerCert(config)

        state = params['state']

        if state == 'present':
            ########
            # Create
            ########
            if not server_cert.exists() or params['overwrite']:

                if check_mode:
                    return {'changed': True,
                            'msg': "CHECK_MODE: Would have created the certificate.",
                            'state': state}

                api_rval = server_cert.create()

                return {'changed': True, 'results': api_rval, 'state': state}

            ########
            # Exists
            ########
            api_rval = server_cert.get()
            return {'changed': False, 'results': api_rval, 'state': state}

        return {'failed': True,
                'msg': 'Unknown state passed. %s' % state}

