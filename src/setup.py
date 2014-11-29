# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2014 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Outspline.
#
# Outspline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Outspline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Outspline.  If not, see <http://www.gnu.org/licenses/>.

import os
import errno
from distutils.core import setup

import config

_DATA_EXT_BLACKLIST = ('.py', '.pyc', '.pyo')


def find_package_data(head, rhead):
    data = []

    for tail in os.listdir(head):
        path = os.path.join(head, tail)
        rpath = os.path.join(rhead, tail)

        if os.path.isdir(path):
            if not os.path.exists(os.path.join(path, '__init__.py')):
                data.extend(find_package_data(path, rpath))

        elif os.path.splitext(tail)[1] not in _DATA_EXT_BLACKLIST:
            data.append(rpath)

    return data


def compose_package_metadata(head):
    packages, package_dir, package_data = [], {}, {}

    if os.path.exists(os.path.join(head, '__init__.py')):
        pkg = head.replace('/', '.')
        packages.append(pkg)
        package_dir[pkg] = head
        data = find_package_data(head, '')

        if data:
            package_data[pkg] = data

    for tail in os.listdir(head):
        path = os.path.join(head, tail)

        if os.path.isdir(path):
            result = compose_package_metadata(path)
            packages.extend(result['packages'])
            package_dir.update(result['package_dir'])
            package_data.update(result['package_data'])

    return {'packages': packages,
            'package_dir': package_dir,
            'package_data': package_data}


def compose_addon_data_files(type_):
    head = os.path.join("data_files", type_)

    try:
        tails = os.listdir(head)
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise
        else:
            return []
    else:
        for tail in tails:
            path = os.path.join(head, tail)

            if os.path.isdir(path):
                return compose_data_files(path)


def compose_data_files(head):
    data_files = []

    for dirpath, dirnames, filenames in os.walk(head):
        if filenames:
            instpath = os.path.join("/", dirpath[len(head):])
            files = [os.path.join(dirpath, filename) for filename in filenames]
            data_files.append((instpath, files))

    return data_files


def compose_scripts():
    try:
        scripts = os.listdir("scripts")
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise
        else:
            return {}
    else:
        return {'scripts': [os.path.join("scripts", script)
                                                        for script in scripts]}


def compose_metadata(meta):
    meta.update(compose_package_metadata('outspline'))
    meta.update(compose_scripts())
    meta['data_files'] = compose_data_files(os.path.join("data_files", "core"))

    for type_ in ("extensions", "interfaces", "plugins"):
        meta['data_files'].extend(compose_addon_data_files(type_))

    return meta

setup(**compose_metadata(config.meta))
