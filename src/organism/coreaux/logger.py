# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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
import logging.config

from configuration import info, config, _USER_FOLDER_PERMISSIONS

log = None


class LevelFilter():
    levels = None
    inverse = None

    def __init__(self, levels, inverse):
        self.levels = levels
        self.inverse = inverse

    def filter(self, record):
        return (record.levelname in self.levels) ^ self.inverse


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

    console_level = ('CRITICAL', 'ERROR', 'INFO', 'DEBUG')[level['console']]
    file_level = ('CRITICAL', 'WARNING', 'INFO', 'DEBUG')[level['file']]
    console_formatter = ('simple_default', 'simple_default', 'simple_default',
                         'verbose_default')[level['console']]
    console_info_formatter = ('simple_info', 'simple_info', 'simple_info',
                              'verbose_info')[level['console']]
    file_low_formatter = ('simple', 'simple', 'simple', 'verbose')[level['file']
                                                                               ]
    file_formatter = ('simple', 'verbose', 'verbose', 'verbose')[level['file']]
    file_max_bytes = (1, 10000, 30000, 100000)[level['file']]
    file_delay = (True, True, False, False)[level['file']]
    handlers = [('null', 'console', 'console', 'console')[level['console']],
                ('null', 'console_info', 'console_info', 'console_info')
                 [level['console']],
                ('null', 'file_low', 'file_low', 'file_low')[level['file']],
                ('null', 'file', 'file', 'file')[level['file']]]

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
        'filters': {
            'console': {
                '()': 'organism.coreaux.logger.LevelFilter',
                'levels': ('INFO', ),
                'inverse': True,
            },
            'console_info': {
                '()': 'organism.coreaux.logger.LevelFilter',
                'levels': ('INFO', ),
                'inverse': False,
            },
            'file_low': {
                '()': 'organism.coreaux.logger.LevelFilter',
                'levels': ('INFO', 'DEBUG'),
                'inverse': False,
            },
            'file': {
                '()': 'organism.coreaux.logger.LevelFilter',
                'levels': ('INFO', 'DEBUG'),
                'inverse': True,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': console_level,
                'formatter': console_formatter,
                'filters': ['console', ]
            },
            'console_info': {
                'class': 'logging.StreamHandler',
                'level': console_level,
                'formatter': console_info_formatter,
                'filters': ['console_info', ]
            },
            'file_low': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': file_level,
                'formatter': file_low_formatter,
                'filename': logfile,
                'maxBytes': file_max_bytes,
                'backupCount': 1,
                'delay': file_delay,
                'filters': ['file_low', ]
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': file_level,
                'formatter': file_formatter,
                'filename': logfile,
                'maxBytes': file_max_bytes,
                'backupCount': 1,
                'delay': file_delay,
                'filters': ['file', ]
            },
            'null': {
                'class': 'logging.NullHandler',
                'formatter': 'simple',
            }
        },
        'loggers': {
            'organism': {
                'level': 'DEBUG',
                'handlers': handlers,
                'propagate': False
            }
        },
        'root': {
            'level': 'DEBUG'
        }
    }

    logging.config.dictConfig(logconfig)

    global log
    log = logging.getLogger('organism')

    log.info('Start logging (level {}, file {})'.format(loglevel, logfile))
    log.info('{} version {} ({})'.format('Organism', info['component_version'],
                                         info['component_release_date']))
