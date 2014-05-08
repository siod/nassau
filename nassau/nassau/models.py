from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    String,
    Boolean,
    Date,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Setting(Base):
    __tablename__ = 'settings'
    name = Column(String(50),primary_key = True)
    value = Column(String(50))

    def __init__(self,name,value):
        self.name = name
        self.value = value

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer,index=True,unique=True)
    title = Column(String(50))
    release_date = Column(Date)
    poster_path = Column(String(50))
    downloaded = Column(Boolean)

    def __init__(self,title,tmdb_id,release_date,poster_path,downloaded):
        self.title = title
        self.tmdb_id = tmdb_id
        self.release_date = release_date
        self.poster_path = poster_path
        self.downloaded = downloaded

class Torrent(Base):
    __tablename__ = 'torrents'
    id = Column(Integer, primary_key=True)
    name = Column(String(100),index=True,unique=True)
    decoded_name = Column(String(100),index=True)
    movie_id = Column(Integer)
    download_path = Column(String(255))
    quality = Column(String(20))

    def __init__(self,torrent_name,decoded_name,movie_id, download_path,quality):
        self.name = torrent_name
        self.decoded_name = decoded_name
        self.movie_id = movie_id
        self.download_path = download_path
        self.quality = quality

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    torrent_name = Column(Text)
    name = Column(Text)
    type = Column(Integer)
    status = Column(Integer)
    extracted_loc = Column(Integer)

    def __init__(self, torrent_name, name, type, status, extracted_loc):
        self.torrent_name = torrent_name
        self.name = name
        self.type = type
        self.status = status
        self.extracted_loc = extracted_loc

    def statusToString(self):
        return [
                "Unknown",
                "Processing",
                "Failed",
                "Extracted"
                ][self.status]

    def typeToString(self):
        return [
                "INVALID",
                "TV Show",
                "Movie"
                ][self.type]

    def toJSON(self):
        return {
                'id' : self.id,
                'torrent_name' : self.torrent_name,
                'type' : self.type,
                'typeS' : self.typeToString(),
                'name' : self.name,
                'status' : self.status,
                'statusS' : self.statusToString(),
                'extracted_loc' : self.extracted_loc
            }

Index('my_index', Item.torrent_name, unique=True, mysql_length=255)
