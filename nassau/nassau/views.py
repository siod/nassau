from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Item,
    )
import json


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

@view_config(route_name='items', request_method='PATCH', renderer='json')
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

