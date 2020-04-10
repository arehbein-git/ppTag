#!/usr/bin/env python
## python 3

# pip install watchdog

import sys
import getopt
import logging
import urllib
import time
from threading import Timer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from exif.exifread.tags import DEFAULT_STOP_TAG, FIELD_TYPES
from exif.exifread import process_file, exif_log, __version__
from OneShotQueueTimer import OneShotQueueTimer
from plexUsers import plexUsers
from lightroomTags import parse_xmp_for_lightroom_tags

from config import ppTagConfig

logger = exif_log.get_logger()

doUpdate = []
firstRun = ppTagConfig.FORCE_RUN_AT_START

# plex
p = None

# timer
t = None

def usage(exit_status):
    """Show command line usage."""
    msg = ('Usage: pptag.py\n'
           'Watch configured path for changes and start update the tags in plex\n'
    )
    print(msg)
    sys.exit(exit_status)

def updateMetadata(item, tags, rating):

    #headers = {'Accept': 'application/json'}

    # update rating
    for user in p.users:
        data = p.fetchPlexApi("/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%i" %(item, rating),"PUT", False, user.token)

    # write the metadata
    # prepare the tags
    tagQuery = "?"
    i = 0
    for tag in tags:
        tagQuery = tagQuery + "tag[%s].tag.tag=%s&" %(i, urllib.parse.quote(tag.encode('utf-8')))
        i = i + 1
    #print(tagQuery)

    data = p.fetchPlexApi("/library/metadata/%s%s" %(item, tagQuery), "PUT")

    # # get updatedAt attribute
    # connection = http.client.HTTPConnection(host)
    # headers = {'Accept': 'application/json'}

    # # get the metadata
    # connection.request("GET", "/library/metadata/%s" % item, None, headers)
    # response = connection.getresponse()
    # data = response.read()
    # connection.close()
    # metadata = json.loads(data)
    # updatedAt = int(metadata["MediaContainer"]["Metadata"][0]["updatedAt"])

def createSmartAlbum(title, tagOrSets=None, rating=0):
    # first get all available keys from plex
    tags = list()
    # we support just one photosection here
    if len(p.photoSections):
        section = p.photoSections[0]
    else:
        return
    #for section in p.photoSections:
    metadata = p.fetchPlexApi("/library/sections/" + section + "/tag?type=13&includeExternalMedia=1")
    tags.extend(metadata["MediaContainer"]["Directory"])

    tagQuery = ""
    for tagSet in tagOrSets:
        tagOr = ","
        seq = ()
        for tagItem in tags:
            if tagItem["title"].encode('utf-8') in tagSet:
                seq += (tagItem["key"].encode('utf-8'),)
        tagOr = tagOr.join(seq)
        if tagOr:
            tagQuery = tagQuery + "tag=%s&" % (tagOr)

    ratingQuery = ""
    if rating > 0:
        ratingQuery = "userRating%3E%3E"+"=%i&" % (rating * 2)

    if tagQuery or ratingQuery:
        url = "/playlists?uri=" + "server%3A%2F%2F" + p.serverId + "%2Fcom.plexapp.plugins.library%2Flibrary%2Fsections%2F" + section + "%2Fall%3F" + urllib.parse.quote(tagQuery) + urllib.parse.quote(ratingQuery) +  "sort%3ForiginallyAvailableAt%3Adesc&includeExternalMedia=1&title=" + urllib.parse.quote(title.encode("utf-8")) + "&smart=1&type=photo"
        for user in p.users:
            data = p.fetchPlexApi(url, "POST", False, user.token)

def updateTagsAndRating(key, filename):

    detailed = True
    stop_tag = DEFAULT_STOP_TAG
    debug = False
    strict = False
    color = False

    #exif_log.setup_logger(debug, color)

    filename = ppTagConfig.PHOTOS_LIBRARY_PATH + filename

    try:
        img_file = open(str(filename), 'rb')
    except IOError:
        print("'%s' is unreadable" % filename)
        return

    try:
        # get the tags
        data = process_file(img_file, stop_tag=stop_tag, details=detailed, strict=strict, debug=debug)

        if not data:
            print("No EXIF information found\n")
            return

        if 'JPEGThumbnail' in data:
            # logger.info('File has JPEG thumbnail')
            del data['JPEGThumbnail']
        if 'TIFFThumbnail' in data:
            # logger.info('File has TIFF thumbnail')
            del data['TIFFThumbnail']

        # xmp data
        if 'Image ApplicationNotes' in data:
            xml = data['Image ApplicationNotes'].printable

            parsedXMP = parse_xmp_for_lightroom_tags(xml)

            updateMetadata(key, parsedXMP['tags'], int(parsedXMP['rating'])*2)

        # if 'Image Copyright' in data:
        #     print("Copyright : %s", data['Image Copyright'].printable)

        # if 'EXIF DateTimeOriginal' in data:
        #     print(datetime.ParseDate(data['EXIF DateTimeOriginal'].printable))
    except:
        # it is a corrupt file (exif/xmp)
        return


def triggerLoopThroughAllPhotos():
    global t
    t.start()

def uniqify(seq):
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return keys.keys()


def loopThroughAllPhotos():
    global doUpdate
    global firstRun
    doUpdateTemp = uniqify(doUpdate)
    doUpdate = []
    toDo = True
    start = 0
    size = 100
    #print('loop through all, started %i' % int(time.time()))
    while toDo:
        if len(p.photoSections):
            url = "/library/sections/" + p.photoSections[0] + "/all?clusterZoomLevel=1&X-Plex-Container-Start=%i&X-Plex-Container-Size=%i" % (start, size)
            metadata = p.fetchPlexApi(url)
            container = metadata["MediaContainer"]
            elements = container["Metadata"]
            totalSize = container["totalSize"]
            offset = container["offset"]
            size = container["size"]
            start = start + size
            if totalSize-offset-size == 0:
                toDo = False
            # loop through all elements
            for photo in elements:
                mediaType = photo["type"]
                if mediaType != "photo":
                    continue
                key = photo["ratingKey"]
                src = photo["Media"][0]["Part"][0]["file"].replace(ppTagConfig.PHOTOS_LIBRARY_PATH_PLEX,"", 1)

                if src in doUpdateTemp or firstRun:

                    # update tags and rating
                    # print(key)
                    # print(src)
                    updateTagsAndRating(key, src)

    
    # after the loop we maybe have new or modifed files which was blocked before so trigger again
    if len(doUpdate):
        triggerLoopThroughAllPhotos()
        #print("change detected while processing, retrigger")
    #print('loop through all, done %i' % int(time.time()))
    firstRun = False


class PhotoHandler(PatternMatchingEventHandler):
    patterns=["*"]
    ignore_patterns=["*thumb*"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        if (event.event_type == 'modified' or event.event_type ==  'created' or event.event_type == 'moved'):
            if not event.is_directory:
                # put file into forced update list
                doUpdate.append(event.src_path.replace(ppTagConfig.PHOTOS_LIBRARY_PATH,"", 1))
                triggerLoopThroughAllPhotos()

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':

    # setup observer
    observer = Observer()
    observer.schedule(PhotoHandler(), path=ppTagConfig.PHOTOS_LIBRARY_PATH, recursive=True)

    # setup timer
    # wait 120 sec after change was detected
    t = OneShotQueueTimer(120, loopThroughAllPhotos)

    p = plexUsers()

    # run at startup
    loopThroughAllPhotos()

    # now start the observer
    observer.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

