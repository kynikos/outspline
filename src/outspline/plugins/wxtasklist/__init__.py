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

import sys
import wx

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.extensions.organism_alarms_api as organism_alarms_api
import outspline.interfaces.wxgui_api as wxgui_api

import list as list_
import filters
import menus


class TaskListPanel(wx.Panel):
    def __init__(self, parent, tasklist, acctable):
        wx.Panel.__init__(self, parent)
        self.tasklist = tasklist
        self.acctable = acctable

    def init_tab_menu(self, tasklist):
        self.ctabmenu = menus.TabContextMenu(tasklist)

    def get_tab_context_menu(self):
        self.ctabmenu.update()
        return self.ctabmenu

    def get_accelerators_table(self):
        return self.acctable

    def close_tab(self):
        self.tasklist._hide()


class TaskList(object):
    def __init__(self, parent):
        self.YEAR_LIMITS = self._set_search_limits()

        wxgui_api.install_bundled_icon("wxtasklist", '@activealarms',
                                                    ("activealarms16.png", ))
        wxgui_api.install_bundled_icon("wxtasklist", '@dismiss',
                                                        ("dismiss16.png", ))
        wxgui_api.install_bundled_icon("wxtasklist", '@navigator',
                                                ("Tango", "navigator16.png"))
        wxgui_api.install_bundled_icon("wxtasklist", '@scroll',
                                                    ("Tango", "scroll16.png"))
        wxgui_api.install_bundled_icon("wxtasklist", '@snooze',
                                                            ("snooze16.png", ))
        wxgui_api.install_bundled_icon("wxtasklist", '@snoozedialog',
                                                    ("snoozedialog48.png", ))
        wxgui_api.install_bundled_icon("wxtasklist", '@tasklist',
                                                ("Tango", "tasklist16.png"))

        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

        aconfig = self.config("ExtendedShortcuts")
        accelerators = {
            aconfig["prev_page"]:
                            lambda event: self.navigator.show_previous_page(),
            aconfig["next_page"]:
                                lambda event: self.navigator.show_next_page(),
            aconfig["apply"]: lambda event: self.navigator.apply(),
            aconfig["set"]: lambda event: self.navigator.set(),
            aconfig["reset"]: lambda event: self.navigator.reset(),
            aconfig["autoscroll"]:
                        lambda event: self.list_.autoscroll.execute_force(),
            aconfig["toggle_autoscroll"]:
                                lambda event: self.list_.autoscroll.toggle(),
            aconfig["find"]: lambda event: self.list_.find_in_tree(),
            aconfig["edit"]: lambda event: self.list_.edit_items(),
            aconfig["snooze"]:
                lambda event: self.list_.snooze_selected_alarms_for_custom(),
            aconfig["snooze_all"]:
                    lambda event: self.list_.snooze_all_alarms_for_custom(),
            aconfig["dismiss"]:
                            lambda event: self.list_.dismiss_selected_alarms(),
            aconfig["dismiss_all"]:
                                lambda event: self.list_.dismiss_all_alarms(),
            aconfig["toggle_navigator"]:
                                lambda event: self.navigator.toggle_shown(),
            aconfig["toggle_gaps"]: lambda event: self.list_.toggle_gaps(),
            aconfig["toggle_overlappings"]:
                                lambda event: self.list_.toggle_overlappings(),
        }
        accelerators.update(wxgui_api.get_right_nb_generic_accelerators())
        acctable = wxgui_api.generate_right_nb_accelerators(accelerators)

        # Note that the remaining border is due to the SplitterWindow, whose
        # border cannot be removed because it's used to highlight the sash
        # See also http://trac.wxwidgets.org/ticket/12413
        # and http://trac.wxwidgets.org/changeset/66230
        self.panel = TaskListPanel(parent, self, acctable)
        self.pbox = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.pbox)

        self.nb_icon_index = wxgui_api.add_right_nb_image(
                                    wxgui_api.get_notebook_icon('@tasklist'))
        self.nb_icon_refresh_index = wxgui_api.add_right_nb_image(
                                    wxgui_api.get_notebook_icon('@refresh'))

        # filters.Navigator must be instantiated *before*
        # list_.OccurrencesView, because the former sets the filter for the
        # latter; note that inverting the order would work anyway because of a
        # usually favorable race condition (the list is refreshed after an
        # asynchronous delay), but of course that shouldn't be relied on
        self.navigator = filters.Navigator(self, self.YEAR_LIMITS)
        self.warningsbar = WarningsBar(self.panel)
        self.list_ = list_.OccurrencesView(self, self.navigator, self.YEAR_LIMITS)

        self.mainmenu = menus.MainMenu(self)
        self.viewmenu = menus.ViewMenu(self)
        self.panel.init_tab_menu(self)
        self.list_._init_context_menu(self.mainmenu)

        self.pbox.Add(self.warningsbar.get_panel(), flag=wx.EXPAND)
        self.pbox.Add(self.list_.listview, 1, flag=wx.EXPAND)

        wxgui_api.bind_to_show_main_window(self._handle_show_main_window)
        wxgui_api.bind_to_hide_main_window(self._handle_hide_main_window)
        wxgui_api.bind_to_open_database(self._handle_open_database)
        core_api.bind_to_exit_app_1(self._handle_exit_application)

    def _set_search_limits(self):
        if sys.maxsize > 2**32:
            # 64bit
            # According to https://docs.python.org/2/library/time.html
            #  "Values 100-1899 are always illegal"
            #  This wouldn't apply to Python 3, if I could use it...
            #  The maximum would be 9999, but keep it reasonable
            return (1900, 2200)
        else:
            # 32bit
            # Here the limits are of course given by the integer size
            return (1902, 2037)

    def _handle_show_main_window(self, kwargs):
        if self.is_shown():
            self._enable()

    def _handle_hide_main_window(self, kwargs):
        if self.is_shown():
            self._disable()

    def _handle_open_database(self, kwargs):
        # Do not add the plugin if there's no database open, otherwise strange
        # bugs will happen, like the keyboard menu shortcuts not working until
        # a database is opened. Add the plugin only when the first database is
        # opened.
        self._show()
        wxgui_api.bind_to_open_database(self._handle_open_database, False)

    def is_shown(self):
        return wxgui_api.is_page_in_right_nb(self.panel)

    def toggle_shown(self, event):
        if self.is_shown():
            self._hide()
        elif wxgui_api.get_databases_count():
            self._show()

    def _show(self):
        wxgui_api.add_plugin_to_right_nb(self.panel, "",
                                                    imageId=self.nb_icon_index)
        self._enable()

    def _hide(self):
        # Showing/hiding is the correct behaviour: allowing multiple instances
        # of tasklist notebook tabs would need finding a way to refresh only
        # one at a time, probably only the selected one, thus requiring to
        # update it every time it gets selected, which would in turn make
        # everything more sluggish
        wxgui_api.hide_right_nb_page(self.panel)
        self._disable()

    def _enable(self):
        self.list_.enable_refresh()
        self.list_.refresh()
        self._update_tab_label()

        organism_alarms_api.bind_to_alarm(self._update_tab_label_after)
        organism_alarms_api.bind_to_alarm_off(self._update_tab_label)
        wxgui_api.bind_to_close_database(self._update_tab_label)

    def _disable(self):
        self.list_.disable_refresh()

        organism_alarms_api.bind_to_alarm(self._update_tab_label, False)
        organism_alarms_api.bind_to_alarm_off(self._update_tab_label, False)
        wxgui_api.bind_to_close_database(self._update_tab_label, False)

    def _handle_exit_application(self, kwargs):
        self.list_.cancel_refresh()

        configfile = coreaux_api.get_user_config_file()
        self.list_.save_configuration()
        self.navigator.save_configuration()
        self.config.export_upgrade(configfile)

    def set_tab_icon_stopped(self):
        wxgui_api.set_right_nb_page_image(self.panel, self.nb_icon_index)

    def set_tab_icon_ongoing(self):
        wxgui_api.set_right_nb_page_image(self.panel,
                                                    self.nb_icon_refresh_index)

    def show_warning(self, message):
        self.warningsbar.show(message)

    def dismiss_warning(self):
        self.warningsbar.hide()

    def _update_tab_label_after(self, kwargs):
        wx.CallAfter(self._update_tab_label, kwargs)

    def _update_tab_label(self, kwargs=None):
        nalarms = organism_alarms_api.get_number_of_active_alarms()
        wxgui_api.set_right_nb_page_title(self.panel,
                                                "{} alarms".format(nalarms))

    def work_around_bug332(self):
        # Temporary workaround for bug #332
        return self.list_.listview


class WarningsBar(object):
    def __init__(self, parent):
        self.parent = parent
        COLOR = wx.Colour(255, 126, 0)

        self.panel = wx.Panel(parent)
        self.panel.SetBackgroundColour(COLOR)
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(box)

        icon = wx.StaticBitmap(self.panel, bitmap=wxgui_api.get_message_icon(
                                                                '@warning'))
        box.Add(icon, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=4)

        self.message = wx.StaticText(self.panel, label="")
        box.Add(self.message, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=4)

        self.panel.Show(False)

    def get_panel(self):
        return self.panel

    def show(self, message):
        self.message.SetLabelText(message)
        self.panel.Show()
        self.parent.Layout()

    def hide(self):
        self.panel.Show(False)
        self.parent.Layout()


def main():
    TaskList(wxgui_api.get_right_nb())
