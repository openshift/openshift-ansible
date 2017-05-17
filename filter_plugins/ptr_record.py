#!/usr/bin/python

'''
Filters to help work with bind DNS configuration files
'''

from netaddr import IPAddress, IPNetwork

class FilterModule(object):
    ''' Custom ansible filters of IP address and network handling
    '''

    @staticmethod
    def subnet(address):
        ''' Returns the subnet of an IP in CIDR format '''
        # We would need the netmask here! Using implicit prefix for now
        ipnet = IPNetwork(address, implicit_prefix=True)
        return str(ipnet)

    @staticmethod
    def subnet_name(network):
        ''' Get a nice name from a subnet definition in CDR format
            e.g. "192.168.1.129/24" -> "192.168.1.0"
        '''
        ipnet = IPNetwork(network)
        return str(ipnet.network)

    @staticmethod
    def ptr_record(address):
        ''' Return a reverse DNS lookup record for an IP address
            Meant to be useful while building DNS PTR records e.g.
              X.Y.Z.A  ->  A.Z.Y.X.in-addr.arpa.
        '''
        ipaddr = IPAddress(address)
        return ipaddr.reverse_dns

    @staticmethod
    def reverse_zone(network):
        ''' Get a nice name for a reverse zone name for a subnet
            e.g. "192.168.1.129/24" -> "0.1.168.192.in-addr.arpa"
        '''
        ipnet = IPNetwork(network, implicit_prefix=True)
        return ipnet.network.reverse_dns.rstrip('.')

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            'subnet': self.subnet,
            'subnet_name': self.subnet_name,
            'ptr_record': self.ptr_record,
            'reverse_zone': self.reverse_zone
        }

# vim: set et ts=4 sw=4 :
