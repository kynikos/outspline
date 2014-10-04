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

import wxcopypaste


def bind_to_cut_items(handler, bind=True):
    return wxcopypaste.cut_items_event.bind(handler, bind)


def bind_to_items_pasted(handler, bind=True):
    return wxcopypaste.items_pasted_event.bind(handler, bind)


def simulate_cut_items(no_confirm=False):
    return wxcopypaste.plugin.mainmenu.cut_items(None, no_confirm=no_confirm)


def simulate_copy_items():
    return wxcopypaste.plugin.mainmenu.copy_items(None)


def simulate_paste_items_as_siblings(no_confirm=False):
    return wxcopypaste.plugin.mainmenu.paste_items_as_siblings(None,
                                                        no_confirm=no_confirm)


def simulate_paste_items_as_children(no_confirm=False):
    return wxcopypaste.plugin.mainmenu.paste_items_as_children(None,
                                                        no_confirm=no_confirm)
