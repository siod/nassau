from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


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
