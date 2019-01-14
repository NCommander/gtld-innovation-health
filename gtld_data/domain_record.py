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
from gtld_data.nameserver_record import NameserverRecord
from gtld_data.ptr_record import PtrRecord
from gtld_data.domain_rdata import DomainRData

import dns.resolver
import dns.rdatatype
import dns.reversename

class DomainRecord(object):
    def __hash__(self):
        return hash(self.domain_name)

    def __init__(self, name, zonefile_id=None):
        self._zonefile_id = None
        self.db_id = None
        self.domain_name = name
        self.nameservers = set()
        self.status = DomainStatus.UNKNOWN
        self.records = {}
        self.reverse_lookup_ptrs = set()

    def to_db(self, cursor):
        '''Stores domain record in the database'''
        domain_insert = """INSERT INTO domains (zone_file_id, domain_name, status) VALUES (?, ?, ?) RETURNING id"""
        domain_nameservers = """INSERT INTO domain_nameservers(domain_id, nameserver_id) VALUES (?, ?)"""

        # Save the domain record
        cursor.execute(domain_insert, (self._zonefile_id, self.domain_name, self.status.value))
        self.db_id = int(cursor.fetchone()[0])

        # And link nameserver records
        for nameserver in self.nameservers:
            cursor.execute(domain_nameservers, (self.db_id, nameserver.db_id))
            
        for ptr in self.reverse_lookup_ptrs:
            ptr._domain_id = self.db_id
            ptr.to_db(cursor)

        for _, record_type in self.records.items():
            for record in record_type:
                # It's possible the domain ID didn't get set on add record (this happens during testing)
                # so manually set it here when we write to the DB
                record._domain_id = self.db_id
                record.to_db(cursor)

    @classmethod
    def from_db(cls, cursor, db_id):
        domain_select = """SELECT id, zone_file_id, domain_name, status FROM domains WHERE id = ?"""
        domain_nameserver_ids = """SELECT nameserver_id FROM domain_nameservers WHERE domain_id = ?"""
        domain_ptr_ids = """SELECT ptr_record_id FROM domain_ptr_records WHERE domain_id = ?"""

        # Read in the domain record
        cursor.execute(domain_select, [int(db_id)])
        row = cursor.fetchone() # Needed to clear cache
        domain_obj = cls(None)
        domain_obj._db_row_to_self(row)

        # Read in domain records
        cursor.execute(domain_nameserver_ids, [domain_obj.db_id])
        rows = cursor.fetchall()
        for row in rows:
            domain_obj.nameservers.add(
                NameserverRecord.from_db(cursor, row[0])
            )

        # Read in domain records
        cursor.execute(domain_ptr_ids, [domain_obj.db_id])
        rows = cursor.fetchall()
        for row in rows:
            domain_obj.reverse_lookup_ptrs.add(
                PtrRecord.from_db(cursor, row[0])
            )

        # Read in RData
        rdata_objs = DomainRData.read_all_from_db_for_domain(cursor, domain_obj.db_id)
        for rdata in rdata_objs:
            domain_obj.add_record(cursor, rdata)

        return domain_obj

    @classmethod
    def read_all_from_db(cls, cursor, zonefile_id):
        '''Reads all nameservers for a given zonefile id'''
        domain_all_select = """SELECT id FROM domains WHERE zone_file_id = ?"""

        # This isn't a great way to do this, but I'm lazy
        cursor.execute(domain_all_select, [int(zonefile_id)])

        domain_set = set()
        rows = cursor.fetchall()

        for row in rows:
            domain_obj = cls.from_db(cursor, int(row[0]))
            domain_set.add(domain_obj)
        return domain_set

    def _db_row_to_self(self, db_dict):
        '''Converts db_dict to class data'''
        self.db_id = db_dict[0]
        self._zonefile_id = db_dict[1]
        self.domain_name = db_dict[2]
        self.status = DomainStatus(db_dict[3])

    def lookup_nameservers(self):
        '''Looks up the nameservers for a given domain

        This is only needed if we're directly querying a domain against our
        lists. Normally we can get this information from the zone file we're
        working again'''

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = gtld_lookup_config.upstream_resolvers

        answers = resolver.query(self.domain_name, 'NS')
        for rdata in answers:
            self.nameservers.add(NameserverRecord(self.domain_name, zonefile_id=self._zonefile_id))
    
    def add_record(self, cursor, rdata_obj):
        '''Adds a record to the internal data structure'''

        if rdata_obj._domain_id is None and self.db_id is not None:
            rdata_obj._domain_id = self.db_id
            rdata_obj.to_db(cursor)

        rdata_dict = self.records.get(rdata_obj.rrtype, None)
        if rdata_dict is None:
            self.records[rdata_obj.rrtype] = set()
        
        self.records[rdata_obj.rrtype].add(rdata_obj)

    def get_records(self, cursor, record_type, refresh=False):
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
            rdata_obj = DomainRData()
            rdata_obj.rrtype = record_type
            rdata_obj.rdata = rdata.to_text()
            self.add_record(cursor, rdata_obj)

        return self.records[record_type]

    def reverse_lookup(self, cursor, refresh=False):
        '''Does a reverse lookup of this domain; all A and AAAA records are pulled, and ptrs are populated'''

        # If we already have reverse records, ignore the request unless refresh is set
        if refresh is False:
            if len(self.reverse_lookup_ptrs) != 0:
                return self.reverse_lookup_ptrs

        # A/AAAA records may not exist
        a_records = self.get_records(cursor, "A")
        aaaa_records = self.get_records(cursor, "AAAA")

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = gtld_lookup_config.upstream_resolvers

        queries = set()

        # Create tuples with the ip and reverse lookup zone for the reverse lookups
        for record in a_records:
            queries.add((record.rdata, (dns.reversename.from_address(record.rdata).to_text())))
        for record in aaaa_records:
            queries.add((record.rdata, (dns.reversename.from_address(record.rdata).to_text())))

        for query in queries:
            # We may get NXDOMAIN responses here
            try:
                # Create a DomainRecord for the reverse zone
                reverse_record = DomainRecord(query[1], zonefile_id=self._zonefile_id)

                records = reverse_record.get_records(cursor, "PTR")
                for record in records:
                    ptr_obj = PtrRecord(query[0], record.rdata)
        
                    # If we're attached to a database, create the PtrRecord in the DB
                    if self._zonefile_id is not None:
                        ptr_obj._zonefile_id = self._zonefile_id
                        ptr_obj._domain_id = self.db_id
                        ptr_obj.to_db(cursor)
                    self.reverse_lookup_ptrs.add(ptr_obj)

            except dns.resolver.NoAnswer:
                continue
            except dns.resolver.NXDOMAIN:
                continue
        
        return self.reverse_lookup_ptrs
