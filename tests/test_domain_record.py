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
from gtld_data.domain_record import DomainRecord

class TestDomainRecord(unittest.TestCase):
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

    #def test_nxdomain_reverse_lookup(self):
    #    '''Test failure to reverse look up zone'''
    #    domain_record = DomainRecord("alexandria.casadevall.pro")
    #    reverse_ptrs = domain_record.reverse_lookup()
    #    self.assertGreater(len(reverse_ptrs), 0)

if __name__ == '__main__':
    unittest.main()
