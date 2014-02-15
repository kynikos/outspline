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

from links import links, exceptions


def get_supported_open_databases():
    return links.cdbs


def get_existing_links(filename):
    return links.select_links(filename)


def make_link(filename, id_, target, group, description='Make link'):
    try:
        return links.upsert_link(filename, id_, target, group,
                                                       description=description)
    except exceptions.CircularLinksError:
        return False


def delete_link(filename, id_, group, description='Delete link'):
    return links.delete_link(filename, id_, group, description=description)


def find_link_target(filename, id_):
    return links.find_link_target(filename, id_)


def find_back_links(filename, id_):
    return links.find_back_links(filename, id_)


def find_broken_links(filename):
    return links.find_broken_links(filename)


def find_first_broken_link(filename):
    return links.find_first_broken_link(filename)
