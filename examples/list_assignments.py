#!/usr/bin/env python

# Print out a list of the sites and their associated assignments

import os
import sys
import getpass
sys.path.append('.')
from sakai_direct import Sakai, SakaiSites

def main():

    try:

        sakai_url = os.environ['SAKAI_URL']
    except KeyError as e:
        sakai_url = input('Enter URL (http://host.domain/direct): ')

    try:
        user = os.environ['SAKAI_USERNAME']
    except KeyError as e:
        user = input('Enter username: ')

    try:
        passwd = os.environ['SAKAI_PASSWORD']
    except KeyError as e:
        passwd = getpass.getpass('Enter password: ')

    sakai = Sakai(sakai_url)
    if not sakai.is_active_session():
        sakai.login(user, passwd)

    sites = SakaiSites(sakai)
    for site in sites.get_sites():
        print (site)
        print ('-' * 20)

        assignments = site.get_assignments()
        for assignment in assignments.get_assignments():
            print (f'\t{assignment}')

if __name__ == '__main__':

    main()
