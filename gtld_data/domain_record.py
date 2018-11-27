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

from gtld_data.config import gtld_lookup_config
from gtld_data.domain_status import DomainStatus

import dns.resolver
import dns.rdatatype
import dns.reversename

class DomainRecord(object):
    def __hash__(self):
        return hash(self.domain_name)

    def __init__(self, name):
        self.domain_name = name
        self.nameservers = set()
        self.status = DomainStatus.UNKNOWN
        self.records = {}
        self.reverse_lookup_ptrs = set()

    def lookup_nameservers(self):
        '''Looks up the nameservers for a given domain

        This is only needed if we're directly querying a domain against our
        lists. Normally we can get this information from the zone file we're
        working again'''

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = gtld_lookup_config.upstream_resolvers

        answers = resolver.query(self.domain_name, 'NS')
        for rdata in answers:
            self.nameservers.add(rdata)
    
    def get_records(self, record_type, refresh=False):
        '''Gets a record type for this domain
        
        Returns True if the records were looked up, False if cached responses
        were given
        '''

        # If we already have records, ignore the request unless forced
        if refresh is False:
            records = self.records.get(record_type, None)
            if records is not None:
                return records

        # Go get the records
        self.records[record_type] = set()

        try:
            resolver = dns.resolver.Resolver(configure=False)
            resolver.nameservers = gtld_lookup_config.upstream_resolvers
            answers = resolver.query(self.domain_name, record_type)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            # Record doesn't exist, return an empty set
            return self.records[record_type]

        for rdata in answers:
            self.records[record_type].add(rdata.to_text())

        return self.records[record_type]

    def reverse_lookup(self, refresh=False):
        '''Does a reverse lookup of this domain; all A and AAAA records are pulled, and ptrs are populated'''

        # If we already have reverse records, ignore the request unless refresh is set
        if refresh is False:
            if len(self.reverse_lookup_ptrs) != 0:
                return self.reverse_lookup_ptrs

        # A/AAAA records may not exist
        a_records = self.get_records(dns.rdatatype.A)
        aaaa_records = self.get_records(dns.rdatatype.AAAA)

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = gtld_lookup_config.upstream_resolvers

        queries = set()

        # Create DomainRecords for the reverse lookups
        for record in a_records:
            queries.add(DomainRecord(dns.reversename.from_address(record).to_text()))

        for record in aaaa_records:
            queries.add(DomainRecord(dns.reversename.from_address(record).to_text()))

        for query in queries:
            # We may get NXDOMAIN responses here
            try:
                records = query.get_records("PTR")
                for record in records:
                    self.reverse_lookup_ptrs.add(record)
            except dns.resolver.NoAnswer:
                continue
            except dns.resolver.NXDOMAIN:
                continue
        
        return self.reverse_lookup_ptrs
