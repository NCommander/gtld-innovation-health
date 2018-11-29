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

import unittest

import dns.rdatatype

from gtld_data import  gtld_db, gtld_lookup_config
from gtld_data.domain_record import DomainRecord

from tests.database_unit_test import DatabaseUnitTest

class TestDomainRecord(DatabaseUnitTest):
    def test_lookup_nameserver(self):
        '''Tests looking up nameservers'''
        domain_record = DomainRecord("casadevall.pro")
        domain_record.lookup_nameservers()
        self.assertGreater(len(domain_record.nameservers), 0)

    def test_zone_lookup(self):
        '''Tests looking up a domain record'''
        domain_record = DomainRecord("a.root-servers.net")
        a_records = domain_record.get_records(dns.rdatatype.A)
        self.assertGreater(len(a_records), 0)

        aaaa_records = domain_record.get_records(dns.rdatatype.AAAA)
        self.assertGreater(len(aaaa_records), 0)

    def test_valid_reverse_lookup(self):
        '''Tests looking up the reverse zone of a valid record'''
        domain_record = DomainRecord("casadevall.pro")
        reverse_ptrs = domain_record.reverse_lookup()
        self.assertGreater(len(reverse_ptrs), 0)

    def test_read_write_database(self):
        '''Test reading/writing records from the database'''
        gtld_db.database_connection.begin()
        cursor = gtld_db.database_connection.cursor()
        zd_id = self.create_zone_data(cursor)

        domain = DomainRecord('test.example.')
        domain._zonefile_id = zd_id
        domain.nameservers.add(
            self.create_nameserver_record(cursor, zd_id, "ns1.example.")
        )
        domain.nameservers.add(
            self.create_nameserver_record(cursor, zd_id, "ns2.example.")
        )

        domain.reverse_lookup_ptrs.add(
            self.create_ptr_record(cursor, zd_id, "10.10.10.1", "reverse.example")
        )
        domain.reverse_lookup_ptrs.add(
            self.create_ptr_record(cursor, zd_id, "10.10.10.2", "reverse2.example")
        )
        domain.reverse_lookup_ptrs.add(
            self.create_ptr_record(cursor, zd_id, "10.10.10.3", "reverse3.example")
        )
        domain.to_db(cursor)
        
        # Read back the object
        domain2 = DomainRecord.from_db(cursor, domain.db_id)
        self.assertEqual(domain.domain_name, domain2.domain_name)
        self.assertEqual(len(domain.nameservers), len(domain2.nameservers))
        self.assertEqual(len(domain.reverse_lookup_ptrs), len(domain2.reverse_lookup_ptrs))

    #def test_nxdomain_reverse_lookup(self):
    #    '''Test failure to reverse look up zone'''
    #    domain_record = DomainRecord("alexandria.casadevall.pro")
    #    reverse_ptrs = domain_record.reverse_lookup()
    #    self.assertGreater(len(reverse_ptrs), 0)

if __name__ == '__main__':
    unittest.main()
