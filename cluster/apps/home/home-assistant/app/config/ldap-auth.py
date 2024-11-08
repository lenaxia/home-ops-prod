#!/usr/bin/env python
# ldap-auth-ad.py - authenticate Home Assistant against AD via LDAP
# Based on Rechner Fox's ldap-auth.py
# Original found at https://gist.github.com/rechner/57c123d243b8adb83ccb1dc94c80847f

import os
import sys
import argparse
import logging
from ldap3 import Server, Connection, ALL
from ldap3.utils.conv import escape_bytes, escape_filter_chars

# Configure logging
LOG_FILE = '/tmp/ldap-auth.log'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Quick and dirty print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Authenticate Home Assistant against AD via LDAP')
parser.add_argument('--ldap-server', required=True, help='LDAP server address')
parser.add_argument('--ldap-basedn', required=True, help='LDAP base DN')
parser.add_argument('--ldap-userscn', required=True, help='LDAP users container name')
parser.add_argument('--ldap-groupcn', required=True, help='LDAP groups container name')
parser.add_argument('--ldap-group', required=True, help='LDAP group for permissions')
parser.add_argument('--ldap-admin-group', required=True, help='LDAP group for administrators')
parser.add_argument('--ldap-helper-user', required=True, help='LDAP helper user')
parser.add_argument('--ldap-helper-pass', required=True, help='LDAP helper user password')
args = parser.parse_args()

# Ensure all required environment variables are set
username = os.environ.get('username')
password = os.environ.get('password')
if not all([username, password]):
    logging.error("Need username and password environment variables!")
    eprint("Need username and password environment variables!")
    exit(1)

# Extract command-line arguments
SERVER = args.ldap_server
BASEDN = args.ldap_basedn
USERSCN = args.ldap_userscn
GROUPCN = args.ldap_groupcn
GROUP = args.ldap_group
ADMINGROUP = args.ldap_admin_group
HELPERUSER = args.ldap_helper_user
HELPERPASS = args.ldap_helper_pass

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

# Escape the username for safe use in LDAP filter
safe_username = escape_filter_chars(username)
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
    logging.info(f"Search success: username {username}, result {conn.entries}")
    user_dn = conn.entries[0].entry_dn
    user_displayName = conn.entries[0].displayName.value if conn.entries[0].displayName else None
    user_memberOf = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []
else:
    logging.error(f"Search for username {username} yielded empty result")
    eprint(f"Search for username {username} yielded empty result")
    exit(1)

# Check if the user is part of the administrators group
is_admin = ADMINGROUP in user_memberOf
logging.info(f"User {username} is an admin: {is_admin}")

# Check if the user is part of the permissions group
is_permitted = PERMISSIONS_GROUP in user_memberOf
logging.info(f"User {username} is permitted: {is_permitted}")

# Ensure the user is part of the permissions group
if not is_permitted:
    logging.error(f"User {username} is not part of the required permissions group: {PERMISSIONS_GROUP}")
    eprint(f"User {username} is not part of the required permissions group: {PERMISSIONS_GROUP}")
    exit(1)

# Attempt to bind as the user
try:
    conn.rebind(user=user_dn, password=password)
    logging.info(f"Bind as {username} successful")
except Exception as e:
    logging.error(f"Bind as {username} failed: {e}")
    eprint(f"Bind as {username} failed: {e}")
    exit(1)

# Print the user's display name and group
print(f"name = {user_displayName}")
print(f"group = {'system-admin' if is_admin else 'system-users'}")

logging.info(f"{username} authenticated successfully")
eprint(f"{username} authenticated successfully")
exit(0)
