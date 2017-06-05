PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
--
-- DDL
--
CREATE TABLE locations (id integer primary key,
                        name text,
                        language text);

CREATE TABLE sites (id integer PRIMARY KEY,
                    name text NOT NULL,
                    url text NOT NULL,
                    title_xpath text,
                    active integer,
                    locations_ref integer,
                    FOREIGN KEY (locations_ref) references locations(id),
                    CHECK (active in (0, 1)));

CREATE TABLE titles (id integer PRIMARY KEY,
                     title text NOT NULL);

CREATE TABLE titles_in_locations (id integer PRIMARY KEY,
                                  titles_ref integer NOT NULL,
                                  locations_ref integer NOT NULL,
                                  FOREIGN KEY (titles_ref) references titles(id),
                                  FOREIGN KEY (locations_ref) references locations(id));

CREATE TABLE shows (id integer PRIMARY KEY,
                    date text,
                    titles_in_locations_ref integer NOT NULL,
                    FOREIGN KEY(titles_in_locations_ref) references titles_in_locations(id));

CREATE TABLE translations (id integer PRIMARY KEY,
                           lang_from text,
                           lang_to text,
                           title_from_ref integer,
                           title_to_ref integer,
                           FOREIGN KEY(title_from_ref) references titles(id),
                           FOREIGN KEY(title_to_ref) references titles(id));

--
-- Seed data
--
INSERT INTO locations VALUES (1, 'San Francisco', 'en');
INSERT INTO locations VALUES (2, 'Milano',        'it');
INSERT INTO locations VALUES (3, 'New York',      'en');
INSERT INTO locations VALUES (4, 'Cairo',         'en');
INSERT INTO locations VALUES (5, 'München',       'de');

INSERT INTO sites VALUES (1,
                          'sfgate.com',
                          'http://www.sfgate.com/cgi-bin/movies/listings/theatershowtimes?county=San%20Francisco',
                          '//div[@class="movie_listing_list"]/div[@class="list"]/div[@class="item"]/div/div[@class="theater"]/a/text()',
                          1,
                          1);
INSERT INTO sites VALUES (2,
                          'film.it',
                          'http://www.film.it/cercacinema/luogo/milano/',
                          '//div[@class="contenutoscheda_citta"]/p/a/text()',
                          1,
                          2);
INSERT INTO sites VALUES (3,
                          'mymovies.it',
                          'http://www.mymovies.it/cinema/milano/',
                          '//div[@id="elenco_film"]/div[@class="link"]/div/a/text()',
                          1,
                          2);
INSERT INTO sites VALUES (4,
						  'Imdb',
						  'http://www.imdb.com/showtimes/location/US/10001?ref_=sh_lc&sort=alpha,asc&mode=showtimes_grid&page=1',
						  '//div[@class="title"]/a/text()',
						  1,
						  3);
INSERT INTO sites VALUES (5,
						  'cairoscene',
						  'http://www.cairoscene.com/Movies',
						  '//div[@class="content-4"]/div/div/div/div[@class="movie-title"]/h2/a/text()',
						  1,
						  4);
INSERT INTO sites VALUES (6,
						  'muenchen.de',
						  'https://kino.muenchen.de/kinos-muenchen.html',
						  '//div[@class="item__content row collapse"]/div/div[@class="upcoming night"]/a/span/text()',
						  1,
						  5);

COMMIT;