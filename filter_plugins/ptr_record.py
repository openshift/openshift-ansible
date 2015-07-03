#!/usr/bin/python

# FIXME all of these filters assume /24 subnets
# and are pretty basic

def subnet(ip):
    # Returns the subnet in CIDR format
    # FIXME we need the netmask here!
    # FIXME assuming /24
    index = ip.rfind('.')
    if index > 0:
        return ip[:index] + '.0/24'
    else:
        return ip

def subnet_name(subnet):
    # Returns a subnet "name" from a CIDR subnet definition
    # e.g. "192.168.1.0/24" -> "192.168.1"
    # FIXME assuming /24 ! need to do the real thing
    index = subnet.rfind('.')
    if index > 0:
        return subnet[:index]
    else:
        return subnet

def ptr_record(ip):
    # From a string representing an IPv4 address, get only the last byte:
    #   X.Y.Z.A  ->  A
    # Doesn't perform any real checks.
    # Meant to be useful while building DNS PTR records e.g.
    # for the zone Z.Y.X.in-addr.arpa.
    index = ip.rfind('.')
    if index > 0:
        return ip[index+1:]
    else:
        return ip

def reverse_zone(subnet):
    # From "192.168.1" it returns "1.168.192.in-addr.arpa"
    zone = subnet.split('.')
    zone.reverse()
    return '.'.join(zone) + ".in-addr.arpa"

class FilterModule(object):
    def filters(self):
        return {
            'subnet': subnet,
            'subnet_name': subnet_name,
            'ptr_record': ptr_record,
            'reverse_zone': reverse_zone
        }

# vim: set et ts=4 sw=4 :
