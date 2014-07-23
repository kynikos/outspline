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

import time as time_
import wx

from outspline.static.wxclasses.misc import NarrowSpinCtrl

import outspline.core_api as core_api
import outspline.extensions.organism_timer_api as organism_timer_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api


class Dialogs(object):
    def __init__(self):
        self.DELAY = 1
        self.search_dialogs = {}
        self.activate_dialogs = {}

        organism_alarms_api.install_unique_old_alarms_interface(
                                                self._choose_old_alarms_unique)
        wxgui_api.register_aborted_save_warning(
                    organism_timer_api.get_old_occurrences_search_exception(),
                    "The database cannot be saved while the old "
                    "alarms are being searched and activated.")

        # Enabling and closing do not race, i.e. it's impossible that first a
        # dialog is started to be created, but it's tried to be closed *while*
        # it's creating, *before* it's shown; this is because these two events
        # run sequentially on the same thread, and they both trigger actions
        # on the GUI (creating the dialog and closing it) that run on the main
        # thread, so while the dialog is creating, the call for closing it,
        # even if triggered, has to wait for the dialog to be created
        organism_timer_api.bind_to_search_old_alarms(self._enable_search)
        organism_timer_api.bind_to_search_old_alarms_end(self._disable_search)

        organism_alarms_api.bind_to_activate_alarms_range(
                                                        self._enable_activate)
        organism_alarms_api.bind_to_activate_alarms_range_end(
                                                        self._disable_activate)

        core_api.bind_to_closing_database(self._handle_closing_database)

    def _enable_search(self, kwargs):
        filename = kwargs['filename']
        self.search_dialogs[filename] = DialogSearch(filename,
                                                        kwargs['last_search'])

        # This method is called from another thread
        wx.CallAfter(wx.CallLater, self.DELAY, self._open_search, filename)

    def _open_search(self, filename):
        try:
            dialog = self.search_dialogs[filename]
        except KeyError:
            # The dialog could have been disabled meanwhile because the search
            # has finished before even reaching here
            pass
        else:
            dialog.create()

    def _disable_search(self, kwargs):
        filename = kwargs['filename']

        # This method is called from another thread
        wx.CallAfter(self.search_dialogs[filename].close)

        # Delete the dialog immediately in this thread so if the search
        # finishes before the delay has expired, the dialog isn't even created
        del self.search_dialogs[filename]

    def _enable_activate(self, kwargs):
        filename = kwargs['filename']
        self.activate_dialogs[filename] = DialogActivate(filename)

        # This method is called from another thread
        wx.CallAfter(self._open_activate, filename)

    def _open_activate(self, filename):
        try:
            dialog = self.activate_dialogs[filename]
        except KeyError:
            # The dialog could have been disabled meanwhile because the search
            # has finished before even reaching here
            pass
        else:
            dialog.create()

    def _disable_activate(self, kwargs):
        filename = kwargs['filename']

        # This method is called from another thread
        wx.CallAfter(self.activate_dialogs[filename].close)

        # Delete the dialog immediately in this thread so if the search
        # finishes before the delay has expired, the dialog isn't even created
        del self.activate_dialogs[filename]

    def _choose_old_alarms_unique(self, filename, count):
        # This method is called from another thread
        wx.CallAfter(self.activate_dialogs[filename].choose_old_alarms_unique,
                                                                        count)

    def _handle_closing_database(self, kwargs):
        filename = kwargs['filename']

        try:
            dialog = self.activate_dialogs[filename]
        except KeyError:
            pass
        else:
            dialog.close()
            del self.activate_dialogs[filename]
            # DialogSearch is already closed when closing the database by the
            # dedicated event in organism_timer's OldOccurrencesSearch


class DialogSearch(object):
    def __init__(self, filename, last_search):
        self.filename = filename
        self.last_search = last_search
        self.dialog = None
        self.WRAP = 320

    def create(self):
        self.dialog = wx.Dialog(wxgui_api.get_main_frame(),
                                title="Old alarms search",
                                style=wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX)

        self.csizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(self.csizer)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.csizer.Add(vsizer, 1, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer1, flag=wx.EXPAND | wx.BOTTOM, border=4)

        icon = wx.StaticBitmap(self.dialog, bitmap=wx.ArtProvider.GetBitmap(
                                        'appointment-soon', wx.ART_CMN_DIALOG))
        hsizer1.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        self.labeltext = ("{} was last saved {} days ago: searching the "
            "alarms that should have been activated since {{}}...".format(
                        self.filename,
                        int(round((time_.time() - self.last_search) / 86400))))
        self.label1 = wx.StaticText(self.dialog,
                                        label=self.labeltext.format("then"))
        self.label1.Wrap(self.WRAP)
        hsizer1.Add(self.label1)

        self.gauge = wx.Gauge(self.dialog)
        vsizer.Add(self.gauge, flag=wx.EXPAND | wx.BOTTOM, border=4)
        self.timer = wx.CallLater(100, self._pulse)

        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer2, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        restrict = wx.Button(self.dialog, label="Restrict")
        hsizer2.Add(restrict, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        label2 = wx.StaticText(self.dialog, label="the search to the last")
        hsizer2.Add(label2, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.number = NarrowSpinCtrl(self.dialog, min=1, max=99,
                                                        style=wx.SP_ARROW_KEYS)
        self.number.SetValue(1)
        hsizer2.Add(self.number, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        label3 = wx.StaticText(self.dialog, label="days")
        hsizer2.Add(label3, flag=wx.ALIGN_CENTER_VERTICAL)

        self.dialog.Bind(wx.EVT_BUTTON, self._restrict_search, restrict)

        abort = wx.Button(self.dialog, label="Skip searching for old alarms")
        vsizer.Add(abort, flag=wx.ALIGN_CENTER)

        self.dialog.Bind(wx.EVT_BUTTON, self._abort_search, abort)

        self.csizer.Fit(self.dialog)

        self.dialog.Bind(wx.EVT_CLOSE, self._handle_close)

        # Don't show it modal because only one modal dialog can be shown at a
        # time, and managing the races among them would be a bigger mess than
        # making it safe to show them non modal
        self.dialog.Show()

    def _pulse(self):
        self.gauge.Pulse()
        self.timer.Restart()

    def _restrict_search(self, event):
        value = self.number.GetValue()
        mint = int(time_.time()) - value * 86400

        self.label1.SetLabelText(self.labeltext.format("{} days ago".format(
                                                                    value)))
        # Re-wrap the text in case of a long filename, so that it will take a
        # new line if needed; it must be done *before* self.csizer.Fit
        self.label1.Wrap(self.WRAP)

        self.csizer.Fit(self.dialog)

        organism_timer_api.restart_old_occurrences_search(self.filename, mint)

    def _abort_search(self, event):
        organism_timer_api.abort_old_occurrences_search(self.filename)

    def _handle_close(self, event):
        # Resetting the style of the dialog without wx.CLOSE_BOX is not enough
        # because it doesn't prevent from closing it with Alt+F4
        pass

    def close(self):
        # The dialog may haven't even been created
        if self.dialog:
            self.timer.Stop()
            self.dialog.Destroy()


class DialogActivate(object):
    def __init__(self, filename):
        self.filename = filename
        self.dialog = None
        self.WRAP = 320

    def create(self):
        self.dialog = wx.Dialog(wxgui_api.get_main_frame(),
                                title="Old alarms search",
                                style=wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX)

        self.csizer = wx.BoxSizer(wx.VERTICAL)
        self.dialog.SetSizer(self.csizer)

        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.csizer.Add(self.vsizer, 1, flag=wx.EXPAND | wx.ALL, border=12)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vsizer.Add(hsizer, flag=wx.EXPAND | wx.BOTTOM, border=4)

        icon = wx.StaticBitmap(self.dialog, bitmap=wx.ArtProvider.GetBitmap(
                                        'appointment-soon', wx.ART_CMN_DIALOG))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        self.label = wx.StaticText(self.dialog, label="Filtering the old "
                                "alarms found for {}...".format(self.filename))
        self.label.Wrap(self.WRAP)
        hsizer.Add(self.label)

        self.gauge = wx.Gauge(self.dialog)
        self.vsizer.Add(self.gauge, flag=wx.EXPAND | wx.BOTTOM, border=4)
        self.timer = wx.CallLater(100, self._pulse)

        self.csizer.Fit(self.dialog)

        self.dialog.Bind(wx.EVT_CLOSE, self._handle_close)

        # Don't show it modal because only one modal dialog can be shown at a
        # time, and managing the races among them would be a bigger mess than
        # making it safe to show them non modal
        self.dialog.Show()

    def choose_old_alarms_unique(self, count):
        self.vsizer.Hide(self.gauge)

        self.label.SetLabelText("{} old alarms found for {}:".format(count,
                                                                self.filename))
        # Re-wrap the text in case of a long filename, so that it will take a
        # new line if needed; it must be done *before* self.csizer.Fit
        self.label.Wrap(self.WRAP)

        self.all_ = wx.Button(self.dialog,
                                        label="Activate all the found alarms")
        self.vsizer.Add(self.all_, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        self.dialog.Bind(wx.EVT_BUTTON, self._activate_all_alarms, self.all_)

        self.unique = wx.Button(self.dialog,
                    label="Activate only the most recent alarm for each item")
        self.vsizer.Add(self.unique, flag=wx.ALIGN_CENTER)

        self.dialog.Bind(wx.EVT_BUTTON, self._activate_unique_alarms,
                                                                self.unique)

        self.csizer.Fit(self.dialog)

    def _pre_activate_alarms(self):
        self.vsizer.Show(self.gauge)
        self.vsizer.Hide(self.all_)
        self.vsizer.Hide(self.unique)

        self.label.SetLabelText("Activating the old alarms for {}:".format(
                                                                self.filename))
        # Re-wrap the text in case of a long filename, so that it will take a
        # new line if needed; it must be done *before* self.csizer.Fit
        self.label.Wrap(self.WRAP)

        self.csizer.Fit(self.dialog)

    def _activate_all_alarms(self, event):
        self._pre_activate_alarms()
        organism_alarms_api.activate_old_alarms(self.filename, False)

    def _activate_unique_alarms(self, event):
        self._pre_activate_alarms()
        organism_alarms_api.activate_old_alarms(self.filename, True)

    def _pulse(self):
        self.gauge.Pulse()
        self.timer.Restart()

    def _handle_close(self, event):
        # Resetting the style of the dialog without wx.CLOSE_BOX is not enough
        # because it doesn't prevent from closing it with Alt+F4
        pass

    def close(self):
        # The dialog may haven't even been created
        if self.dialog:
            self.timer.Stop()
            self.dialog.Destroy()

            # This is needed in case the database (or the whole application) is
            # closed before any button has been clicked: in that case the
            # activation algorithm in organism_alarms must be unlocked in this
            # way, or its thread will never complete, thus hanging the closure
            # of the application
            organism_alarms_api.activate_old_alarms(self.filename, None)


def main():
    Dialogs()
