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

import dns.resolver
from gtld_data.domain_status import DomainStatus

class ZoneProcessor(object):
    '''Processes a zone file looking for parked or blocked domains'''
    def __init__(self, zone_data):
        self.zone_data = zone_data
        self.no_ns_rdata = set()
        self.parked_domains = set()
        self.blocked_domains = set()
        self.reverse_parked_domains = set()
        self.reverse_expired_domains = set()
        self.other_inactive_nameservers = set()
        self.unknown_status_domains = set()
        self.known_parked_nameservers = []
        self.known_blocked_nameservers = []
        self.known_other_inactive_nameservers = []
        self.known_expired_ptrs = []
        self.known_parked_ptrs = []

    def process_domain_list(self, domain_list_file):
        '''Parses and loads the domain list'''
        domain_list = []

        with open(domain_list_file, 'r') as f:
            for line in f:
                # Skip blanks and comments
                if len(line.rstrip()) == 0 or line[0] == "#":
                    continue

                domain_list.append(re.compile(line.rstrip()))
        return domain_list

    def load_parked_domains_list(self, known_parked_ns_file):
        '''Loads the set of parked domains'''
        self.known_parked_nameservers = self.process_domain_list(known_parked_ns_file)

    def load_blocked_domains_list(self, known_blocked_ns_file):
        '''Loads the set of parked domains'''
        self.known_blocked_nameservers = self.process_domain_list(known_blocked_ns_file)

    def load_known_expired_ptrs(self, known_expired_ptrs_file):
        self.known_expired_ptrs = self.process_domain_list(known_expired_ptrs_file)

    def load_known_parked_ptrs(self, known_parked_ptrs_file):
        self.known_parked_ptrs = self.process_domain_list(known_parked_ptrs_file)

    def load_other_inactive_list(self, known_other_inactive_file):
        self.known_other_inactive_nameservers = self.process_domain_list(known_other_inactive_file)

    def process_zone_data(self):
        '''Processes the zone data file'''

        def check_nameserver_against_list(domain_list, nameserver):
            for domain in domain_list:
                if domain.search(nameserver) is not None:
                    return True
            
            return False

        # Let's walk the domain list, and see what we need to still process
        domains = copy.deepcopy(self.zone_data.domains)

        # The order this is handled in is determined to be most accurate/specific reason we can handle
        # In general, we'll handle known domains (via seen NS records), then PTRs, the other list, then
        # anything that didn't return rdata (since we might know something from the master zone file)

        # Handle Parked Domains
        for domain in domains:
            for nameserver in domain.nameservers:
                if check_nameserver_against_list(self.known_parked_nameservers, nameserver.nameserver) is True:
                    self.parked_domains.add(domain)
                    break
        
        # Remove the domains we don't need process further
        for domain in self.parked_domains:
            domains.remove(domain)

        # Handle blocked domains
        for domain in domains:
            for nameserver in domain.nameservers:
                if check_nameserver_against_list(self.known_blocked_nameservers, nameserver.nameserver) is True:
                    self.blocked_domains.add(domain)
                    break

        for domain in self.blocked_domains:
            domains.remove(domain)

        # Handle Reverse Parked PTRs
        for domain in domains:
            for ptr in domain.reverse_lookup_ptrs:
                if check_nameserver_against_list(self.known_parked_ptrs, ptr.reverse_lookup_name) is True:
                    self.reverse_parked_domains.add(domain)
                    break

        for domain in self.reverse_parked_domains:
            domains.remove(domain)

        # Handle Expired PTRs
        for domain in domains:
            for ptr in domain.reverse_lookup_ptrs:
                if check_nameserver_against_list(self.known_expired_ptrs, ptr.reverse_lookup_name) is True:
                    self.reverse_expired_domains.add(domain)
                    break

        for domain in self.reverse_expired_domains:
            domains.remove(domain)

        # Remove anything from the other list now
        for domain in domains:
            for nameserver in domain.nameservers:
                if check_nameserver_against_list(self.known_other_inactive_nameservers, nameserver.nameserver) is True:
                    self.other_inactive_nameservers.add(domain)
                    break
        
        # Remove the domains we don't need process further
        for domain in self.other_inactive_nameservers:
            domains.remove(domain)

        # Get rid of anything that didn't return a nameserver; we do this now because some results
        # are determined directly from the master zonefile list, and not through domain rdata
        for domain in domains:
            if len(domain.records) == 0:
                self.no_ns_rdata.add(domain)

        for domain in self.no_ns_rdata:
            domains.remove(domain)

        self.unknown_status_domains = domains
        return

    def get_reverse_zone_information(self, cursor, domains):
        '''Returns all reverse zone information for a given domain'''
        reverse_zones = {}
        for domain in domains.values():
            try:
                print("Resolving " + domain.domain_name + " ...")
                reverse_zones[domain.domain_name] = domain.reverse_lookup(cursor)
            except dns.resolver.NoAnswer:
                continue

        return reverse_zones
