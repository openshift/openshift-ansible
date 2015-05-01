#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4

''' The purpose of this module is to contain small utility functions.
'''

import re

def normalize_dnsname(name, padding=10):
    ''' The purpose of this function is to return a dns name with zero padding,
        so that it sorts properly (as a human would expect).

        Example: name=ex-lrg-node10.prod.rhcloud.com
        Returns: ex-lrg-node0000000010.prod.rhcloud.com

        Example Usage:
            sorted(['a3.example.com', 'a10.example.com', 'a1.example.com'],
                   key=normalize_dnsname)

        Returns: ['a1.example.com', 'a3.example.com', 'a10.example.com']
    '''
    parts = re.split(r'(\d+)', name)
    retval = []
    for part in parts:
        if re.match(r'^\d+$', part):
            retval.append(part.zfill(padding))
        else:
            retval.append(part)

    return ''.join(retval)
