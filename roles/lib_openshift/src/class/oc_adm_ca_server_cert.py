# pylint: skip-file

class CAServerCertConfig(OpenShiftCLIConfig):
    ''' CertificateAuthorityConfig is a DTO for the oadm ca command '''
    def __init__(self, cmd, kubeconfig, verbose, ca_options):
        super(CertificateAuthorityConfig, self).__init__('ca', None, kubeconfig, ca_options)
        self.cmd = cmd
        self.kubeconfig = kubeconfig
        self.verbose = verbose
        self._ca = ca_options

class CAServerCert(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''
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
        '''run openshift ca cmd'''
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

        config = CAServerCertConfig(params['cmd'],
                                    params['kubeconfig'],
                                    params['debug'],
                                    {'cert':          {'value': params['cert'], 'include': True},
                                     'hostnames':     {'value': ','.join(params['hostnames']), 'include': True},
                                     'overwrite':     {'value': params['overwrite'], 'include': True},
                                     'signer_name':   {'value': params['signer_name'], 'include': True},
                                     'key':           {'value': params['key'], 'include': True},
                                     'signer_cert':   {'value': params['signer_cert'], 'include': True},
                                     'signer_key':    {'value': params['signer_key'], 'include': True},
                                     'signer_serial': {'value': params['signer_serial'], 'include': True},
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

