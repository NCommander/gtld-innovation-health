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

'''Holds the record of a domain'''

import copy
import re

from gtld_data.domain_status import DomainStatus

class ZoneProcessor(object):
    '''Processes a zone file looking for parked or blocked domains'''
    def __init__(self, zone_data):
        self.zone_data = zone_data
        self.parked_domains = set()
        self.blocked_domains = set()
        self.unknown_status_domains = set()
        self.known_parked_nameservers = []
        self.known_blocked_nameservers = []

    def process_domain_list(self, domain_list_file):
        '''Parses and loads the domain list'''
        domain_list = []

        with open(domain_list_file, 'r') as f:
            for line in f:
                # Skip blanks and comments
                if len(line) == 0 or line[0] == "#":
                    continue

                domain_list.append(re.compile(line.rstrip()))
        return domain_list

    def load_parked_domains_list(self, known_parked_ns_file):
        '''Loads the set of parked domains'''
        self.known_parked_nameservers = self.process_domain_list(known_parked_ns_file)

    def process_zone_data(self):
        '''Processes the zone data file'''

        def check_nameserver_against_list(domain_list, nameserver):
            for domain in domain_list:
                if domain.search(nameserver) is not None:
                    return True
            
            return False

        # Let's walk the domain list, and see what we need to still process
        domains = copy.deepcopy(self.zone_data.domains)
        for domain in domains.values():
            for nameserver in domain.nameservers:
                if check_nameserver_against_list(self.known_parked_nameservers, nameserver) is True:
                    self.parked_domains.add(domain)
                    break
        
        # Remove the domains we don't need process further
        for domain in self.parked_domains:
            del domains[domain.domain_name]

        for domain in self.blocked_domains:
            del domains[domain.domain_name]

        self.unknown_status_domains = domains
        return
