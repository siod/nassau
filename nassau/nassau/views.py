from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Item,
    )
import json
import feedparser
import re
import tmdbsimple
import copy


#@view_config(route_name='home', renderer='templates/mytemplate.pt')
#def my_view(request):
    #try:
        #one = DBSession.query(Item).filter(Item.name == 'one').first()
    #except DBAPIError:
        #return Response(conn_err_msg, content_type='text/plain', status_int=500)
    #return {'one': one, 'project': 'nassau'}

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

tmdb = tmdbsimple.TMDB('')
def getMovieInfo(title,year):
    search = tmdb.Search()
    response = search.movie( { 'query' : title , 'year' : year})
    if (search):
        if (len(search.results) == 1):
            return search.results[0]
        for x in search.results:
            if (x['title'] == title):
                return x

    print("Unable to find " + title + " " + year + " on tmdb")
    print(repr(search.results))
    return {'title' : title, 'release_date' : year, 'poster_path' : '' }

def addIfHighestQuality(newMovie,dest_list):
    dest_copy = copy.deepcopy(dest_list)
    for y in dest_copy:
        if y['title'] == newMovie['title']:
            if (newMovie['quality'] == '1080p' and y['quality'] != '1080p'):
                dest_list.remove(y)
                dest_list.append(newMovie)
                return
            return
    dest_list.append(newMovie)

movieRegex = re.compile(r'([A-Za-z\d\._-]+\.)((19|20)\d\d)\.([0-9]{3,4}p)\.')
@view_config(route_name='latestMovies', renderer='templates/movies.pt')
def latestMovies(request):
    try:
        moviesFeed = ''
        movieInfo = feedparser.parse(moviesFeed)
        initialMovies = []
        for x in movieInfo.entries:
            if (DBSession.exists().where(Torrent.name == x.title)):
                continue
            titleSearch = movieRegex.search(x.title)
            movieTitle = titleSearch.group(1)
            movieTitle = movieTitle.replace('.',' ')[:-1]
            movieYear = titleSearch.group(2)
            movieQuality = titleSearch.group(4)
            initialMovies.append({
                'release_date' : movieYear,
                'title' : movieTitle,
                'quality' : movieQuality,
                'torrent_name' : x.title,
                'download_path' : x.link
                })
        raw_movies = []
        for x in initialMovies:
            addIfHighestQuality(x,raw_movies)

        movies = []
        for x in raw_movies:
            #if (DBSession.query(Movie).filter(Movie.title == x['title'])
            print( x['title'] + ' ' + x['release_date'] + ' ' + x['quality'])
            movies.append(getMovieInfo(x['title'],x['release_date']))
        baseURL = 'http://image.tmdb.org/t/p/'
        posterSize = 'w185'
        return { 'baseURL' : baseURL, 'posterSize' : posterSize ,'movies' : movies }
    except DBAPIError:
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

