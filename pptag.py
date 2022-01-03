#!/usr/bin/env python
## python 3

# pip install watchdog

import sys
import getopt
import logging
import urllib
import time
import os
from datetime import datetime, date, timedelta
from threading import Timer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from exif.exifread.tags import DEFAULT_STOP_TAG, FIELD_TYPES
from exif.exifread import process_file, exif_log, __version__
from OneShotQueueTimer import OneShotQueueTimer
from plexUsers import plexUsers
from lightroomTags import parse_xmp_for_lightroom_tags
from photoElement import PhotoElement

from config import ppTagConfig

logger = exif_log.get_logger()

doUpdate = []
firstRun = ppTagConfig.FORCE_RUN_AT_START

# plex
p = None

# timer
t = None

def updateMetadata(item, tags, rating):

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
    #logging.debug("  updateMetaData: tagQuery is '%s'" % tagQuery)

    data = p.fetchPlexApi("/library/metadata/%s%s" %(item, tagQuery), "PUT")

def getdata(filename):

    detailed = True
    stop_tag = DEFAULT_STOP_TAG
    debug = False
    strict = False
    color = False

    #exif_log.setup_logger(debug, color)

    try:
        filename = ppTagConfig.PHOTOS_LIBRARY_PATH + filename
        img_file = open(str(filename), 'rb')

        data = process_file(img_file, stop_tag=stop_tag, details=detailed, strict=strict, debug=debug)

        img_file.close()

        if not data:
            logging.info("No EXIF information for '%s'" % filename)
            return None

        if 'JPEGThumbnail' in data:
            del data['JPEGThumbnail']
        if 'TIFFThumbnail' in data:
            del data['TIFFThumbnail']
    except IOError:
        logging.debug("'%s' is unreadable" % filename)
        return None
    except:
        logging.error("Exif process_file error: '%s'" % filename)
        return None

    return data

def getXMP(data):
    XMP = None
    if 'Image ApplicationNotes' in data:
        try:
            xml = data['Image ApplicationNotes'].printable
            XMP = parse_xmp_for_lightroom_tags(xml)
        except:
            logging.error("Unable to parse XMP")

    return XMP

def updateTagsAndRating(key, filename):
    data = getdata(filename)
    if not data:
        return

    parsedXMP = getXMP(data)
    if parsedXMP:
        logging.info("Updating Tags and Rating: '%s'" % filename)
        updateMetadata(key, parsedXMP['tags'], int(parsedXMP['rating'])*2)
    else:
        logging.info("No XMP data for '%s'" % filename)

def parseExifAndTags(filename):
    data = getdata(filename)
    if not data:
        return None

    parsedXMP = getXMP(data)
    if not parsedXMP:
        parsedXMP = {}
        parsedXMP['rating'] = 0
        parsedXMP['tags'] = []

    date = datetime.today().date()
    if 'EXIF DateTimeOriginal' in data:
        date = datetime.strptime(data['EXIF DateTimeOriginal'].printable, '%Y:%m:%d %H:%M:%S').date()
    else:
        datetimeModified = datetime.fromtimestamp(os.path.getmtime(filename))
        date = datetimeModified.date()
        
    return PhotoElement(filename, date, parsedXMP['tags'], parsedXMP['rating'])

def triggerProcess():
    global t
    t.start()

def uniqify(seq):
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())

def fetchPhotosAndProcess():
    global firstRun

    if firstRun:
        # if a complete update on startup is requested loop through all photos
        loopThroughAllPhotos()
    else:
        # else fetch all photos based on date
        if fetchAndProcessByDate():
            # failed so loop through all photos
            loopThroughAllPhotos()

def fetchAndProcessByDate():
    global doUpdate
    doUpdateTemp = uniqify(doUpdate)
    doUpdate = []

    photoGroups = {}
    # first group all photos by date
    for filepath in doUpdateTemp:
        photoElement = parseExifAndTags(filepath)
        if photoElement:
            # this has exif data
            date = photoElement.date()
            if date in photoGroups.keys():
                photoGroups[date].append(photoElement)
            else:
                photoGroups[date] = [photoElement]
        else: # missing or not a photo
            doUpdateTemp.remove(filepath)

    for date in photoGroups.keys():
        #print(date)
        fromTimecode = int(datetime.strptime(date.isoformat(), '%Y-%m-%d').timestamp())
        toTimecode = int((datetime.strptime(date.isoformat(), '%Y-%m-%d') + timedelta(days=1)).timestamp())-1

        toDo = True
        start = 0
        size = 1000

        # Make a key list of all pics in the date range
        plexData = {}
        if p.photoSection:
            while toDo:
                url = "/library/sections/" + str(p.photoSection) + "/all?originallyAvailableAt%3E=" + str(fromTimecode) + "&originallyAvailableAt%3C=" + str(toTimecode) + "&X-Plex-Container-Start=%i&X-Plex-Container-Size=%i" % (start, size)
                metadata = p.fetchPlexApi(url)
                container = metadata["MediaContainer"]
                if 'Metadata' not in container:
                   # no photos in this time range (probably wrong section)
                   break
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

                    plexData[src] = key

        # Update the pics that changed in the date range
        for photo in photoGroups[date]:
            path = photo.path()
            # make sure path seperator is equal in plex and ppTag
            if "/" in ppTagConfig.PHOTOS_LIBRARY_PATH_PLEX:
                path = path.replace("\\","/")
            if path in plexData.keys():
                logging.info("Updating modified file '%s'" % path)
                updateMetadata(plexData[path], photo.tags(), photo.rating()*2)
                photoGroups[date].remove(photo)
                doUpdateTemp.remove(path)

    # if we failed to process something then try a full scan
    if len(doUpdateTemp):
        logging.warning("Some updated files were not found by date range.")
        doUpdate = [*doUpdate, *doUpdateTemp]
        return True

    # after the loop we maybe have new or modifed files which was blocked before so trigger again
    if len(doUpdate):
        triggerProcess()
    
    return False

def loopThroughAllPhotos():
    global doUpdate
    global firstRun
    doUpdateTemp = uniqify(doUpdate)
    doUpdate = []
    toDo = True
    start = 0
    size = 1000
    #print('loop through all, started %i' % int(time.time()))
    if p.photoSection:
        while toDo:
            url = "/library/sections/" + str(p.photoSection) + "/all?clusterZoomLevel=1&X-Plex-Container-Start=%i&X-Plex-Container-Size=%i" % (start, size)
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

                # make sure path seperator is equal in plex and ppTag
                if "\\" in ppTagConfig.PHOTOS_LIBRARY_PATH:
                    src = src.replace("/","\\")
                if src in doUpdateTemp or firstRun:

                    # update tags and rating
                    # print(key)
                    # print(src)
                    updateTagsAndRating(key, src)
                    try:
                        doUpdateTemp.remove(src)
                    except:
                        pass # ok if missing, probably firstRun
                    if not firstRun and len(doUpdateTemp) == 0:
                        toDo = False
                        break

    if not firstRun:
        for src in doUpdateTemp:
            logging.info("Skipped file not found in this section '%s'" % src)		 
    
    # after the loop we maybe have new or modifed files which was blocked before so trigger again
    if len(doUpdate):
        triggerProcess()

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
		# check if file belongs to monitored section
                for folder in p.photoLocations:
                    if event.src_path.startswith(folder):
                        # put file into forced update list
                        pptag_path=event.src_path.replace(ppTagConfig.PHOTOS_LIBRARY_PATH,"", 1)
                        if pptag_path not in doUpdate:
                            logging.info("Queued for update: '%s'", event.src_path)
                            doUpdate.append(pptag_path)
                            triggerProcess()
                        return
                logging.debug("Ignored file in wrong location: '%s'" % event.src_path)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':

    if ppTagConfig.LOG_LEVEL is None or ppTagConfig.LOG_LEVEL == '':
         ppTagConfig.LOG_LEVEL = 'CRITICAL'
    logging.basicConfig(level=getattr(logging,ppTagConfig.LOG_LEVEL), format='%(asctime)s %(levelname)s - %(message)s')

    # setup observer
    observer = Observer()
    observer.schedule(PhotoHandler(), path=ppTagConfig.PHOTOS_LIBRARY_PATH, recursive=True)

    # setup timer
    # wait 120 sec after change was detected
    t = OneShotQueueTimer(120, fetchPhotosAndProcess)

    p = plexUsers()

    # run at startup
    fetchPhotosAndProcess()

    # now start the observer
    observer.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
