# check_pdns_stale
Monitoring Plugin to check for stale domains on PowerDNS secondary servers.

## Purpose
When running PowerDNS in a Primary-Secondary (old names: Master-Slave) setup, the DNS replication happens over the DNS protocol. 

Note: Check out https://www.claudiokuenzler.com/blog/844/powerdns-master-slave-dns-replication-mysql-backend for an overview and the difference between "Native" and "DNS" replicaiton.

This works fine for zone changes and for newly created domains in the Primary; new domains are automatically created on the Secondary server(s) when `autosecondary=yes` is configured. 

There is one downside though: Zones (domains) deleted on the Primary are not replicated to the Secondary server(s). The Secondary server(s) still have the deleted domains and servers as authoritative server. This is what we call a "stale domain": The domain was deleted on the Primary but the Secondary server(s) don't know about it.

This monitoring plugin helps to identify these stale zones/domains.


## Requirements

### Python3 modules
Requires the following Python3 modules:
- mysql.connector
- dnspython

These can be installed either using `pip3`:

```
pip3 install mysql.connector dnspython
```

Or by using prepared Python3 packages in your OS. Example for Ubuntu:

```
apt-get install python3-mysql.connector python3-dnspython
```

### MySQL privileges
The MySQL user you use for the script needs SELECT privileges on the table "domains" in the "powerdns" database. Assuming your PowerDNS MySQL database is named "powerdns", you would use the following `GRANT` query:

```
mysql> GRANT SELECT ON powerdns.domains TO 'monitoring'@'localhost' IDENTIFIED BY 'secret';
```
