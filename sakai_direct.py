#!/usr/bin/env python

# Sakai direct API client

import requests
import json
from requests.models import RequestsJSONDecodeError
from datetime import datetime
from typing import List, Optional, Dict, Mapping

class CacheFileNotFoundError(Exception): 
    pass

class NoGradebookError(Exception):
    pass

class AssignmentNotFoundError(Exception):
    pass

class SiteNotFoundError(Exception):
    pass

def convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp/1000.0) 

class Sakai:

    def __init__(self, url: str) -> None:
        self.url = url
        self._cookiejar = requests.cookies.RequestsCookieJar()

    def login(self, username: str, password: str) -> None:
        self.__username = username
        payload =  { '_username': username, '_password': password }
        r = requests.post(self.url + '/session', data=payload)
        self._cookiejar = r.cookies

    def is_active_session(self) -> bool:
        r = requests.get(self.url + '/session.json', cookies=self._cookiejar)
        data = r.json()
        session = data['session_collection'][0]
        if session['active'] == True and session['userId']:
            return True
        return False


    def get_sites(self, course_only=True) -> Dict:
        sites = {}
        r = requests.get(self.url + '/site.json', cookies=self._cookiejar)
        data = r.json()
        for site_data in data['site_collection']:
            site_type = site_data['type']
            if course_only and site_type != 'course': continue
            site_id = site_data['id']
            try:
                site_title = site_data['title']
            except:
                site_title = None
            sites[site_id] = { 'site_title': site_title, 'site_type': site_type } 

        return sites

    def get_assignments(self, site_id: str) -> Dict:
        assignments = {}
        r = requests.get(f'{self.url}/assignment/site/{site_id}.json', cookies=self._cookiejar)
        data = r.json()
        for assignment_data in data['assignment_collection']:
            assignment_id = assignment_data['id']
            assignment_title = assignment_data['title']
            assignments[assignment_id] = { 'assignment_title': assignment_title }
        return assignments

    def get_membership(self, site_id: str) -> Dict:
        members = {}
        url = f'{self.url}/membership/site/{site_id}.json'


        data = None
        try:
            with open(f'{site_id}-members.json') as data_file:
                data = json.load(data_file)
        except FileNotFoundError:
                r = requests.get(url, cookies=self._cookiejar)
                data = r.json()

        for member_data in data['membership_collection']:
            user_id = member_data['userId']
            display_id = member_data['userDisplayId']
            role = member_data['memberRole']
            members[user_id] = { 'username': display_id, 'role': role }
        return members

    def get_site_term(self, site_id: str) -> int:
        url = f'{self.url}/site/{site_id}.json'
        r = requests.get(url, cookies=self._cookiejar)
        data = r.json()
        #print (data['props'])
        site_term = data['props']['term']
        return int(site_term)

    def get_gradebook(self, site_id: str) -> Dict:
        gradebook = {}

        url = f'{self.url}/gradebook/site/{site_id}.json'

        data = None
        try:
            with open(f'{site_id}-gradebook.json') as data_file:
                data = json.load(data_file)
        except FileNotFoundError:
                r = requests.get(url, cookies=self._cookiejar)
                if r.status_code != 200:
                    raise Exception("No gradebook")
                data = r.json()

        for grade_data in data['assignments']:
            assignment_name = grade_data['itemName']
            user_id = grade_data['userId']
            if not assignment_name in gradebook.keys():
                gradebook[assignment_name] = {}

            if not user_id in gradebook[assignment_name].keys():
                gradebook[assignment_name][user_id] = { 'grade': grade_data['grade'] } 

        return gradebook 

    def get_cookie_jar(self):
        return self._cookiejar

    def get_session_id(self):
        return self._cookiejar['JSESSIONID']

class SakaiSites:

    def __init__(self, sakai: Sakai) -> None:
        self.sakai = sakai
        self.__get_sites()
        
    def __get_sites(self) -> None:

        url = f'{self.sakai.url}/site.json'
        self.sites= []

        # Sakai has a limit on the number of sites it returns 
        # per request. Depending on the number of sites the 
        # user has access to, it might be necessary to make 
        # a number of requests.

        for i in range(0, 1000, 50):

            payload = { '_start': i, '_limit': i + 50 }
            r = requests.get(
                url, 
                cookies=self.sakai.get_cookie_jar(), 
                params = payload
            )

            data = r.json()

            if len(data['site_collection']) == 0: break

            for site_data in data['site_collection']:
                site_id = site_data['id']
                site = SakaiSite(self.sakai, site_id)
                if not site in self.sites:
                    self.sites.append(site)

            for key in data.keys():
                    
                if not hasattr(self, key):
                    setattr(self, key, data[key])
                else:
                    if key == 'site_collection':
                        self.site_collection += data['site_collection']

    def get_sites(self) -> List:
        return self.sites

    def get_site(self, site_id: str) -> str:
        site =  next((site for site in self.sites if site.get_id() == site_id), None)
        if site:
            return site 
        raise SiteNotFoundError('Site not found.')


class SakaiSite:

    def __init__(self, sakai: Sakai, site_id: str) -> None:
        self.site_id = site_id
        self.sakai = sakai
        self.__get_site()

    def __get_site(self) -> None:
        url = f'{self.sakai.url}/site/{self.site_id}.json'
        r = requests.get(url, cookies = self.sakai.get_cookie_jar())
        data = r.json()
        for key in data.keys():
            setattr(self, '_' + key, data[key])

    @property
    def term(self) -> Optional[int]:
        if 'term' in self._props.keys():
            return int(self._props['term'])
        return None

    @property
    def created_time(self) -> datetime:
        return convert_timestamp(self._createdTime['time'])

    @property
    def contact_email(self) -> str:
        return self._contactEmail

    @property
    def contact_name(self) -> str:
        return self._contactName

    @property
    def description(self) -> str:
        return self._description

    @property
    def short_description(self) -> str:
        return self._shortDescription

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def title(self) -> str:
        return self._title

    @property
    def type(self) -> str:
        return self._type

    @property
    def is_published(self) -> bool:
        return self._published

    @property
    def id(self) -> str:
        return self._id

    @property
    def modified_time(self) -> datetime:
        return convert_timestamp(self._modified_time['time'])

    def get_gradebook(self):
        return SakaiGradebook(self.sakai, self.site_id)

    def get_membership(self):
        return SakaiMembership(self.sakai, self.site_id)

    def get_assignments(self):
        return SakaiAssignments(self.sakai, self.site_id)

    def __repr__(self):
        return f'{self.title} ({self.id})'

class SakaiAssignment:

    def __init__(self, sakai: Sakai, assignment_id: str, assignment_data=None):
        self.sakai = sakai
        self.assignment_id = assignment_id
        self.assignment_data = assignment_data
        self.__get_assignment()

    def __get_assignment(self) -> None:
        if not self.assignment_data:
            url = f'{self.sakai.url}/assignment/item/{self.assignment_id}.json'
            r = requests.get(url, cookies=self.sakai.get_cookie_jar())
            if r.status_code != 200:
                raise AssignmentNotFoundError("Assignment not found.")
            data = r.json()
        else:
            data = self.assignment_data

        for key in data.keys():
            setattr(self, key, data[key])

    def __eq__(self, other) -> bool:
        if self.id == other.id:
            return True
        return False

    def get_id(self) -> str:
        return self.id

    def get_grade_scale(self) -> str:
        return self.gradeScale

    def get_grade_scale_max_points(self) -> float:
        return float(self.gradeScaleMaxPoints)

    def get_due_time(self) -> datetime:
        return convert_timestamp(self.dueTime['time'])

    def get_title(self) -> str:
        return self.title

    def get_status(self) -> str:
        return self.status

    def is_draft(self) -> bool:
        return self.draft

    def get_close_time(self) -> datetime:
        return convert_timestamp(self.closeTime['time'])

    def get_time_last_modified(self) -> datetime:
        return convert_timestamp(self.timeLastModified['time'])

    def is_resubmittable(self) -> bool:
        return self.allowResubmission

    def get_submission_type(self) -> str:
        return self.submissionType

    def get_status(self) -> str:
        return self.status

    def __repr__(self) -> str:
        return f'{self.title}'


class SakaiAssignments:

    def __init__(self, sakai, site_id):
        self.site_id = site_id
        self.sakai = sakai
        self.__get_assignments()
        
    def __get_assignments(self):

        # This url seems to fetch all assignments andnot just those
        # in the site specified
        url = f'{self.sakai.url}/assignment/site/{self.site_id}.json'

        r = requests.get(url, cookies=self.sakai.get_cookie_jar())
        try:
            data = r.json()
        except RequestsJSONDecodeError as e:
            data = { 'assignment_collection': [] }
            
        for key in data.keys():
            setattr(self, key, data[key])

        self.assignments = []
        for assignment_data in self.assignment_collection:
            assignment_id = assignment_data['id']
            assignment = SakaiAssignment(self.sakai, assignment_id, assignment_data=assignment_data)
            if not assignment in self.assignments:
                self.assignments.append(assignment)

    def get_assignments(self) -> List:
        return self.assignments

    def get_assignment_by_name(self, name: str) -> SakaiAssignment:
        assignment =  next((assignment for assignment in self.assignments if assignment.get_title() == name), None)
        if not assignment:
            raise AssignmentNotFoundError("Assignment not found")

        return assignment


class SakaiMembership:

    def __init__(self, sakai: Sakai, site_id: str) -> None:
        self.site_id = site_id
        self.sakai = sakai
        self.__get_membership()
        
    def __get_membership(self) -> None:

        url = f'{self.sakai.url}/membership/site/{self.site_id}.json'

        r = requests.get(url, cookies=self.sakai.get_cookie_jar())
        data = r.json()
            
        for key in data.keys():
            setattr(self, key, data[key])

        self.members = []
        for member_data in self.membership_collection:
            member_id = member_data['userId']
            member = SakaiMember(self.sakai, member_id, member_data)
            if not member in self.members:
                self.members.append(member)

    def get_members_by_userid(self, user_id: str) -> List:
        return [ member for member in self.members if member.userId.lower() == user_id.lower() ]


    def get_member_by_userid(self, user_id: str) -> str:
        member =  next((member for member in self.members if member.userId == user_id), None)
        return member

    def get_members_by_usereid(self, user_eid: str) -> List:
        return [ member for member in self.members if member.userEid.lower() == user_eid.lower() ]

    def get_members(self) -> List:
        return self.members


# We are not able to query /direct/member so we need to provide the data
# as a parameter

class SakaiMember:

    def __init__(
        self, 
        sakai: Sakai, 
        member_id: str, 
        member_data: Optional[Mapping[str, str]] = None
    ):
        self.sakai = sakai
        self.member_id = member_id
        if member_data:
            self.member_data = member_data
        else:
            self.member_data = {}
        self.__get_member()

    def __get_member(self) -> None:
        for key in self.member_data.keys():
            setattr(self, '_' + key, self.member_data[key])

    def __eq__(self, other):
        if self._userId.lower() == other._userId.lower():
            return True
        elif self._userEid.lower() == other._userEid.lower():
            return True
        return False

    @property
    def name(self) -> str:
        return self._entityTitle

    @property
    def user_eid(self) -> str:
        return self._userEid

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def email(self) -> str:
        return self._userEmail

    @property
    def display_name(self) -> str:
        return self._DisplayName

    @property
    def role(self) -> str:
        return self._memberRole

    @property
    def last_login_time(self) -> datetime:
        return convert_timestamp(self._lastLoginTime)

    @property
    def user_eid(self) -> str:
        return self._userEid

    @property
    def user_id(self) -> str:
        return self._userId

    def __repr__(self):
        return f'{self.name} ({self.user_eid })'

class SakaiGradebook:

    def __init__(self, sakai: Sakai, site_id: str) -> None:
        self.site_id = site_id
        self.sakai = sakai
        self.__get_gradebook()
        
    def __get_gradebook(self) -> None:

        url = f'{self.sakai.url}/gradebook/site/{self.site_id}.json'

        r = requests.get(url, cookies=self.sakai.get_cookie_jar())
        if r.status_code != 200:
            raise NoGradebookError('No gradebook found')
        data = r.json()
            
        for key in data.keys():
            setattr(self, '_' + key, data[key])

    @property
    def assignment_names(self) -> List:
        assignment_names = []
        for assignment in self._assignments:
            if not assignment['itemName'] in assignment_names:
                assignment_names.append(assignment['itemName'])
        return assignment_names
        

    def get_grades_for_assignment(self, assignment_name: str) -> List:
        return [ grade for grade in self._assignments if grade['itemName'] == assignment_name ]

    def get_grades_for_user(self, user_id: str) -> List:
        return [ grade for grade in self._assignments if grade['userId'] == user_id ]

