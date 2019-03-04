'''
Created on Oct 13, 2018

SQLAlchemy classes for the MovieDiversity db.

@author: Guido
'''
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import inspect
from sqlalchemy.sql.schema import CheckConstraint

Base = declarative_base()

class movieDbBaseClass():
    """
    Base class that captures common behaviors in this package. 
    """

    def describe(self, classInstance = None):
        """
        Common representation of the given class.
        """
        mapper = inspect(classInstance)

        return mapper

    def getColumnNames(self):
        """
        Returns a list of the columns defined for this class.
        """
        return [x for x in self.__dict__.keys() if x[0] != "_"]

class Locations(Base, movieDbBaseClass):
    """
    Table for all locations.
    """
    __tablename__ = 'locations'
    id = Column(Integer, primary_key = True)
    name = Column(String(250))
    language = Column(String(250))

class Sites(Base, movieDbBaseClass):
    """
    Table for all sites.
    """
    __tablename__ = 'sites'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    url = Column(String(250), nullable = False)
    title_xpath = Column(String(250))
    active = Column(Integer())
    locations_ref = Column(Integer, ForeignKey("locations.id"))
    CheckConstraint("active  in (0, 1)", name = "site_active_constraint")

class Titles(Base, movieDbBaseClass):
    """
    Table for all titles.
    """
    __tablename__ = 'titles'
    id = Column(Integer, primary_key = True)
    title = Column(String(250))

class TitlesInLocations(Base, movieDbBaseClass):
    """
    Many to many relation linking titles and locations.
    """
    __tablename__ = 'titles_in_locations'
    id = Column(Integer, primary_key = True)
    titles_ref = Column(Integer, ForeignKey('titles.id'))
    titles = relationship(Titles)
    locations_ref = Column(Integer, ForeignKey('locations.id'))
    locations = relationship(Locations)

class Shows(Base, movieDbBaseClass):
    """
    Table for all shows.
    """
    __tablename__ = 'shows'
    id = Column(Integer, primary_key = True)
    date = Column(String(250))
    titles_in_locations_ref = Column(Integer, ForeignKey('titles_in_locations.id'))
    locations = relationship(TitlesInLocations)

class Translations(Base, movieDbBaseClass):
    """
    Table for all translations.
    """
    __tablename__ = 'translations'
    id = Column(Integer, primary_key = True)
    lang_from = Column(String(250))
    lang_to = Column(String(250))
    title_from_ref = Column(Integer, ForeignKey('titles.id'))
    titleFrom = relationship(Titles, foreign_keys = [title_from_ref])
    title_to_ref = Column(Integer, ForeignKey('titles.id'))
    titleTo = relationship(Titles, foreign_keys = [title_to_ref])

