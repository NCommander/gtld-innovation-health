#!/usr/bin/env pyhton3
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

'''Dumps all the nameservers seen in a given zone with their quantity'''

import argparse
import operator

import gtld_data
from gtld_data import gtld_db

def main():
    parser = argparse.ArgumentParser()
    #parser.add_argument('zonefile', help='Zonefile to load')
    parser.add_argument('--origin', help="Origin of the zone file")
    parser.add_argument('--parking-nameservers', help='Parking nameservers', default='data/parking_nameservers.txt')
    parser.add_argument('--blocking-nameservers', help='Blocking nameservers', default='data/blocking_nameservers.txt')
    parser.add_argument('--reverse-parking-ptrs', help='Parking PTR Domains', default='data/reverse_parking_ptrs.txt')
    parser.add_argument('--reverse-expired-ptrs', help='Expired PTR Domains', default='data/reverse_expired_ptrs.txt')
    parser.add_argument('--other-inactive-nameservers', help='Other Inactive nameservers list', default='data/other_inactive_nameservers.txt')
    args = parser.parse_args()

    print("Connecting database ...")
    gtld_data.gtld_db.connect()

    print("Loading zone data, this may take a moment")
    gtld_db.database_connection.begin()
    cursor = gtld_db.database_connection.cursor()
    zone_data = gtld_data.ZoneData.load_from_db(cursor, 1)


    zone_processor = gtld_data.ZoneProcessor(zone_data)
    zone_processor.load_parked_domains_list(args.parking_nameservers)
    zone_processor.load_blocked_domains_list(args.blocking_nameservers)
    zone_processor.load_known_expired_ptrs(args.reverse_expired_ptrs)
    zone_processor.load_known_parked_ptrs(args.reverse_parking_ptrs)
    zone_processor.load_other_inactive_list(args.other_inactive_nameservers)
    zone_processor.process_zone_data()

    print("Unique domains: " + str(len(zone_data.domains)))
    print("Loaded " + str(len(zone_processor.known_parked_nameservers)) + " Known Parked Domains")
    print("Loaded " + str(len(zone_processor.known_parked_ptrs)) + " Known Parked PTRs")
    print("Loaded " + str(len(zone_processor.known_blocked_nameservers)) + " Known Blocked Domains")
    print("Loaded " + str(len(zone_processor.known_expired_ptrs)) + " Known Expired PTRs")
    print()
    print("Domain Report:")
    print("  NO_RDATA: " +str(len(zone_processor.no_ns_rdata)))
    print("  PARKED:  " + str(len(zone_processor.parked_domains)))
    print("  PTR_PARKED: " + str(len(zone_processor.reverse_parked_domains)))
    print("  PTR_EXPIRED: " + str(len(zone_processor.reverse_expired_domains)))
    print("  BLOCKED: " + str(len(zone_processor.blocked_domains)))
    print("  OTHER_INACTIVE: " + str(len(zone_processor.other_inactive_nameservers)))
    print("  UNKNOWN: " + str(len(zone_processor.unknown_status_domains)))

if __name__ == "__main__":
    main()
