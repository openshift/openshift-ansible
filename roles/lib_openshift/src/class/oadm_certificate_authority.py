# pylint: skip-file

class CertificateAuthorityConfig(OpenShiftCLIConfig):
    ''' CertificateAuthorityConfig is a DTO for the oadm ca command '''
    def __init__(self, cmd, kubeconfig, verbose, ca_options):
        super(CertificateAuthorityConfig, self).__init__('ca', None, kubeconfig, ca_options)
        self.cmd = cmd
        self.kubeconfig = kubeconfig
        self.verbose = verbose
        self._ca = ca_options

class CertificateAuthority(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''
    def __init__(self,
                 config,
                 verbose=False):
        ''' Constructor for oadm ca '''
        super(CertificateAuthority, self).__init__(None, config.kubeconfig, verbose)
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
        '''Create a deploymentconfig '''
        options = self.config.to_option_list()

        cmd = ['ca']
        cmd.append(self.config.cmd)
        cmd.extend(options)

        return self.openshift_cmd(cmd, oadm=True)

    def exists(self):
        ''' check whether the certificate exists and has the clusterIP '''

        cert_path = self.config.config_options['cert']['value']
        if not os.path.exists(cert_path):
            return False

        proc = subprocess.Popen(['openssl', 'x509', '-noout', '-subject', '-in', cert_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            for var in self.config.config_options['hostnames']['value'].split(','):
                if var in stdout:
                    return True

        return False

    @staticmethod
    def run_ansible(params, check_mode):
        '''run the idempotent ansible code'''

        config = CertificateAuthorityConfig(params['cmd'],
                                            params['kubeconfig'],
                                            params['debug'],
                                            {'cert_dir':      {'value': params['cert_dir'], 'include': True},
                                             'cert':          {'value': params['cert'], 'include': True},
                                             'hostnames':     {'value': ','.join(params['hostnames']), 'include': True},
                                             'master':        {'value': params['master'], 'include': True},
                                             'public_master': {'value': params['public_master'], 'include': True},
                                             'overwrite':     {'value': params['overwrite'], 'include': True},
                                             'signer_name':   {'value': params['signer_name'], 'include': True},
                                             'private_key':   {'value': params['private_key'], 'include': True},
                                             'public_key':    {'value': params['public_key'], 'include': True},
                                             'key':           {'value': params['key'], 'include': True},
                                             'signer_cert':   {'value': params['signer_cert'], 'include': True},
                                             'signer_key':    {'value': params['signer_key'], 'include': True},
                                             'signer_serial': {'value': params['signer_serial'], 'include': True},
                                            })


        oadm_ca = CertificateAuthority(config)

        state = params['state']

        if state == 'present':
            ########
            # Create
            ########
            if not oadm_ca.exists() or params['overwrite']:

                if check_mode:
                    return {'changed': True,
                            'msg': "CHECK_MODE: Would have created the certificate.",
                            'state': state}

                api_rval = oadm_ca.create()

                return {'changed': True, 'results': api_rval, 'state': state}

            ########
            # Exists
            ########
            api_rval = oadm_ca.get()
            return {'changed': False, 'results': api_rval, 'state': state}

        return {'failed': True,
                'msg': 'Unknown state passed. %s' % state}

