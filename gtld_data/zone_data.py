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
from gtld_data.nameserver_record import NameserverRecord

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
        zd.parsed_zone = dns.zone.from_file(file_name, origin=origin, relativize=False)
        zd.origin = origin
        zd.process_loaded_zone()
        return zd

    @classmethod
    def load_from_db(cls, db_id):
        zd = ZoneData()
        
    def to_db(self, cursor):
        '''Stores zone data in the database'''

        # Create zone file entry and our PK entry
        print("Writing to database ...")
        zone_file_insert = """INSERT INTO zone_files (origin, soa) VALUES (?, ?) RETURNING id"""
        cursor.execute(zone_file_insert, (self.origin, self.soa))
        self.db_id = int(cursor.fetchone()[0])

    def process_loaded_zone(self):
        '''Processes parsed zone data'''
        # Get our SOA
        soa_record = list(self.parsed_zone.iterate_rdatas(dns.rdatatype.SOA))[0]
        self.soa = int(soa_record[2].serial)
        records = list(self.parsed_zone.iterate_rdatas(dns.rdatatype.NS))

        # Write the zonefile record to the database
        cursor = gtld_db.database_connection.cursor()
        gtld_db.database_connection.begin()
        self.to_db(cursor)

        # We loop twice to handle adding the nameservers in a single go
        for rr in records:
            # See if we've seen this nameserver, and increment its count
            nameserver_txt = rr[2].to_text()
            nameserver_obj = self.known_nameservers.get(nameserver_txt, None)
            if nameserver_obj is None:
                nameserver_obj = NameserverRecord(nameserver_txt)
                self.known_nameservers[nameserver_txt] = nameserver_obj
            self.known_nameservers[nameserver_txt].increment_count()

        # Add all nameservers to the database
        for _, nameserver in self.known_nameservers.items():
            nameserver._zonefile_id = self.db_id
            nameserver.to_db(cursor)

        # Now process the domains
        for rr in records:
            full_domain_name = rr[0].to_text() + "." + self.origin
            nameserver_txt = rr[2].to_text()

            # First document the domains
            domain = self.domains.get(full_domain_name, None)
            if domain is None:
                self.domains[full_domain_name] = DomainRecord(full_domain_name)
                domain = self.domains[full_domain_name]

            # This is ugly, but we need the nameserver record from above.
            nameserver_obj = self.known_nameservers[nameserver_txt]
            domain.nameservers.add(nameserver_obj)

        # Write our list of domains to the database
        for _, value in self.domains.items():
            value._zonefile_id = self.db_id
            value.to_db(cursor)

        gtld_db.database_connection.commit()
