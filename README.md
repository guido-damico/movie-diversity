# MovieDiversity
MovieDiversity is a python 3 app aimed at quantifying the diversity of movie titles
in theaters across several different cities.

It relies on a URL where to scrub all the titles of the movies currently showing,
and it will store the results in a SQLite database for further analysis.

## How to run it
Download/fork this code and then, from the directory where you saved it, run
```
python3 scraper.py --dbfile movieDiversity.db --location Milano
```
and you should get a list of all shows in Milano saved in the sqlite dile movieDiversity.db.

This is a typical run output:
```
$ python3 scraper.py -db ./movieDiversity.db -loc Milano
2017-05-23 10:39:15 - INFO - Logger initialized at level INFO.
2017-05-23 10:39:15 - INFO - Source connected to db in './movieDiversity.db'
2017-05-23 10:39:15 - INFO - Verifying db schema tables...
2017-05-23 10:39:15 - INFO - Verification terminated and passed.
2017-05-23 10:39:15 - INFO - Scraper instance inited.
2017-05-23 10:39:15 - INFO - Locations definitions found for: ['San Francisco', 'Milano']
2017-05-23 10:39:15 - INFO - Looking for: Milano...
2017-05-23 10:39:15 - INFO - Looking for movie titles in Milano.
2017-05-23 10:39:15 - INFO - Querying http://www.film.it/cercacinema/luogo/milano/ ...
2017-05-23 10:39:16 - INFO - Identified 50 titles.
2017-05-23 10:39:16 - INFO - Querying http://www.mymovies.it/cinema/milano/ ...
2017-05-23 10:39:16 - INFO - Identified 55 titles.
2017-05-23 10:39:16 - INFO - Inserted 75 new shows for today in Milano.
2017-05-23 10:39:16 - INFO - End run.
```

### Command line options
The main routine in `scraper.py` accepts the following options:
```
--dbfile | -db    : the name of the sqlite db file.
--location | -loc : the name of the city whose data is to be updated in the db.
--logLevel | -log : the amount of information sent back to the console.
```

## Initialization of a valid db file
To create a valid db file, run the `movieDiversity.sql` script against a clean/new db.
This will generate a db with all the needed metadata and the seeded information for
Milano (Milan, Italy) and San Francisco.

# Dependencies
The following python 3 packages must be installed and usable to have the application running:
- sqlite3
- lxml
- logging
- requests
- argparse
- pprint
- datetime
- contextlib
- sqlalchemy

For the translations data I rely on the excellent service provided by The Movie Database (TMDb)
at https://www.themoviedb.org/en.

## Disclaimer
This product uses the TMDb API but is not endorsed or certified by TMDb.

# Tests
There are few tests already in the `./tests` directory that you can run.
A sample of run should yield:
```
$ python3 -m unittest discover -v -b
testDbClasses (tests.testMovieDbClasses.testMovieDbClasses)
Verifies that the package defines the expected classes (one per table). ... ok
testDbClassesColumns (tests.testMovieDbClasses.testMovieDbClasses)
Verifies that the definitions of the db classes conform to the expectations. ... ok
testInsertSites (tests.testMovieDbClasses.testMovieDbClasses)
Verifies the 1-to-many relationship between Locations and sites works. ... ok
testInsertTitlesInLocations (tests.testMovieDbClasses.testMovieDbClasses)
Verifies the 1-to-many relationship between Locations and sites works. ... ok
testReadAFile (tests.testPropertiesFileReader.testPropertiesReader)
Tests reading a temporary .properties file. ... ok
testGetMovieTitles (tests.testScraper.testScraper) ... ok
testInsertShow (tests.testSources.testSource)
Tests inserting a show with a test title in a location. ... ok
testInsertTitleInLocation (tests.testSources.testSource)
Tests inserting a test title in a location. ... ok
testLocationsSitesData (tests.testSources.testSource)
Tests the locations and sites data. ... ok
testPlacesNames (tests.testSources.testSource)
Tests the places names data. ... ok
testPlacesType (tests.testSources.testSource)
Tests the places metadata. ... ok
testSchema (tests.testSources.testSource)
Verifies that the definitions of the db schema conforms to the expectations. ... ok
testTitlesData (tests.testSources.testSource)
Tests the getAllTitles. ... ok
testGetTitleFromId (tests.testTimdbRestClient.testTimdb)
Tests getting a movie from a known given ID. ... ok
testSearchByTitle (tests.testTimdbRestClient.testTimdb)
Tests searching a movie by a generic title in different ways. ... ok

----------------------------------------------------------------------
Ran 15 tests in 11.450s

OK
```
