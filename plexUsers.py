## python 3
# pip install plexapi
# pip install xmltodict

import http.client
import xmltodict
import json
import urllib
import sys
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from plexapi.myplex import MyPlexDevice
from uuid import uuid3, NAMESPACE_URL

class userData(object):
    """a simple class that holds some user data"""
    id = ""
    uuid = ""
    title = ""
    pin = ""
    token = ""

    def __init__(self, id, uuid, title, pin):
        self.id = id
        self.uuid = uuid
        self.title = title
        self.pin = pin

    def setToken(self, token):
        self.token = token

class plexUsers():

    ####################### Change HERE #######################
    #if you do not have a token you have to supply your credentials
    PLEX_LOGIN = ''
    PLEX_PASS = ''
    # if you already have a token pass it here
    PLEX_TOKEN = ''
    # the plex server url
    PLEX_URL = 'http://192.168.0.200:32400'
    # provide the usernames for which the rating should be updated
    # when users have a pin we need this, otherwise set it to ''
    USERDATA = { 'user': '1234' }

    # for the access tokens we need the exact server name
    SERVERNAME = 'plexserver'

    # path of the photo library in plex
    PHOTOS_LIBRARY_PATH = '/share/Photos/'

    ###########################################################

    def fetchPlexApi(self, path='', method='GET', getFormPlextv=False, token=PLEX_TOKEN, params=None):
        """a helper function that fetches data from and put data to the plex server"""
        headers = {'X-Plex-Token': token,
                'Accept': 'application/json'}
        if getFormPlextv:
            url = 'plex.tv'
            connection = http.client.HTTPSConnection(url)
        else:
            url = self.PLEX_URL.rstrip('/').replace('http://','')
            connection = http.client.HTTPConnection(url)

        try:
            if method.upper() == 'GET':
                pass
            elif method.upper() == 'POST':
                headers.update({'Content-type': 'application/x-www-form-urlencoded'})
                pass
            elif method.upper() == 'PUT':
                pass
            elif method.upper() == 'DELETE':
                pass
            else:
                print("Invalid request method provided: {method}".format(method=method))
                connection.close()
                return

            connection.request(method.upper(), path , params, headers)
            response = connection.getresponse()
            r = response.read()
            contentType = response.getheader('Content-Type')
            status = response.status
            connection.close()

            if response and len(r):
                if 'application/json' in contentType:
                    return json.loads(r)
                elif 'application/xml' in contentType:
                    return xmltodict.parse(r)
                else:
                    return r
            else:
                return r

        except Exception as e:
            connection.close()
            print("Error fetching from Plex API: {err}".format(err=e))

    def getAccessTokenForUser(self):
        for user in self.users:
            params = urllib.parse.urlencode({'pin': user.pin, 'X-Plex-Client-Identifier': self.clientId})
            data = self.fetchPlexApi('/api/v2/home/users/{uuid}/switch'.format(uuid=user.uuid), 'POST', True, self.PLEX_TOKEN, params)
            if 'authToken' in data:
                authToken = data['authToken']
                data = self.fetchPlexApi('/api/resources?includeHttps=1&includeRelay=1&X-Plex-Client-Identifier={clientid}'.format(clientid=self.clientId), 'GET', True, authToken)
                for device in data['MediaContainer']['Device']:
                    if isinstance(device, dict):
                        if device.get('@provides') == 'server' and device.get('@name') == self.SERVERNAME:
                            self.serverId = device.get('@clientIdentifier')
                            user.setToken(device.get('@accessToken'))
                            break

    def __init__(self):
        ## some initial tests
        if len(self.PLEX_TOKEN) == 0:
            # get a token
            try:
                account = MyPlexAccount(self.PLEX_LOGIN, self.PLEX_PASS)
            except Exception as e:
                raise("Error fetching from Plex API: {err}".format(err=e))
            # print the Token and message to enter it here
            print('use this token')
            print (account.authenticationToken)
            print('and put it into this file PLEX_TOKEN: plexUsers.py')
            raise

        # some lists for data
        self.users = list()
        self.photoSections = list()
        self.serverId = ''

        # creating the client id
        self.clientId = uuid3(NAMESPACE_URL, "pptag").hex

        self.plex = PlexServer(self.PLEX_URL, self.PLEX_TOKEN)


        apiUsers = self.fetchPlexApi("/api/home/users","GET",True)

        for user in apiUsers['MediaContainer']['User']:
            if user['@title'] in self.USERDATA.keys():
                pin = self.USERDATA.get(user['@title'])
                u = userData(user['@id'],user['@uuid'],user['@title'], pin)
                self.users.append(u)

        self.getAccessTokenForUser()

        for user in self.users:
            if user.token == '':
                print('no token found for user {user}'.format(user=user.title))
                self.users.remove(user)
            # else:
            #     print(user.title)
            #     print(user.token)

        # print (plex.machineIdentifier)
        for section in self.plex.library.sections():
            if section.type == 'photo':
                self.photoSections.append(section.key)

        # for playlist in self.plex.playlists():
        #     if playlist.isPhoto:
        #         print(playlist.smart)
