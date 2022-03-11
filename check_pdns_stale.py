#!/usr/bin/env python
######################################################################
# check_pdns_stale.py
#
# A monitoring plugin to be run on a PowerDNS secondary (old term: slave)
# server with a MySQL backend. The local domains are checked against the 
# primary PowerDNS server and if a stale domain is found, it is reported.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>. 
#
# Copyright (c) 2022 Claudio Kuenzler www.claudiokuenzler.com
#
# History:
# 20220310: Development and public release as v0.1
# 20220311: Fix error handling in MySQL connection
# 20220311: Improve plugin exit, add performance data
######################################################################
# version
version='0.2.0'

# imports
import argparse
import mysql.connector
from mysql.connector import errorcode
import dns.resolver
import socket
import sys

# defaults
dbname="powerdns"
dbhost="localhost"
debug=False

# Input parameters
description = "check_pdns_stale.py v%s - Monitoring Plugin for PowerDNS Secondary servers with MySQL backend" % version
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-H', '--dbhost', dest='dbhost', default="localhost", required=True, help='IP or Hostname of MySQL server used by this PDNS')
parser.add_argument('-u', '--dbuser', dest='dbuser', required=True, help='Username for MySQL')
parser.add_argument('-p', '--dbpass', dest='dbpass', required=True, help='Password for MySQL')
parser.add_argument('-d', '--dbname', dest='dbname', default="powerdns", help='PowerDNS database name (default: powerdns)')
parser.add_argument('-P', '--primary', dest='primary', required=True, help='IP or Hostname of primary PowerDNS server)')
parser.add_argument('--debug', dest='debug', action='store_true', help='Debug)')
args = parser.parse_args()

# Handle inputs, overwrite defaults
if (args.dbhost):
    dbhost=args.dbhost

if (args.dbuser):
    dbuser=args.dbuser

if (args.dbpass):
    dbpass=args.dbpass

if (args.dbname):
    dbname=args.dbname

if (args.primary):
    primary=args.primary

if (args.debug):
    debug=True
#################################################################################
# Functions
def systemexit(exit_status, output, perfdata):
    print("%s %s" % (output, perfdata))
    sys.exit(exit_status)
#################################################################################
# Do the check

try:
    cnx = mysql.connector.connect(user=dbuser, password=dbpass, host=dbhost, database=dbname)
except mysql.connector.Error as err:
    systemexit(2, "PDNS SECONDARY CRITICAL: {0}".format(err), "")

cursor = cnx.cursor()
cursor.execute("SELECT name FROM %s.domains" % dbname)
result = cursor.fetchall()
domaincount = len(result)

warndomains = []

# Set primary as resolver
resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = [socket.gethostbyname(primary)]

# For each domain, lookup the domain on the primary
for domain in result:
    domain = domain[0]
    if debug:
      print("Handling zone {}".format(domain))
    try:
        soaresult = resolver.query(domain, 'SOA')
    except:
        warndomains.append(domain)
        if debug:
          print("Unable to resolve SOA of {} on Primary ({}) -> marked as stale".format(domain, primary))
    else:
      if debug:
        for rdata in soaresult:
          print("Serial of {} is {} ".format(domain, rdata.serial))

cursor.close()
cnx.close()

warncount = len(warndomains)

if warncount > 0:
    output = "PDNS SECONDARY WARNING: Stale zones: %a" % warndomains
    perfdata = "|total_zones=%i;;;; stale_zones=%i;;;;" % (domaincount, warncount)
    systemexit(2, output, perfdata)
else:
    output = "PDNS SECONDARY OK: No stale zones on this secondary server"
    perfdata = "|total_zones=%i;;;; stale_zones=%i;;;;" % (domaincount, warncount)
    systemexit(0, output, perfdata)
#################################################################################
systemexit(3, "PDNS SECONDARY UNKNOWN: Should never reach that part", "")
