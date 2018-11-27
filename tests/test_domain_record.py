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
