# Organism - A simple and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import os
import errno
import logging

# This module is used indirectly, make sure it's imported
import loggingext

from configuration import info, config, _USER_FOLDER_PERMISSIONS

log = None


def set_logger(cliargs):
    if cliargs.loglevel != None:
        loglevel = cliargs.loglevel
    else:
        loglevel = config('Log')['log_level']
    
    if cliargs.logfile != None:
        logfile = os.path.expanduser(cliargs.logfile)
    else:
        logfile = os.path.expanduser(config('Log')['log_file'])
    
    try:
        os.makedirs(os.path.dirname(logfile), mode=_USER_FOLDER_PERMISSIONS)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    
    level = {'console': int(loglevel[0]), 'file': int(loglevel[1:])}
    
    if level['console'] not in (0, 1, 2, 3):
        level['console'] = 2
    if level['file'] not in (0, 1, 2, 3):
        level['file'] = 0
    
    logconfig = {
        'version': 1,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(relativeCreated)d | %(levelname)s: '
                                                                 '%(message)s',
                'datefmt': '%Y-%m-%d %H:%M'
            },
            'simple_info': {
                'format': ':: %(message)s'
            },
            'simple_default': {
                'format': '%(levelname)s: %(message)s'
            },
            'verbose': {
                'format': '%(asctime)s %(relativeCreated)d | %(levelname)s: '
                                       '%(message)s [%(pathname)s %(lineno)d]',
                'datefmt': '%Y-%m-%d %H:%M'
            },
            'verbose_info': {
                'format': '%(relativeCreated)d | :: %(message)s [%(module)s '
                                                                  '%(lineno)d]'
            },
            'verbose_default': {
                'format': '%(relativeCreated)d | %(levelname)s: %(message)s '
                                                      '[%(module)s %(lineno)d]'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': ('CRITICAL', 'ERROR', 'INFO', 'DEBUG'
                          )[level['console']],
                'formatter': ('simple_default', 'simple_default',
                              'simple_default', 'verbose_default'
                              )[level['console']],
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': ('CRITICAL', 'WARNING', 'INFO', 'DEBUG'
                          )[level['file']],
                'formatter': ('simple', 'simple', 'simple', 'verbose'
                              )[level['file']],
                'filename': logfile,
                'maxBytes': (1, 10000, 30000, 100000)[level['file']],
                'backupCount': 1,
                'delay': (True, True, False, False)[level['file']]
            },
            'null': {
                'class': 'logging.NullHandler',
                'formatter': 'simple',
            }
        },
        'loggers': {
            'organism1': {
                'level': 'DEBUG',
                'handlers': [('null', 'console', 'console', 'console'
                              )[level['console']],
                             ('null', 'file', 'file', 'file'
                              )[level['file']]],
                'propagate': False
            }
        },
        'root': {
            'level': 'DEBUG'
        }
    }
    
    formconfig = {
        'console': {
            'info': ('simple_info', 'simple_info',
                     'simple_info', 'verbose_info'
                     )[level['console']],
        },
        'file': {
            'warning': ('simple', 'verbose', 'verbose', 'verbose'
                        )[level['file']],
            'error': ('simple', 'verbose', 'verbose', 'verbose'
                      )[level['file']],
            'critical': ('simple', 'verbose', 'verbose', 'verbose'
                         )[level['file']],
        },
    }
    
    logging.setLoggerClass(loggingext.Logger)
    loggingext.dictConfig(logconfig, formconfig)
    
    global log
    log = logging.getLogger('organism1')
    
    log.info('Start logging (level {}, file {})'.format(loglevel, logfile))
    log.info('{} version {} ({})'.format('Organism', info['component_version'],
                                         info['component_release_date']))
