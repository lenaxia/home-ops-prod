#!/usr/bin/env python
# ldap-auth-ad.py - authenticate Home Assistant against AD via LDAP
# Based on Rechner Fox's ldap-auth.py
# Original found at https://gist.github.com/rechner/57c123d243b8adb83ccb1dc94c80847f

import os
import sys
import logging
from ldap3 import Server, Connection, ALL
from ldap3.utils.conv import escape_bytes, escape_filter_chars

# Configure logging
LOG_FILE = '/config/logs/ldap-auth.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Quick and dirty print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# XXX: Update these with settings appropriate to your environment:
# (all settings must be provided via environment variables)

# Environment variables for dynamic configuration
SERVER = os.environ.get('LDAP_SERVER')
BASEDN = os.environ.get('LDAP_BASEDN')
USERSCN = os.environ.get('LDAP_USERSCN')
GROUPCN = os.environ.get('LDAP_GROUPCN')
GROUP = os.environ.get('LDAP_GROUP')
ADMINGROUP = os.environ.get('LDAP_ADMINGROUP')
HELPERUSER = os.environ.get('LDAP_HELPERUSER')
HELPERPASS = os.environ.get('LDAP_HELPERPASS')

# Ensure all required environment variables are set
if not all([SERVER, BASEDN, USERSCN, GROUPCN, ADMINGROUP, HELPERUSER, HELPERPASS, os.environ.get('username'), os.environ.get('password')]):
    logging.error("Need LDAP_SERVER, LDAP_BASEDN, LDAP_USERSCN, LDAP_GROUPCN, LDAP_GROUP, LDAP_ADMINGROUP, LDAP_HELPERUSER, LDAP_HELPERPASS, username, and password environment variables!")
    eprint("Need LDAP_SERVER, LDAP_BASEDN, LDAP_USERSCN, LDAP_GROUPCN, LDAP_GROUP, LDAP_ADMINGROUP, LDAP_HELPERUSER, LDAP_HELPERPASS, username, and password environment variables!")
    exit(1)

# Construct the permissions group DN
PERMISSIONS_GROUP = f"cn={GROUP},cn={GROUPCN},{BASEDN}"
logging.info(f"Permissions group DN: {PERMISSIONS_GROUP}")

# Construct the administrators group DN
ADMINGROUP = f"cn={ADMINGROUP},cn={GROUPCN},{BASEDN}"
logging.info(f"Administrators group DN: {ADMINGROUP}")

# Construct the helper account DN
HELPERDN = f"uid={HELPERUSER},cn={USERSCN},{BASEDN}"
logging.info(f"Helper account DN: {HELPERDN}")

TIMEOUT = 3

FILTER = """
    (&
        (objectClass=person)
        (|
            (uid={})
        )
    )"""

ATTRS = "distinguishedName,uid,displayName,mail,memberOf,cn"

## End config section

safe_username = escape_filter_chars(os.environ['username'])
FILTER = FILTER.format(safe_username)

server = Server(SERVER, get_info=ALL)
try:
    conn = Connection(server, HELPERDN, password=HELPERPASS, auto_bind=True, raise_exceptions=True)
    logging.info("Initial bind successful")
except Exception as e:
    logging.error(f"Initial bind failed: {e}")
    eprint(f"Initial bind failed: {e}")
    exit(1)

try:
    search = conn.search(BASEDN, FILTER, attributes=ATTRS.split(','))
    logging.info("Search successful")
except Exception as e:
    logging.error(f"Search failed: {e}")
    eprint(f"Search failed: {e}")
    exit(1)

if len(conn.entries) > 0:  # search is True on success regardless of result size
    logging.info(f"Search success: username {os.environ['username']}, result {conn.entries}")
    user_dn = conn.entries[0].entry_dn
    user_displayName = conn.entries[0].displayName.value if conn.entries[0].displayName else None
    user_memberOf = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []
else:
    logging.error(f"Search for username {os.environ['username']} yielded empty result")
    eprint(f"Search for username {os.environ['username']} yielded empty result")
    exit(1)

# Check if the user is part of the administrators group
is_admin = ADMINGROUP in user_memberOf
logging.info(f"User {os.environ['username']} is an admin: {is_admin}")

# Check if the user is part of the permissions group
is_permitted = PERMISSIONS_GROUP in user_memberOf
logging.info(f"User {os.environ['username']} is permitted: {is_permitted}")

# Ensure the user is part of the permissions group
if not is_permitted:
    logging.error(f"User {os.environ['username']} is not part of the required permissions group: {PERMISSIONS_GROUP}")
    eprint(f"User {os.environ['username']} is not part of the required permissions group: {PERMISSIONS_GROUP}")
    exit(1)

# Attempt to bind as the user
try:
    conn.rebind(user=user_dn, password=os.environ['password'])
    logging.info(f"Bind as {os.environ['username']} successful")
except Exception as e:
    logging.error(f"Bind as {os.environ['username']} failed: {e}")
    eprint(f"Bind as {os.environ['username']} failed: {e}")
    exit(1)

# Print the user's display name and group
print(f"name = {user_displayName}")
print(f"group = {'system-admin' if is_admin else 'system-users'}")

logging.info(f"{os.environ['username']} authenticated successfully")
eprint(f"{os.environ['username']} authenticated successfully")
exit(0)
