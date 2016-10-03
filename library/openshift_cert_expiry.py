#!/usr/bin/python
# -*- coding: utf-8 -*-

# etcd config file
import ConfigParser
# Expiration parsing
import datetime
# File path stuff
import os
# Config file parsing
import yaml
# Certificate loading
import OpenSSL.crypto


DOCUMENTATION = '''
---
module: openshift_cert_expiry
short_description: Check OpenShift Container Platform (OCP) and Kube certificate expirations on a cluster
description:
  - The M(openshift_cert_expiry) module has two basic functions: to flag certificates which will expire in a set window of time from now, and to notify you about certificates which have already expired.
  - When the module finishes, a summary of the examination is returned. Each certificate in the summary has a C(health) key with a value of one of the following:
  - C(ok) - not expired, and outside of the expiration C(warning_days) window.
  - C(warning) - not expired, but will expire between now and the C(warning_days) window.
  - C(expired) - an expired certificate.
  - Certificate flagging follow this logic:
  - If the expiration date is before now then the certificate is classified as C(expired).
  - The certificates time to live (expiration date - now) is calculated, if that time window is less than C(warning_days) the certificate is classified as C(warning).
  - All other conditions are classified as C(ok).
  - The following keys are ALSO present in the certificate summary:
  - C(cert_cn) - The common name of the certificate (additional CNs present in SAN extensions are omitted)
  - C(days_remaining) - The number of days until the certificate expires.
  - C(expiry) - The date the certificate expires on.
  - C(path) - The full path to the certificate on the examined host.
version_added: "0.0"
options:
  config_base:
    description:
      - Base path to OCP system settings.
    required: false
    default: /etc/origin
  warning_days:
    description:
      - Flag certificates which will expire in C(warning_days) days from now.
    required: false
    default: 30
  show_all:
    description:
      - Enable this option to show analysis of ALL certificates examined by this module.
      - By default only certificates which have expired, or will expire within the C(warning_days) window will be reported.
    required: false
    default: false

author: "Tim Bielawa (@tbielawa) <tbielawa@redhat.com>"
'''

EXAMPLES = '''
# Default invocation, only notify about expired certificates or certificates which will expire within 30 days from now
- openshift_cert_expiry:

# Expand the warning window to show certificates expiring within a year from now
- openshift_cert_expiry: warning_days=365

# Show expired, soon to expire (now + 30 days), and all other certificates examined
- openshift_cert_expiry: show_all=true
'''


######################################################################
# etcd does not begin their config file with an opening [section] as
# required by the Python ConfigParser module. We hack around it by
# slipping one in ourselves prior to parsing.
#
# Source: Alex Martelli - http://stackoverflow.com/a/2819788/6490583
class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[ETCD]\n'

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()

######################################################################

def filter_paths(path_list):
    # `path_list` - A list of file paths to check. Only files which
    # exist will be returned
    return filter(
        lambda p: os.path.exists(os.path.realpath(p)),
        path_list)

def load_and_handle_cert(cert_string, now, base64decode=False):
    """Load a certificate, split off the good parts, and return some
useful data

Params:

- `cert_string` (string) - a certificate loaded into a string object
- `now` (datetime) - a datetime object of the time to calculate the certificate 'time_remaining' against
- `base64decode` (bool) - run .decode('base64') on the input?

Returns:
A 3-tuple of the form: (certificate_common_name, certificate_expiry_date, certificate_time_remaining)

    """
    if base64decode:
        _cert_string = cert_string.decode('base-64')
    else:
        _cert_string = cert_string

    cert_loaded = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM, _cert_string)

    # Strip the subject down to just the value of the first name
    cert_subject = cert_loaded.get_subject().get_components()[0][1]

    # Grab the expiration date
    cert_expiry = cert_loaded.get_notAfter()
    cert_expiry_date = datetime.datetime.strptime(
        cert_expiry,
        # example get_notAfter() => 20180922170439Z
        '%Y%m%d%H%M%SZ')

    time_remaining = cert_expiry_date - now

    return (cert_subject, cert_expiry_date, time_remaining)

def classify_cert(cert_meta, now, time_remaining, expire_window, cert_list):
    """Given metadata about a certificate under examination, classify it
    into one of three categories, 'ok', 'warning', and 'expired'.

Params:

- `cert_meta` dict - A dict with certificate metadata. Required fields
  include: 'cert_cn', 'path', 'expiry', 'days_remaining', 'health'.
- `now` (datetime) - a datetime object of the time to calculate the certificate 'time_remaining' against
- `time_remaining` (datetime.timedelta) - a timedelta for how long until the cert expires
- `expire_window` (datetime.timedelta) - a timedelta for how long the warning window is
- `cert_list` list - A list to shove the classified cert into

Return:
- `cert_list` - The updated list of classified certificates
    """
    expiry_str = str(cert_meta['expiry'])
    # Categorization
    if cert_meta['expiry'] < now:
        # This already expired, must NOTIFY
        cert_meta['health'] = 'expired'
    elif time_remaining < expire_window:
        # WARN about this upcoming expirations
        cert_meta['health'] = 'warning'
    else:
        # Not expired or about to expire
        cert_meta['health'] = 'ok'

    cert_meta['expiry'] = expiry_str
    cert_list.append(cert_meta)
    return cert_list

def tabulate_summary(certificates, kubeconfigs):
    """Calculate the summary text for when the module finishes
running. This includes counds of each classification and what have
you.

Params:

- `certificates` (list of dicts) - Processed `expire_check_result`
  dicts with filled in `health` keys for system certificates.
- `kubeconfigs` (list of dicts) - Processed `expire_check_result`
  dicts with filled in `health` keys for embedded kubeconfig
  certificates.

Return:
- `summary_results` (dict) - Counts of each cert/kubeconfig
  classification and total items examined.
    """
    summary_results = {
        'system_certificates': len(certificates),
        'kubeconfig_certificates': len(kubeconfigs),
        'total': len(certificates + kubeconfigs),
        'ok': 0,
        'warning': 0,
        'expired': 0
    }

    items = certificates + kubeconfigs
    summary_results['expired'] = len([c for c in items if c['health'] == 'expired'])
    summary_results['warning'] = len([c for c in items if c['health'] == 'warning'])
    summary_results['ok'] = len([c for c in items if c['health'] == 'ok'])

    return summary_results


######################################################################
def main():
    module = AnsibleModule(
        argument_spec=dict(
            config_base=dict(
                required=False,
                default="/etc/origin",
                type='str'),
            warning_days=dict(
                required=False,
                default=int(30),
                type='int'),
            show_all=dict(
                required=False,
                default="False",
                type='bool')
        ),
        supports_check_mode=True,
    )

    # Basic scaffolding for OpenShift spcific certs
    openshift_base_config_path = module.params['config_base']
    openshift_master_config_path = os.path.normpath(
        os.path.join(openshift_base_config_path, "master/master-config.yaml")
    )
    openshift_node_config_path = os.path.normpath(
            os.path.join(openshift_base_config_path, "node/node-config.yaml")
    )
    openshift_cert_check_paths = [
        openshift_master_config_path,
        openshift_node_config_path,
    ]

    # Paths for Kubeconfigs. Additional kubeconfigs are conditionally checked later in the code
    kubeconfig_paths = [
        os.path.normpath(
            os.path.join(openshift_base_config_path, "master/admin.kubeconfig")
        ),
        os.path.normpath(
            os.path.join(openshift_base_config_path, "master/openshift-master.kubeconfig")
        ),
        os.path.normpath(
            os.path.join(openshift_base_config_path, "master/openshift-node.kubeconfig")
        ),
        os.path.normpath(
            os.path.join(openshift_base_config_path, "master/openshift-router.kubeconfig")
        ),
    ]

    # Expiry checking stuff
    now = datetime.datetime.now()
    # todo, catch exception for invalid input and return a fail_json
    warning_days = int(module.params['warning_days'])
    expire_window = datetime.timedelta(days=warning_days)

    # Module stuff
    #
    # The results of our cert checking to return from the task call
    check_results = {}
    check_results['meta'] = {}
    check_results['meta']['warning_days'] = warning_days
    check_results['meta']['checked_at_time'] = str(now)
    check_results['meta']['warn_after_date'] = str(now + expire_window)
    check_results['meta']['show_all'] = str(module.params['show_all'])
    # All the analyzed certs accumulate here
    certs = []

    ######################################################################
    # Sure, why not? Let's enable check mode.
    if module.check_mode:
        check_results['certs'] = []
        module.exit_json(
            check_results=check_results,
            msg="Checked 0 certificates. Expired/Warning/OK: 0/0/0. Warning window: %s days" % module.params['warning_days'],
            rc=0,
            changed=False
        )

    ######################################################################
    # Check for OpenShift Container Platform specific certs
    ######################################################################
    for os_cert in filter_paths(openshift_cert_check_paths):
        # Open up that config file and locate the cert and CA
        with open(os_cert, 'r') as fp:
            cert_meta = {}
            cfg = yaml.load(fp)
            # cert files are specified in parsed `fp` as relative to the path
            # of the original config file. 'master-config.yaml' with certFile
            # = 'foo.crt' implies that 'foo.crt' is in the same
            # directory. certFile = '../foo.crt' is in the parent directory.
            cfg_path = os.path.dirname(fp.name)
            cert_meta['certFile'] = os.path.join(cfg_path, cfg['servingInfo']['certFile'])
            cert_meta['clientCA'] = os.path.join(cfg_path, cfg['servingInfo']['clientCA'])

        ######################################################################
        # Load the certificate and the CA, parse their expiration dates into
        # datetime objects so we can manipulate them later
        for _, v in cert_meta.iteritems():
            with open(v, 'r') as fp:
                cert = fp.read()
                cert_subject, cert_expiry_date, time_remaining = load_and_handle_cert(cert, now)

                expire_check_result = {
                    'cert_cn': cert_subject,
                    'path': fp.name,
                    'expiry': cert_expiry_date,
                    'days_remaining': time_remaining.days,
                    'health': None,
                }

                classify_cert(expire_check_result, now, time_remaining, expire_window, certs)

    ######################################################################
    # /Check for OpenShift Container Platform specific certs
    ######################################################################

    ######################################################################
    # Check service Kubeconfigs
    ######################################################################
    kubeconfigs = []

    # There may be additional kubeconfigs to check, but their naming
    # is less predictable than the ones we've already assembled.

    try:
        # Try to read the standard 'node-config.yaml' file to check if
        # this host is a node.
        with open(openshift_node_config_path, 'r') as fp:
            cfg = yaml.load(fp)
            # OK, the config file exists, therefore this is a
            # node. Nodes have their own kubeconfig files to
            # communicate with the master API. Let's read the relative
            # path to that file from the node config.
            node_masterKubeConfig = cfg['masterKubeConfig']
            # As before, the path to the 'masterKubeConfig' file is
            # relative to `fp`
            cfg_path = os.path.dirname(fp.name)
            node_kubeconfig = os.path.join(cfg_path, node_masterKubeConfig)
        with open(node_kubeconfig, 'r') as fp:
            # Read in the nodes kubeconfig file and grab the good stuff
            cfg = yaml.load(fp)
            c = cfg['users'][0]['user']['client-certificate-data']
            (cert_subject,
             cert_expiry_date,
             time_remaining) = load_and_handle_cert(c, now, base64decode=True)

            expire_check_result = {
                'cert_cn': cert_subject,
                'path': fp.name,
                'expiry': cert_expiry_date,
                'days_remaining': time_remaining.days,
                'health': None,
            }

            classify_cert(expire_check_result, now, time_remaining, expire_window, kubeconfigs)
    except Exception:
        # This is not a node
        pass

    for kube in filter_paths(kubeconfig_paths):
        with open(kube, 'r') as fp:
            # TODO: Maybe consider catching exceptions here?
            cfg = yaml.load(fp)
            # Per conversation, "the kubeconfigs you care about:
            # admin, router, registry should all be single
            # value". Following that advice we only grab the data for
            # the user at index 0 in the 'users' list. There should
            # not be more than one user.
            c = cfg['users'][0]['user']['client-certificate-data']
            (cert_subject,
             cert_expiry_date,
             time_remaining) = load_and_handle_cert(c, now, base64decode=True)

            expire_check_result = {
                'cert_cn': cert_subject,
                'path': fp.name,
                'expiry': cert_expiry_date,
                'days_remaining': time_remaining.days,
                'health': None,
            }

            classify_cert(expire_check_result, now, time_remaining, expire_window, kubeconfigs)


    ######################################################################
    # /Check service Kubeconfigs
    ######################################################################
    res = tabulate_summary(certs, kubeconfigs)

    msg = "Checked {count} certificates and kubeconfigs. Expired/Warning/OK: {exp}/{warn}/{ok}. Warning window: {window} days".format(
        count=res['total'],
        exp=res['expired'],
        warn=res['warning'],
        ok=res['ok'],
        window=int(module.params['warning_days']),
    )

    # By default we only return detailed information about expired or
    # warning certificates. If show_all is true then we will print all
    # the certificates examined.
    if not module.params['show_all']:
        check_results['certs'] = filter(lambda ctr: ctr['health'] in ['expired', 'warning'], certs)
        check_results['kubeconfigs'] = filter(lambda ctr: ctr['health'] in ['expired', 'warning'], kubeconfigs)
    else:
        check_results['certs'] = certs
        check_results['kubeconfigs'] = kubeconfigs

    # Sort the final results to report in order of ascending safety
    # time. That is to say, the certificates which will expire sooner
    # will be at the front of the list and certificates which will
    # expire later are at the end.
    check_results['certs'] = sorted(check_results['certs'], cmp=lambda x, y: cmp(x['days_remaining'], y['days_remaining']))
    check_results['kubeconfigs'] = sorted(check_results['kubeconfigs'], cmp=lambda x, y: cmp(x['days_remaining'], y['days_remaining']))
    # This module will never change anything, but we might want to
    # change the return code parameter if there is some catastrophic
    # error we noticed earlier
    module.exit_json(
        check_results=check_results,
        summary=res,
        msg=msg,
        rc=0,
        changed=False
    )

######################################################################
# import module snippets
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
