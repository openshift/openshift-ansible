# pylint: skip-file

class Secret(OpenShiftCLI):
    ''' Class to wrap the oc command line tools
    '''
    def __init__(self,
                 namespace,
                 secret_name=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(Secret, self).__init__(namespace, kubeconfig)
        self.namespace = namespace
        self.name = secret_name
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a secret by name '''
        return self._get('secrets', self.name)

    def delete(self):
        '''delete a secret by name'''
        return self._delete('secrets', self.name)

    def create(self, files=None, contents=None):
        '''Create a secret '''
        if not files:
            files = Utils.create_files_from_contents(contents)

        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd)

    def update(self, files, force=False):
        '''run update secret

           This receives a list of file names and converts it into a secret.
           The secret is then written to disk and passed into the `oc replace` command.
        '''
        secret = self.prep_secret(files)
        if secret['returncode'] != 0:
            return secret

        sfile_path = '/tmp/%s' % self.name
        with open(sfile_path, 'w') as sfd:
            sfd.write(json.dumps(secret['results']))

        atexit.register(Utils.cleanup, [sfile_path])

        return self._replace(sfile_path, force=force)

    def prep_secret(self, files=None, contents=None):
        ''' return what the secret would look like if created
            This is accomplished by passing -ojson.  This will most likely change in the future
        '''
        if not files:
            files = Utils.create_files_from_contents(contents)

        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-ojson', '-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd, output=True)


