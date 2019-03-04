'''
Created on May 15, 2017

@author: Guido
Logging system for the MovieDiversity app.
'''
import logging
import sys

class MovieLoggger(object):
    """
    Wrapper to get uniform logging across all the MovieDiversity modules.
    """
    LOGGER_NAME = 'MovieLogger'

    _defaultLevel = 'INFO'
    _levelMap = {'NOTSET'   : logging.NOTSET,
                 'DEBUG'    : logging.DEBUG,
                 'INFO'     : logging.INFO,
                 'WARNING'  : logging.WARNING,
                 'ERROR'    : logging.ERROR,
                 'CRITICAL' : logging.CRITICAL
                }

    def initLogger(self, level = None, loggerName = LOGGER_NAME):
        """
        This initialization functions should be called first to set the properties
        of the logger named loggerName (defaults to MovieLogger.LOGGER_NAME).

        After this has been called, all references obtained with
            logging.getLogger(MovileLogger.LOGGER_NNAME)
        return the same logger, ensuring uniformity.

        level can be set to any valid logging level, the default being logging.INFO.
            It can be specified either as a preset value
            (logging.[DEBUG|INFO|WARNNING|ERROR|CRITICAL])
            or as a number (0,10,20,30,40,50).
        """
        logger = logging.getLogger(loggerName)

        if level is None:
            level = self._defaultLevel
        elif isinstance(level, type("")):
            level = self._levelMap[level]
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(fmt = '%(asctime)s - %(levelname)s - %(module)s#%(funcName)s - %(message)s',
                                      datefmt = '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info("Logger initialized at level %s.", level)

    def resetLoggingLevel(self, newLevel = None):
        """
        Allows the logging level to be changed after initialization.

        newLevel can be set to any valid logging level, the default being logging.INFO.
            It can be specified either as a preset value
            (logging.[DEBUG|INFO|WARNNING|ERROR|CRITICAL])
            or as a number (0,10,20,30,40,50).
        """
        logger = logging.getLogger(self.LOGGER_NAME)

        if newLevel is None:
            newLevel = self._defaultLevel
        elif isinstance(newLevel, type("")):
            newLevel = self._levelMap[newLevel]
        logger.setLevel(newLevel)

        logger.info("Logger level reset to %s.", newLevel)
