from datetime import datetime, date

class PhotoElement():
    """A Object holding the information of the photo"""

    _path = ""
    _date = datetime.today().date()
    _tags = []
    _rating = 0

    def __init__(self, path, date, tags, rating):
        """path: path of photo including filename, date: date photo was taken [datetime.date], tags: xmp tags [list], rating: 0-5"""
        self._path = path
        self._date = date
        self._tags = tags
        self._rating = rating
    
    def path(self):
        """returns the path of the photo"""
        return self._path
    
    def date(self):
        """returns the date of the photo"""
        return self._date
    
    def tags(self):
        """returns the tags of the photo"""
        return self._tags

    def rating(self):
        """returns the rating of the photo"""
        return self._rating
