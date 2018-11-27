# Copyright 2018 Michael Casadevall <michael@casadevall.pro>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import dns.zone
import dns.rdatatype

from gtld_data.domain_status import DomainStatus
from gtld_data.domain_record import DomainRecord

class ZoneData(object):
    '''Holds reference data for the zone and useful modules for it'''
    def __init__(self, origin=None):
        self.origin = None
        self.parsed_zone = None
        self.domains = {}
        self.known_nameservers = {}

    @classmethod
    def load_from_file(cls, file_name, origin=None):
        zd = ZoneData()
        zd.parsed_zone = dns.zone.from_file(file_name, origin=origin)
        zd.origin = origin
        zd.process_loaded_zone()
        return zd

    def process_loaded_zone(self):
        '''Processes parsed zone data'''
        records = list(self.parsed_zone.iterate_rdatas(dns.rdatatype.NS))
        for rr in records:
            full_domain_name = rr[0].to_text() + "." + self.origin

            # First document the domains
            domain = self.domains.get(full_domain_name, None)
            if domain is None:
                self.domains[full_domain_name] = DomainRecord(full_domain_name)

            ns_text = rr[2].to_text()
            self.domains[full_domain_name].nameservers.add(ns_text)
        
            # Then see if we've seen this nameserver, and increment its count
            nameserver = self.known_nameservers.get(ns_text, None)
            if nameserver is None:
                self.known_nameservers[ns_text] = {}
                self.known_nameservers[ns_text]['count'] = 0

            self.known_nameservers[ns_text]['count'] = \
                self.known_nameservers[ns_text]['count'] + 1

