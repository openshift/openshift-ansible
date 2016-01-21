#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Custom filters for use in openshift-master
'''
import copy
import sys
import yaml

from ansible import errors
from ansible.runner.filter_plugins.core import bool as ansible_bool


class IdentityProviderBase(object):
    """ IdentityProviderBase

        Attributes:
            name (str): Identity provider Name
            login (bool): Is this identity provider a login provider?
            challenge (bool): Is this identity provider a challenge provider?
            provider (dict): Provider specific config
            _idp (dict): internal copy of the IDP dict passed in
            _required (list): List of lists of strings for required attributes
            _optional (list): List of lists of strings for optional attributes
            _allow_additional (bool): Does this provider support attributes
                not in _required and _optional

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    # disabling this check since the number of instance attributes are
    # necessary for this class
    # pylint: disable=too-many-instance-attributes
    def __init__(self, api_version, idp):
        if api_version not in ['v1']:
            raise errors.AnsibleFilterError("|failed api version {0} unknown".format(api_version))

        self._idp = copy.deepcopy(idp)

        if 'name' not in self._idp:
            raise errors.AnsibleFilterError("|failed identity provider missing a name")

        if 'kind' not in self._idp:
            raise errors.AnsibleFilterError("|failed identity provider missing a kind")

        self.name = self._idp.pop('name')
        self.login = ansible_bool(self._idp.pop('login', False))
        self.challenge = ansible_bool(self._idp.pop('challenge', False))
        self.provider = dict(apiVersion=api_version, kind=self._idp.pop('kind'))

        self._required = [['mappingMethod', 'mapping_method']]
        self._optional = []
        self._allow_additional = True

    @staticmethod
    def validate_idp_list(idp_list):
        ''' validates a list of idps '''
        login_providers = [x.name for x in idp_list if x.login]
        if len(login_providers) > 1:
            raise errors.AnsibleFilterError("|failed multiple providers are "
                                            "not allowed for login. login "
                                            "providers: {0}".format(', '.join(login_providers)))

        names = [x.name for x in idp_list]
        if len(set(names)) != len(names):
            raise errors.AnsibleFilterError("|failed more than one provider configured with the same name")

        for idp in idp_list:
            idp.validate()

    def validate(self):
        ''' validate an instance of this idp class '''
        valid_mapping_methods = ['add', 'claim', 'generate', 'lookup']
        if self.provider['mappingMethod'] not in valid_mapping_methods:
            raise errors.AnsibleFilterError("|failed unkown mapping method "
                                            "for provider {0}".format(self.__class__.__name__))

    @staticmethod
    def get_default(key):
        ''' get a default value for a given key '''
        if key == 'mappingMethod':
            return 'claim'
        else:
            return None

    def set_provider_item(self, items, required=False):
        ''' set a provider item based on the list of item names provided. '''
        for item in items:
            provider_key = items[0]
            if item in self._idp:
                self.provider[provider_key] = self._idp.pop(item)
                break
        else:
            default = self.get_default(provider_key)
            if default is not None:
                self.provider[provider_key] = default
            elif required:
                raise errors.AnsibleFilterError("|failed provider {0} missing "
                                                "required key {1}".format(self.__class__.__name__, provider_key))

    def set_provider_items(self):
        ''' set the provider items for this idp '''
        for items in self._required:
            self.set_provider_item(items, True)
        for items in self._optional:
            self.set_provider_item(items)
        if self._allow_additional:
            for key in self._idp.keys():
                self.set_provider_item([key])
        else:
            if len(self._idp) > 0:
                raise errors.AnsibleFilterError("|failed provider {0} "
                                                "contains unknown keys "
                                                "{1}".format(self.__class__.__name__, ', '.join(self._idp.keys())))

    def to_dict(self):
        ''' translate this idp to a dictionary '''
        return dict(name=self.name, challenge=self.challenge,
                    login=self.login, provider=self.provider)


class LDAPPasswordIdentityProvider(IdentityProviderBase):
    """ LDAPPasswordIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['attributes'], ['url'], ['insecure']]
        self._optional += [['ca'],
                           ['bindDN', 'bind_dn'],
                           ['bindPassword', 'bind_password']]

        self._idp['insecure'] = ansible_bool(self._idp.pop('insecure', False))

        if 'attributes' in self._idp and 'preferred_username' in self._idp['attributes']:
            pref_user = self._idp['attributes'].pop('preferred_username')
            self._idp['attributes']['preferredUsername'] = pref_user

    def validate(self):
        ''' validate this idp instance '''
        IdentityProviderBase.validate(self)
        if not isinstance(self.provider['attributes'], dict):
            raise errors.AnsibleFilterError("|failed attributes for provider "
                                            "{0} must be a dictionary".format(self.__class__.__name__))

        attrs = ['id', 'email', 'name', 'preferredUsername']
        for attr in attrs:
            if attr in self.provider['attributes'] and not isinstance(self.provider['attributes'][attr], list):
                raise errors.AnsibleFilterError("|failed {0} attribute for "
                                                "provider {1} must be a list".format(attr, self.__class__.__name__))

        unknown_attrs = set(self.provider['attributes'].keys()) - set(attrs)
        if len(unknown_attrs) > 0:
            raise errors.AnsibleFilterError("|failed provider {0} has unknown "
                                            "attributes: {1}".format(self.__class__.__name__, ', '.join(unknown_attrs)))


class KeystonePasswordIdentityProvider(IdentityProviderBase):
    """ KeystoneIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['url'], ['domainName', 'domain_name']]
        self._optional += [['ca'], ['certFile', 'cert_file'], ['keyFile', 'key_file']]


class RequestHeaderIdentityProvider(IdentityProviderBase):
    """ RequestHeaderIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['headers']]
        self._optional += [['challengeURL', 'challenge_url'],
                           ['loginURL', 'login_url'],
                           ['clientCA', 'client_ca']]

    def validate(self):
        ''' validate this idp instance '''
        IdentityProviderBase.validate(self)
        if not isinstance(self.provider['headers'], list):
            raise errors.AnsibleFilterError("|failed headers for provider {0} "
                                            "must be a list".format(self.__class__.__name__))


class AllowAllPasswordIdentityProvider(IdentityProviderBase):
    """ AllowAllPasswordIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False


class DenyAllPasswordIdentityProvider(IdentityProviderBase):
    """ DenyAllPasswordIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False


class HTPasswdPasswordIdentityProvider(IdentityProviderBase):
    """ HTPasswdPasswordIdentity

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['file', 'filename', 'fileName', 'file_name']]

    @staticmethod
    def get_default(key):
        if key == 'file':
            return '/etc/origin/htpasswd'
        else:
            return IdentityProviderBase.get_default(key)


class BasicAuthPasswordIdentityProvider(IdentityProviderBase):
    """ BasicAuthPasswordIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['url']]
        self._optional += [['ca'], ['certFile', 'cert_file'], ['keyFile', 'key_file']]


class IdentityProviderOauthBase(IdentityProviderBase):
    """ IdentityProviderOauthBase

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderBase.__init__(self, api_version, idp)
        self._allow_additional = False
        self._required += [['clientID', 'client_id'], ['clientSecret', 'client_secret']]

    def validate(self):
        ''' validate this idp instance '''
        IdentityProviderBase.validate(self)
        if self.challenge:
            raise errors.AnsibleFilterError("|failed provider {0} does not "
                                            "allow challenge authentication".format(self.__class__.__name__))


class OpenIDIdentityProvider(IdentityProviderOauthBase):
    """ OpenIDIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderOauthBase.__init__(self, api_version, idp)
        self._required += [['claims'], ['urls']]
        self._optional += [['ca'],
                           ['extraScopes'],
                           ['extraAuthorizeParameters']]
        if 'claims' in self._idp and 'preferred_username' in self._idp['claims']:
            pref_user = self._idp['claims'].pop('preferred_username')
            self._idp['claims']['preferredUsername'] = pref_user
        if 'urls' in self._idp and 'user_info' in self._idp['urls']:
            user_info = self._idp['urls'].pop('user_info')
            self._idp['urls']['userInfo'] = user_info
        if 'extra_scopes' in self._idp:
            self._idp['extraScopes'] = self._idp.pop('extra_scopes')
        if 'extra_authorize_parameters' in self._idp:
            self._idp['extraAuthorizeParameters'] = self._idp.pop('extra_authorize_parameters')

        if 'extraAuthorizeParameters' in self._idp:
            if 'include_granted_scopes' in self._idp['extraAuthorizeParameters']:
                val = ansible_bool(self._idp['extraAuthorizeParameters'].pop('include_granted_scopes'))
                self._idp['extraAuthorizeParameters']['include_granted_scopes'] = val


    def validate(self):
        ''' validate this idp instance '''
        IdentityProviderOauthBase.validate(self)
        if not isinstance(self.provider['claims'], dict):
            raise errors.AnsibleFilterError("|failed claims for provider {0} "
                                            "must be a dictionary".format(self.__class__.__name__))

        if 'extraScopes' not in self.provider['extraScopes'] and not isinstance(self.provider['extraScopes'], list):
            raise errors.AnsibleFilterError("|failed extraScopes for provider "
                                            "{0} must be a list".format(self.__class__.__name__))
        if ('extraAuthorizeParameters' not in self.provider['extraAuthorizeParameters']
                and not  isinstance(self.provider['extraAuthorizeParameters'], dict)):
            raise errors.AnsibleFilterError("|failed extraAuthorizeParameters "
                                            "for provider {0} must be a dictionary".format(self.__class__.__name__))

        required_claims = ['id']
        optional_claims = ['email', 'name', 'preferredUsername']
        all_claims = required_claims + optional_claims

        for claim in required_claims:
            if claim in required_claims and claim not in self.provider['claims']:
                raise errors.AnsibleFilterError("|failed {0} claim missing "
                                                "for provider {1}".format(claim, self.__class__.__name__))

        for claim in all_claims:
            if claim in self.provider['claims'] and not isinstance(self.provider['claims'][claim], list):
                raise errors.AnsibleFilterError("|failed {0} claims for "
                                                "provider {1} must be a list".format(claim, self.__class__.__name__))

        unknown_claims = set(self.provider['claims'].keys()) - set(all_claims)
        if len(unknown_claims) > 0:
            raise errors.AnsibleFilterError("|failed provider {0} has unknown "
                                            "claims: {1}".format(self.__class__.__name__, ', '.join(unknown_claims)))

        if not isinstance(self.provider['urls'], dict):
            raise errors.AnsibleFilterError("|failed urls for provider {0} "
                                            "must be a dictionary".format(self.__class__.__name__))

        required_urls = ['authorize', 'token']
        optional_urls = ['userInfo']
        all_urls = required_urls + optional_urls

        for url in required_urls:
            if url not in self.provider['urls']:
                raise errors.AnsibleFilterError("|failed {0} url missing for "
                                                "provider {1}".format(url, self.__class__.__name__))

        unknown_urls = set(self.provider['urls'].keys()) - set(all_urls)
        if len(unknown_urls) > 0:
            raise errors.AnsibleFilterError("|failed provider {0} has unknown "
                                            "urls: {1}".format(self.__class__.__name__, ', '.join(unknown_urls)))


class GoogleIdentityProvider(IdentityProviderOauthBase):
    """ GoogleIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    def __init__(self, api_version, idp):
        IdentityProviderOauthBase.__init__(self, api_version, idp)
        self._optional += [['hostedDomain', 'hosted_domain']]


class GitHubIdentityProvider(IdentityProviderOauthBase):
    """ GitHubIdentityProvider

        Attributes:

        Args:
            api_version(str): OpenShift config version
            idp (dict): idp config dict

        Raises:
            AnsibleFilterError:
    """
    pass


class FilterModule(object):
    ''' Custom ansible filters for use by the openshift_master role'''

    @staticmethod
    def translate_idps(idps, api_version):
        ''' Translates a list of dictionaries into a valid identityProviders config '''
        idp_list = []

        if not isinstance(idps, list):
            raise errors.AnsibleFilterError("|failed expects to filter on a list of identity providers")
        for idp in idps:
            if not isinstance(idp, dict):
                raise errors.AnsibleFilterError("|failed identity providers must be a list of dictionaries")

            cur_module = sys.modules[__name__]
            idp_class = getattr(cur_module, idp['kind'], None)
            idp_inst = idp_class(api_version, idp) if idp_class is not None else IdentityProviderBase(api_version, idp)
            idp_inst.set_provider_items()
            idp_list.append(idp_inst)


        IdentityProviderBase.validate_idp_list(idp_list)
        return yaml.safe_dump([idp.to_dict() for idp in idp_list], default_flow_style=False)

    @staticmethod
    def validate_pcs_cluster(data, masters=None):
        ''' Validates output from "pcs status", ensuring that each master
            provided is online.
            Ex: data = ('...',
                        'PCSD Status:',
                        'master1.example.com: Online',
                        'master2.example.com: Online',
                        'master3.example.com: Online',
                        '...')
                masters = ['master1.example.com',
                           'master2.example.com',
                           'master3.example.com']
               returns True
        '''
        if not issubclass(type(data), basestring):
            raise errors.AnsibleFilterError("|failed expects data is a string or unicode")
        if not issubclass(type(masters), list):
            raise errors.AnsibleFilterError("|failed expects masters is a list")
        valid = True
        for master in masters:
            if "{0}: Online".format(master) not in data:
                valid = False
        return valid

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {"translate_idps": self.translate_idps,
                "validate_pcs_cluster": self.validate_pcs_cluster}
