# pptag

Plex Photo Tagger

As the plex server is not compatible with xmp metadata inside photos, this python based app uses plex rest api to implement an update of all related metadata within plex with tags and rating of the xmp

## dependencies

* python 3
* watchdog
* plexapi
* xmltodict

## what you need to change

### change values to fit your installation in config.py
    
```python
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
    # Windows: "C:\\some folder\\some folder\\" # (paths need escaping)
    PHOTOS_LIBRARY_PATH = "/<some path>/"

    # start an update at the start of the script
    FORCE_RUN_AT_START = True
    ###########################################################
```

For getting a valid token you can enter you login credentials and run the script.
It will then output this:

```
use this token
xxxxxxxxxxxxxxxxxxxxxxx
and put it into the file config.py after PLEX_TOKEN:
```

## how it works

pptag needs local access to the images that are part of the plex library. An observer is started to look for changes in the path of the library. If so, all changes are processed. For this the Plex server needs to be set to automatically update all libraries, "Scan my library automatically". In addition you may select "Run a partial scan when changes are detected".

pptag fetches all users and tries to get an access token for the user. This is needed as the rating of images is user based.

Currently only one photo library is supported. 

Images are scanned for adobe lightroom tags and rating written to the XMP data in the images.

## Docker Container

You can use the provided docker file to build the image yourself or use the dockerhub versions arehbein/pptag.
The container needs one volumes for the photos:
```
<path to photolibrary>:/Photos
```
The config file should be mounted as readonly:
```
<path to config>/config.py:/app/pptag/config.py:ro
```


Run the image

```bash
docker run -v <path to photolibrary>:/Photos -v <path to config>/config.py:/app/pptag/config.py:ro -d arehbein/pptag
```

Use the provided docker-compose:
```bash
docker-compose up -d
```
