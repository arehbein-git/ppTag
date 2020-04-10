#!/usr/bin/env python

class ppTagConfig():
    """A simple class holding the config for ppTag"""
    ####################### Change HERE #######################
    #if you do not have a token you have to supply your credentials
    PLEX_LOGIN = ''
    PLEX_PASS = ''

    # if you already have a token pass it here
    PLEX_TOKEN = ''

    # the plex server url
    PLEX_URL = 'http://192.168.0.200:32400' # including http(s) (local url is best)

    # provide the usernames for which the rating should be updated
    # when users have a pin we need this, otherwise set it to ''
    USERDATA = { 'user': '1234' }

    # for the access tokens we need the exact server name
    SERVERNAME = 'plexserver'

    # path of the photo library in plex (absolute path)
    PHOTOS_LIBRARY_PATH_PLEX = '/<some path>/'

    # for the correct path creation we need the path to the
    # photo library from the view of the script (absolute path)
    # Linux/Mac: "/<some path>/"
    # Windows: "C:\\some folder\\some folder" # (paths need escaping)
    PHOTOS_LIBRARY_PATH = "/<some path>/"

    # start an update at the start of the script
    FORCE_RUN_AT_START = True
    ###########################################################
