'''
Created on Jun 5, 2017

@author: Guido
'''
import argparse
import sources
import movieLogger

def formatReport():
    """Outputs the requested report.
    """

###
#
# main entry point
#
###
if __name__ == "__main__":
    # Parse arguments from command line
    parser = argparse.ArgumentParser(description = 'The Analytics module includes reporting functions for the MovieDiversity app.')
    parser.add_argument('--dbfile', '-db',
                        required = True,
                        help = 'The sqlite db file to be used.')
    parser.add_argument('--logLevel', '-log',
                        required = False,
                        choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help = 'The level of output for logging. Defaults to INFO.')
    parser.add_argument('--location', '-loc',
                        required = True,
                        help = 'The location for which to collect data.')
    parser.add_argument('--report', '-r',
                        required = True,
                        choices = ['allTitlesInLoc'],
                        help = 'The report that needs to be created in output.')

    args = parser.parse_args()

    # Init the logging system
    movieLogger.MovieLoggger().initLogger(level = args.logLevel)

    S = sources.Sources(dbfile = args.dbfile)

    S.logger.info("Analytics module")

    allLocations = S.getAllLocations()
    S.logger.info("Locations definitions found for: %s", allLocations)

    S.logger.info("Looking for: %s...", args.location)

    S.logger.fatal("Analytics not yet implemented!")

    allData = S.getAllTitlesInLocation()
    S.logger.info("End run.")
