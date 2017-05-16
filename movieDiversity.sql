PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
--
-- DDL
--
CREATE TABLE locations(id integer primary key,
                       name text,
                       language text);
CREATE TABLE sites(id integer primary key,
                   name text,
                   url text,
                   title_xpath text,
                   active integer,
                   locations_ref integer,
                   FOREIGN KEY (locations_ref) references locations(id),
                   CHECK (active in (0, 1)));
CREATE TABLE titles(id integer primary key,
                    name text,
                    locations_ref integer,
                    FOREIGN KEY (locations_ref) references locations(id));
CREATE TABLE shows(id integer primary key,
                   date text,
                   titles_ref integer,
                   FOREIGN KEY(titles_ref) references titles(id));
CREATE TABLE translations(id integer primary key,
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
INSERT INTO locations VALUES (2, 'Milano', 'it');

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
COMMIT;
