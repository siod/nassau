import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Item,
    Base,
    Setting,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        model = Item(torrent_name = 'Doctor.who',name= 'Doctor Who',type=1,status=3,extracted_loc='torrentz')
        DBSession.add(model)
        model = Item(torrent_name = 'Futurama.Benders.Big.Game',name= 'Futurama Benders Big Game',type=2,status=3,extracted_loc='torrentz')
        DBSession.add(model)
        setting = Setting(name = 'tmdb_api_key',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'rss_url',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'auth_realm',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'auth_uri',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'auth_user',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'auth_passwd',value = '')
        DBSession.add(setting)
        setting = Setting(name = 'default_quality',value = '1080p')
        DBSession.add(setting)
        setting = Setting(name = 'torrent_url',value = '')
        DBSession.add(setting)

