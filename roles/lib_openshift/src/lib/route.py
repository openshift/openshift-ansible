# pylint: skip-file
# flake8: noqa
# noqa: E302,E301


# pylint: disable=too-many-instance-attributes
class RouteConfig(object):
    ''' Handle route options '''
    # pylint: disable=too-many-arguments
    def __init__(self,
                 sname,
                 namespace,
                 kubeconfig,
                 destcacert=None,
                 cacert=None,
                 cert=None,
                 key=None,
                 host=None,
                 tls_termination=None,
                 service_name=None):
        ''' constructor for handling route options '''
        self.kubeconfig = kubeconfig
        self.name = sname
        self.namespace = namespace
        self.host = host
        self.tls_termination = tls_termination
        self.destcacert = destcacert
        self.cacert = cacert
        self.cert = cert
        self.key = key
        self.service_name = service_name
        self.data = {}

        self.create_dict()

    def create_dict(self):
        ''' return a service as a dict '''
        self.data['apiVersion'] = 'v1'
        self.data['kind'] = 'Route'
        self.data['metadata'] = {}
        self.data['metadata']['name'] = self.name
        self.data['metadata']['namespace'] = self.namespace
        self.data['spec'] = {}

        self.data['spec']['host'] = self.host

        if self.tls_termination:
            self.data['spec']['tls'] = {}

            if self.tls_termination == 'reencrypt':
                self.data['spec']['tls']['destinationCACertificate'] = self.destcacert
            self.data['spec']['tls']['key'] = self.key
            self.data['spec']['tls']['caCertificate'] = self.cacert
            self.data['spec']['tls']['certificate'] = self.cert
            self.data['spec']['tls']['termination'] = self.tls_termination

        self.data['spec']['to'] = {'kind': 'Service', 'name': self.service_name}


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class Route(Yedit):
    ''' Class to wrap the oc command line tools '''
    host_path = "spec.host"
    service_path = "spec.to.name"
    cert_path = "spec.tls.certificate"
    cacert_path = "spec.tls.caCertificate"
    destcacert_path = "spec.tls.destinationCACertificate"
    termination_path = "spec.tls.termination"
    key_path = "spec.tls.key"
    kind = 'route'

    def __init__(self, content):
        '''Route constructor'''
        super(Route, self).__init__(content=content)

    def get_destcacert(self):
        ''' return cert '''
        return self.get(Route.destcacert_path)

    def get_cert(self):
        ''' return cert '''
        return self.get(Route.cert_path)

    def get_key(self):
        ''' return key '''
        return self.get(Route.key_path)

    def get_cacert(self):
        ''' return cacert '''
        return self.get(Route.cacert_path)

    def get_service(self):
        ''' return service name '''
        return self.get(Route.service_path)

    def get_termination(self):
        ''' return tls termination'''
        return self.get(Route.termination_path)

    def get_host(self):
        ''' return host '''
        return self.get(Route.host_path)
