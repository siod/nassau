from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import exists
from sqlalchemy import desc
from sqlalchemy import and_

from .models import (
    DBSession,
    Item,
    Torrent,
    Movie,
    Setting,
    )
import json
import feedparser
import re
import tmdbsimple
import copy
import datetime
import urllib
import urllib2

import logging
log = logging.getLogger(__name__)


@view_config(route_name='home', renderer='templates/home.pt')
def rootPage(request):
    try:
        one = DBSession.query(Item).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'one': one, 'project': 'nassau'}

@view_config(route_name='updateItem', request_method='PATCH', renderer='json')
def updateItem(request):
    try:
        item = DBSession.query(Item).filter(Item.id == request.matchdict['id']).first()
        if 'torrent_name' in request.params:
            item.torrent_name = request.params['torrent_name']
        if 'name' in request.params:
            item.name = request.params['name']
        if 'type' in request.params:
            item.type = int(request.params['type'])
        if 'status' in request.params:
            item.status = int(request.params['status'])
        if 'extracted_loc' in request.params:
            item.extracted_loc = request.params['extracted_loc']
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

tmdb = None
def setupTMDB():
    global tmdb
    if (tmdb == None):
        try:
            (api_key,) = DBSession.query(Setting.value).filter(Setting.name == 'tmdb_api_key').one()
            tmdb = tmdbsimple.TMDB(api_key)
        except NoResultFound:
            log.error('tmdb_api_key is missing from the database')
            raise Exception('Invalid Database')

def lookupMovie(details,maxResults = None):
    setupTMDB()
    search = tmdb.Search()
    response = search.movie(details)
    movieInfo = None
    if ( search.results == 0):
        log.warning("Unable to find " + str(details) + " on tmdb")
        return None

    if (len(search.results) == 1):
        movieInfo = search.results[0]
    elif (maxResults == None or maxResults <= len(search.results)):
        for x in search.results:
            movieInfo = search.results[0]
            break
    else:
        return None
    if (movieInfo == None):
        return None

    return Movie(movieInfo['title'],
            movieInfo['id'],
            datetime.datetime.strptime((movieInfo['release_date']),"%Y-%m-%d").date(),
            movieInfo['poster_path'],
            False,
            movieInfo['vote_average'])

def createMovie(title,year):
    movie = lookupMovie( { 'query' : title , 'year' : year})
    if (movie == None):
        log.info("Attempting to get movie without year")
        movie = lookupMovie( { 'query' : title },1)
        if (movie == None):
            log.warning("Creating movie without tmdb info")
            movie = Movie(title,None,datetime.date(year,1,1),'',False,None)
    if (movie.tmdb_id != None):
        #Check to see if the Movie is in the database, but has a slight variation on the name
        try:
            existingMovie = DBSession.query(Movie).filter(Movie.tmdb_id == movie.tmdb_id).one()
            return existingMovie.id
        except NoResultFound:
            pass
    DBSession.add(movie)
    DBSession.flush()
    DBSession.refresh(movie)
    return movie.id

movieRegex = re.compile(r'([A-Za-z\d\._-]+\.)((19|20)\d\d).*\.([0-9]{3,4}(p|P))\.')
def updateMovies():
    try:
        try:
            (moviesFeed,) = DBSession.query(Setting.value).filter(Setting.name == 'rss_url').one()
        except NoResultFound:
            log.error('rss_url is missing from the database')
            raise Exception('Invalid Database')

        movieInfo = feedparser.parse(moviesFeed)
        movieTorrents = []
        for x in movieInfo.entries:
            if (DBSession.query(exists().where(Torrent.name == x.title)).scalar() == 1):
                continue
            titleSearch = movieRegex.search(x.title)
            if (titleSearch == None):
                log.error("Regex failed to parse: " + x.title)
                log.error(repr(x))
                continue
            movieTitle = titleSearch.group(1)
            movieTitle = movieTitle.replace('.',' ')[:-1]
            movieYear = int(titleSearch.group(2))
            movieQuality = titleSearch.group(4)
            movieTorrents.append({
                'release_date' : movieYear,
                'title' : movieTitle,
                'quality' : movieQuality,
                'name' : x.title,
                'download_path' : x.link
                })
        for x in movieTorrents:
            try:
                torrent = DBSession.query(Torrent).filter(Torrent.decoded_name == x['title']).one()
                movie_id = torrent.movie_id
            except NoResultFound:
                movie_id = createMovie(x['title'],x['release_date'])
            newTorrent = Torrent(x['name'],x['title'],movie_id,x['download_path'],x['quality'].lower())
            DBSession.add(newTorrent)
        return True
    except DBAPIError:
        log.exception("Update movies caused an exception")
        return False

@view_config(route_name='update')
def update(Request):
    if (updateMovies()):
        return Response('Update finished successfully', content_type='text/plain', status_int=204)
    return Response('Update was unsuccessfull', content_type='text/plain', status_int=500)

def setupTorrentAuth():
    auth_settings = DBSession.query(Setting).filter(Setting.name.like("auth_%")).all()
    auth = dict()
    for x in auth_settings:
        auth[x.name[5:]] = x.value

    auth_handler = urllib2.HTTPDigestAuthHandler()
    auth_handler.add_password(realm=auth['realm'],
                                uri=auth['uri'],
                                user=auth['user'],
                                passwd=auth['passwd'])
    opener = urllib2.build_opener(auth_handler)
    urllib2.install_opener(opener)

def queueTorrentDownload(torrent,download_dir):
    try:
        try:
            (url,) = DBSession.query(Setting.value).filter(Setting.name == 'torrent_url').one()
        except NoResultFound:
            log.error('torrent_url is missing from the database')
            raise Exception('Invalid Database')

        setupTorrentAuth()
        options = urllib.urlencode({ 'dir_edit' : download_dir})
        request = urllib2.Request(url + '?' + options,data=urllib.urlencode( {'url' : torrent.download_path}))
        response = urllib2.urlopen(request)
        log.info("Response url: " + str(response.geturl()))
        log.info("Response code: " + str(response.getcode()))
        return True
    except urllib2.URLError as e:
        log.exception("Download of : " + torrent.name + " failed")
        return False



@view_config(route_name='downloadMovie', renderer='json')
def downloadMovie(request):
    try:
        try:
            (quality,) = DBSession.query(Setting.value).filter(Setting.name == 'default_quality').one()
        except NoResultFound:
            log.error('default_quality is missing from the database')
            raise Exception('Invalid Database')
        if 'quality' in request.params:
            quality = request.params['quality']
        movie_id = request.matchdict['id']
        movie = None
        try:
            movie = DBSession.query(Movie).filter(and_(Movie.id == movie_id,Movie.downloaded == False)).one()
        except NoResultFound:
            return Response('Movie already Downloaded', content_type='text/plain', status_int=400)

        try:
            torrent = DBSession.query(Torrent).filter(and_(Torrent.movie_id == movie_id, Torrent.quality == quality)).one()
            movie_download_loc = '/home/torrentz/active/MOVIE'
            if (queueTorrentDownload(torrent,movie_download_loc)):
                movie.downloaded = True
                return Response('Success', content_type='text/plain', status_int=200)
        except NoResultFound:
            log.error("Unable to find suitable torrent")

    except DBAPIError:
        log.exception(":(")

@view_config(route_name='latestMovies', renderer='templates/movies.pt')
def latestMovies(request):
    try:
        baseURL = 'http://image.tmdb.org/t/p/'
        posterSize = 'w185'
        return { 'baseURL' : baseURL, 'posterSize' : posterSize , 'noPoster' : request.static_url('nassau:static/no-poster-w185.jpg'), 'movies' :
                DBSession.query(Movie).order_by(desc(Movie.id)).all() }
    except DBAPIError:
        log.exception("Exception when displaying movies")
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

@view_config(route_name='items', request_method='PUT', renderer='json')
def createItem(request):
    try:
        name = u'Not Set'
        type = 0
        status = 0
        extracted_loc = u'Not Set'
        if not 'torrent_name' in request.params:
            return Response('Torrent_name not set', content_type='text/plain', status_int=400)
        torrent_name = request.params['torrent_name']
        if 'name' in request.params:
            name = request.params['name']
        if 'type' in request.params:
            type = int(request.params['type'])
        if 'status' in request.params:
            status = int(request.params['status'])
        if 'extracted_loc' in request.params:
            extracted_loc = request.params['extracted_loc']
        newItem = Item(torrent_name,name,type,status,extracted_loc)
        DBSession.add(newItem)
        DBSession.flush()
        DBSession.refresh(newItem)
        return { 'id' : newItem.id }
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

@view_config(route_name='items', renderer='json')
def getItems(request):
    try:
        query = DBSession.query(Item).all()
        objects = []
        for x in query:
                objects.append(x.toJSON())
        return objects
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_nassau_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

