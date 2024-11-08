#!/usr/bin/env python
# ldap-auth-ad.py - authenticate Home Assistant against AD via LDAP
# Based on Rechner Fox's ldap-auth.py
# Original found at https://gist.github.com/rechner/57c123d243b8adb83ccb1dc94c80847f

import os
import sys
from ldap3 import Server, Connection, ALL
from ldap3.utils.conv import escape_bytes, escape_filter_chars

# Quick and dirty print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# XXX: Update these with settings appropriate to your environment:
# (all settings must be provided via environment variables)

# Environment variables for dynamic configuration
SERVER = os.environ.get('SERVER')
BASEDN = os.environ.get('BASEDN')
USERSCN = os.environ.get('USERSCN')
GROUPCN = os.environ.get('GROUPCN')
GROUP = os.environ.get('GROUP')
ADMINGROUP = os.environ.get('ADMINGROUP')
HELPERUSER = os.environ.get('HELPERUSER')
HELPERPASS = os.environ.get('HELPERPASS')

# Ensure all required environment variables are set
if not all([SERVER, BASEDN, USERSCN, GROUPCN, ADMINGROUP, HELPERUSER, HELPERPASS, os.environ.get('username'), os.environ.get('password')]):
    eprint("Need SERVER, BASEDN, USERSCN, GROUPCN, GROUP, ADMINGROUP, HELPERUSER, HELPERPASS, username, and password environment variables!")
    exit(1)

# Construct the permissions group DN
PERMISSIONS_GROUP = f"cn={GROUP},cn={GROUPCN},{BASEDN}"
print(f"{PERMISSIONS_GROUP}")

# Construct the administrators group DN
ADMINGROUP = f"cn={ADMINGROUP},cn={GROUPCN},{BASEDN}"
print(f"{ADMINGROUP}")

# Construct the helper account DN
HELPERDN = f"uid={HELPERUSER},cn={USERSCN},{BASEDN}"
print(f"{HELPERDN}")

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
except Exception as e:
    eprint("initial bind failed: {}".format(e))
    exit(1)

try:
    search = conn.search(BASEDN, FILTER, attributes=ATTRS.split(','))
except Exception as e:
    eprint("search failed: {}".format(e))
    exit(1)

if len(conn.entries) > 0:  # search is True on success regardless of result size
    eprint("search success: username {}, result {}".format(os.environ['username'], conn.entries))
    user_dn = conn.entries[0].entry_dn
    user_displayName = conn.entries[0].displayName.value if conn.entries[0].displayName else None
    user_memberOf = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []
else:
    eprint("search for username {} yielded empty result".format(os.environ['username']))
    exit(1)

# Check if the user is part of the administrators group
is_admin = ADMINGROUP in user_memberOf

# Check if the user is part of the permissions group
is_permitted = PERMISSIONS_GROUP in user_memberOf

# Ensure the user is part of the permissions group
if not is_permitted:
    eprint("User {} is not part of the required permissions group: {}".format(os.environ['username'], PERMISSIONS_GROUP))
    exit(1)

# Attempt to bind as the user
try:
    conn.rebind(user=user_dn, password=os.environ['password'])
except Exception as e:
    eprint("bind as {} failed: {}".format(os.environ['username'], e))
    exit(1)

# Print the user's display name and group
print("name = {}".format(user_displayName))
print("group = {}".format("system-admin" if is_admin else "system-users"))

eprint("{} authenticated successfully".format(os.environ['username']))
exit(0)
