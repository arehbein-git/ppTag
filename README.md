# pptag

Plex Photo Tagger

As the plex server is not compatible with xmp metadata inside photos, this python based app uses plex rest api to implement an update of all related metadata within plex with tags and rating of the xmp

## dependencies

* python 3
* watchdog
* ExifRead
* plexapi
* xmltodict

## what you need to change

### change values to fit your installation in plexUsers.py
    
´´´python

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
    SERVERNAME = 'plex'

    # path of the photo library in plex
    PHOTOS_LIBRARY_PATH = '/share/Photos'

´´´

For getting a valid token you can enter you login credentials and run the script.
It will then output this:

´´´

use this token
xxxxxxxxxxxxxxxxxxxxxxx
and put it into plexUsers.py file after PLEX_TOKEN: 

´´´

put the token into plexUsers.py

### change values to fit your installation in ppTag.py

Adjust the paths for the photos (for ppTag)

´´´python

    if system == "Linux":
    photosPath = "/Photos/" # Running in Docker
else:
    photosPath = "P:\\" # Windows

´´´

## how it works

pptag needs local access to the images that are part of the plex library. An observer is started to look for changes in the path of the library. If so, all changes are processed.

pptag fetches all users and tries to get an access token for the user. This is needed as the rating of images is user based.

Currently only one photo library is supported. 

Images are scanned for adobe lightroom tags and rating written to the XMP data in the images.

## Docker Container

You can use the provided docker file and docker-compose to run ppTag inside docker.
The Container needs to Volumes. One for the photos and the second for the app.
This way it is easy to make changes to the files (config)