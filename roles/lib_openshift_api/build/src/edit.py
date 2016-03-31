# pylint: skip-file

class Edit(OpenShiftCLI):
    ''' Class to wrap the oc command line tools
    '''
    # pylint: disable=too-many-arguments
    def __init__(self,
                 kind,
                 namespace,
                 resource_name=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(Edit, self).__init__(namespace, kubeconfig)
        self.namespace = namespace
        self.kind = kind
        self.name = resource_name
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a secret by name '''
        return self._get(self.kind, self.name)

    def update(self, file_name, content, force=False, content_type='yaml'):
        '''run update '''
        if file_name:
            if content_type == 'yaml':
                data = yaml.load(open(file_name))
            elif content_type == 'json':
                data = json.loads(open(file_name).read())

            changes = []
            yed = Yedit(file_name, data)
            for key, value in content.items():
                changes.append(yed.put(key, value))

            if any([not change[0] for change in changes]):
                return {'returncode': 0, 'updated': False}

            yed.write()

            atexit.register(Utils.cleanup, [file_name])

            return self._replace(file_name, force=force)

        return self._replace_content(self.kind, self.name, content, force=force)


