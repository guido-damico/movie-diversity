'''
Created on May 15, 2017

@author: Guido
Logging system for the MovieDiversity app.
'''
import logging
import sys

class MovieLoggger(object):
    """Wrapper to get uniform logging across all the MovieDiversity modules.
    """
    LOGGER_NAME = 'MovieLogger'

    _defaultLevel = logging.DEBUG

    def initLogger(self):
        """
        This initialization functions should be called first to set the properties
        of the logger named MovieLogger.LOGGER_NAME.
        
        After this has been called, all references obtained with
            logging.getLogger(MovileLogger.LOGGER_NNAME)
        return the same logger, ensuring uniformity.
        """
        logger = logging.getLogger(self.LOGGER_NAME)
        logger.setLevel(self._defaultLevel)

        handler = logging.StreamHandler(sys.stdout)

        handler.setLevel(self._defaultLevel)
        formatter = logging.Formatter(fmt = '%(asctime)s - %(levelname)s - %(message)s',
                                      datefmt = '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        logger.debug("Logger initialized.")