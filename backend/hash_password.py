#!/usr/bin/env python3
"""Print an AUTH_PASSWORD_HASH value. Usage: python hash_password.py [password]"""
import getpass
import sys

from auth import hash_password

pw = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Password: ")
print(hash_password(pw))
