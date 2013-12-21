# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
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

import time

try:
    from gi.repository import Notify
except ImportError:
    Notify = None

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
wxgui_api = coreaux_api.import_optional_interface_api('wxgui')


class Notifications():
    alarm = None

    def __init__(self):
        Notify.init("Outspline")

    def handle_alarm(self, kwargs):
        if kwargs['alarm'] == int(time.time()) // 60 * 60:
            filename = kwargs['filename']
            id_ = kwargs['id_']

            text = core_api.get_item_text(filename, id_).partition('\n')[0]

            self.alarm = Notify.Notification.new(summary="Outspline",
                                             body=text, icon="appointment-new")

            if wxgui_api:
                self.alarm.add_action("open_item", "Open", self.open_item,
                                                               [filename, id_])
            self.alarm.show()

    def open_item(self, alarm, action, user_data):
        # In order for actions to work, a notification must be a proper object
        # (i.e., they do *not* work if these are plain functions of this
        # module, without this Notifications class)
        wxgui_api.show_main_window()
        wxgui_api.open_editor(user_data[0], user_data[1])


def main():
    if Notify:
        organism_alarms_api.bind_to_alarm(Notifications().handle_alarm)
