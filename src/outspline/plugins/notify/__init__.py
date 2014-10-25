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

import time

try:
    from gi.repository import Notify
except ImportError:
    Notify = None

try:
    import wx
except ImportError:
    wx = None

from outspline.static.pyaux.timeaux import TimeSpanFormatters

import outspline.core_api as core_api
import outspline.coreaux_api as coreaux_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
wxgui_api = coreaux_api.import_optional_interface_api('wxgui')
wxtrayicon_api = coreaux_api.import_optional_plugin_api('wxtrayicon')


class Notifications():
    def __init__(self, trayicon_id):
        Notify.init("Outspline")

        # It should be safe if the icon is not found in the system
        self.ICON = "outspline-alarm"
        self.trayicon_id = trayicon_id

        organism_alarms_api.bind_to_alarm(self._handle_alarm)

    def _handle_alarm(self, kwargs):
        now = int(time.time()) // 60 * 60

        # Don't notify for old alarms to avoid filling the screen with
        # notifications
        # Of course this check will prevent a valid notification if Outspline
        # takes more than 1 minute from the activation of the alarm to get
        # here, but in case of such serious slowness, a missed notification is
        # probably just a minor problem
        if kwargs['alarm'] == now:
            filename = kwargs['filename']
            id_ = kwargs['id_']
            start = kwargs['start']
            end = kwargs['end']

            text = core_api.get_item_text(filename, id_).partition('\n')[0]

            rstart = start - now

            if rstart > 0:
                body = "In {}".format(TimeSpanFormatters.format_compact(
                                                                    rstart))
            elif rstart == 0:
                body = "Now"
            else:
                body = "{} ago".format(TimeSpanFormatters.format_compact(
                                                                    rstart))

            if end:
                body += ", for {}".format(TimeSpanFormatters.format_compact(
                                                                end - start))

            self.alarm = Notify.Notification.new(summary=text, body=body,
                                                                icon=self.ICON)

            if wxgui_api:
                self.alarm.add_action("open_item", "Open", self._open_item,
                                                               [filename, id_])
            self.alarm.show()

    def _open_item(self, alarm, action, user_data):
        # In order for actions to work, a notification must be a proper object
        # (i.e., they do *not* work if these are plain functions of this
        # module, without this Notifications class)
        wxgui_api.show_main_window()
        wxgui_api.open_editor(user_data[0], user_data[1])

        if self.trayicon_id:
            wxtrayicon_api.stop_blinking(self.trayicon_id)


class BlinkingTrayIcon():
    ref_id = None
    icon = None
    DELAY = None
    SDELAY = None
    delay = None
    sdelay = None
    active_alarms = None

    def __init__(self):
        self.ref_id = wx.NewId()
        wxgui_api.install_bundled_icon("notify", '@trayalarm',
                                                            ("alarm24.png", ))
        self.icon = wxgui_api.get_tray_icon("@trayalarm")
        self.DELAY = 50
        # Set SDELAY shorter than DELAY, so that if an alarm is activated at
        # the same time an alarm is dismissed, there's a better chance that
        # the icon starts blinking
        self.SDELAY = 30

        # Initialize self.delay and self.sdelay with a dummy function (int)
        self.delay = wx.CallLater(1, int)
        self.sdelay = wx.CallLater(1, int)

        self.active_alarms = {}

        self._update_tooltip()

        organism_alarms_api.bind_to_alarm(self._blink_after)
        organism_alarms_api.bind_to_alarm_off(self._stop_after)
        wxgui_api.bind_to_close_database(self._stop_after)
        core_api.bind_to_exit_app_2(self._exit)

    def _blink_after(self, kwargs):
        # Instead of self.blink, bind _this_ function to events that can be
        # signalled many times in a loop, so that self.blink is executed only
        # once after the last signal
        filename = kwargs['filename']
        alarmid = kwargs['alarmid']

        # Keep track of the active alarms because the alarm event is signalled
        # every time occurrences are searched and old alarms are found, so not
        # doing this check would blink the tray icon every time occurrences
        # are searched if there are already-open alarms
        # Do this check here and not in self._blink, otherwise only the last
        # handled alarm would be checked
        if filename not in self.active_alarms:
            self.active_alarms[filename] = [alarmid, ]
        elif alarmid not in self.active_alarms[filename]:
            self.active_alarms[filename].append(alarmid)
        else:
            return False

        # self._blink_later uses wx.CallLater, which cannot be called from
        # other threads than the main one
        wx.CallAfter(self._blink_later)

    def _blink_later(self):
        self.delay.Stop()
        self.delay = wx.CallLater(self.DELAY, self._blink)

    def _blink(self):
        wxtrayicon_api.start_blinking(self.ref_id, self.icon)
        self._update_tooltip()

    def _stop_after(self, kwargs):
        # Instead of self.stop, bind _this_ function to events that can be
        # signalled many times in a loop, so that self.stop is executed only
        # once after the last signal
        filename = kwargs['filename']

        # Do this check here and not in self._stop, otherwise only the last
        # handled alarm would be checked
        # Try-except should be more performing in this case
        try:
            self.active_alarms[filename]
        except KeyError:
            pass
        else:
            try:
                alarmid = kwargs['alarmid']
            except KeyError:
                # alarmid is not present when handling the database close event
                del self.active_alarms[filename]
            else:
                self.active_alarms[filename].remove(alarmid)

                if len(self.active_alarms[filename]) == 0:
                    del self.active_alarms[filename]

        # self._blink_later uses wx.CallLater, which cannot be called from
        # other threads than the main one
        wx.CallAfter(self._stop_later)

    def _stop_later(self):
        # Always stop blinking when handling an alarm off event, even in the
        # remote case that no alarm was found in self.active_alarms above
        self.sdelay.Stop()
        self.sdelay = wx.CallLater(self.SDELAY, self._stop)

    def _stop(self):
        nalarms = self._update_tooltip()

        if nalarms == 0:
            wxtrayicon_api.stop_blinking(self.ref_id)

    def _update_tooltip(self):
        # Don't rely on counts from wxtasklist or wxalarms, as they aren't
        # accurate because of race conditions
        nalarms = organism_alarms_api.get_number_of_active_alarms()

        tooltip = 'Active alarms: {}'.format(str(nalarms))
        wxtrayicon_api.set_tooltip_value(self.ref_id, tooltip)
        return nalarms

    def _exit(self, kwargs):
        # Unbind the handlers whose timers could race with the application
        # closure
        organism_alarms_api.bind_to_alarm_off(self._stop_after, False)
        wxgui_api.bind_to_close_database(self._stop_after, False)
        self.delay.Stop()
        self.sdelay.Stop()


def main():
    if wxtrayicon_api:
        trayicon = BlinkingTrayIcon()
        trayicon_id = trayicon.ref_id
    else:
        trayicon_id = False

    if Notify:
        Notifications(trayicon_id)
