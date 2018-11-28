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
from gtld_data.db import gtld_db

class ZoneData(object):
    '''Holds reference data for the zone and useful modules for it'''
    def __init__(self, origin=None):
        self.db_id = None
        self.origin = None
        self.soa = None
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

    def to_db(self):
        '''Stores zone data in the database'''

        # Create zone file entry and our PK entry
        print("Writing to database ...")
        zone_file_insert = """INSERT INTO zone_files (origin, soa) VALUES (?, ?) RETURNING id"""
        cursor = gtld_db.database_connection.cursor()
        gtld_db.database_connection.begin()
        cursor.execute(zone_file_insert, (self.origin, self.soa))
        self.db_id = int(cursor.fetchone()[0])

        # Load the list of nameservers and append a database id to the dict
        nameserver_insert = """INSERT INTO nameservers (zone_file, nameserver, domain_count) VALUES (?, ?, ?) RETURNING id"""
        for key, value in self.known_nameservers.items():
            cursor.execute(nameserver_insert, (self.db_id, key, value['count']))
            value['db_id'] = int(cursor.fetchone()[0])

        # Load our list of domains, then link it to the nameserver
        domain_insert = """INSERT INTO domains (zone_file, domain_name, status) VALUES (?, ?, ?) RETURNING id"""
        domain_nameservers = """INSERT INTO domain_nameservers(domain_id, nameserver_id) VALUES (?, ?)"""
        for _, value in self.domains.items():
            # First the domain
            cursor.execute(domain_insert, (self.db_id, value.domain_name, "UNKNOWN"))
            value.db_id = int(cursor.fetchone()[0])

            # Now the link table
            for nameserver in value.nameservers:
                nameserver_record = self.known_nameservers.get(nameserver)
                cursor.execute(domain_nameservers, (value.db_id, nameserver_record['db_id']))
        gtld_db.database_connection.commit()

    def process_loaded_zone(self):
        '''Processes parsed zone data'''
        # Get our SOA
        soa_record = list(self.parsed_zone.iterate_rdatas(dns.rdatatype.SOA))[0]
        self.soa = int(soa_record[2].serial)
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

        # Write it out to the database
        self.to_db()