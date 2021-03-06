from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('items', '/item')
    config.add_route('updateItem', '/item/{id}')
    config.add_route('torrents', '/torrents')
    config.add_route('getTorrents', '/torrent')
    config.add_route('latestMovies', '/movies')
    config.add_route('downloadMovie', '/movie/{id}/download')
    config.add_route('update', '/update')
    config.add_route('updateTv', '/tv/update')
    config.scan()
    return config.make_wsgi_app()
