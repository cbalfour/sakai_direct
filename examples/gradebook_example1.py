#!/usr/bin/env python3

import os
import sys
sys.path.append('.')
from sakai_direct import Sakai, SakaiSite, SakaiGradebook

try:
    sakai_url = os.environ['SAKAI_URL']
except KeyError as e:
    sakai_url = input('Enter URL (https://site.domain/direct): ')

try:
    sakai_username = os.environ['SAKAI_USERNAME']
except KeyError as e:
    sakai_username = input('Enter username: ')

try:
    sakai_passwd = os.environ['SAKAI_PASSWORD']
except KeyError as e:
    sakai_passwd = getpass.getpass('Enter password: ')

try:
    site_id = os.environ['SAKAI_SITE_ID']
except KeyError as e:
    site_id = input('Enter Site ID: ')

try:
    assignment_name = os.environ['SAKAI_ASSIGNMENT_NAME']
except KeyError as e:
    assignment_name = input('Enter assignment name: ')

sakai = Sakai(sakai_url)

sakai.login(sakai_username, sakai_passwd)

site = SakaiSite(sakai, site_id)

membership = site.get_membership()
for member in membership.get_members():
    print (member)

gradebook = SakaiGradebook(sakai, site_id) 
for grade in gradebook.get_grades_for_assignment(assignment_name):
    print (grade)
