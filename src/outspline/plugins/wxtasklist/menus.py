# Outspline - A highly modular and extensible outliner.
# Copyright (C) 2011 Dario Giovannetti <dev@dariogiovannetti.net>
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

import wx

from outspline.static.wxclasses.timectrls import TimeSpanCtrl

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api
import outspline.extensions.organism_alarms_api as organism_alarms_api

import list as list_
import filters as filters_
import export


class MainMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)

        self.tasklist = tasklist
        self.occview = tasklist.list_

        self.ID_NAVIGATOR = wx.NewId()
        self.ID_SCROLL = wx.NewId()
        self.ID_FIND = wx.NewId()
        self.ID_EDIT = wx.NewId()
        self.ID_SNOOZE = wx.NewId()
        self.ID_SNOOZE_ALL = wx.NewId()
        self.ID_SNOOZE_FOR_SEL = wx.NewId()
        self.ID_SNOOZE_FOR_ALL = wx.NewId()
        self.ID_DISMISS = wx.NewId()
        self.ID_DISMISS_ALL = wx.NewId()
        self.ID_EXPORT = wx.NewId()

        config = coreaux_api.get_plugin_configuration('wxtasklist')

        # Using a set here to remove any duplicates would lose the order of the
        # times
        snooze_times = config['snooze_times'].split(' ')
        self.snoozetimesconf = []

        for stime in snooze_times:
            ID_SNOOZE_FOR_N_SEL = wx.NewId()
            ID_SNOOZE_FOR_N_ALL = wx.NewId()
            time = int(stime) * 60
            number, unit = TimeSpanCtrl.compute_widget_values(time)
            # Duplicate time values are not supported, just make sure they
            # don't crash the application
            self.snoozetimesconf.append(((ID_SNOOZE_FOR_N_SEL,
                                    ID_SNOOZE_FOR_N_ALL), time, number, unit))

        self.navigator_submenu = NavigatorMenu(tasklist)
        self.snooze_selected_submenu = SnoozeSelectedConfigMenu(tasklist, self)
        self.snooze_all_submenu = SnoozeAllConfigMenu(tasklist, self)
        self.export_submenu = ExportMenu(tasklist)

        shconf = config("GlobalShortcuts")

        self.navigator = wx.MenuItem(self, self.ID_NAVIGATOR, 'Na&vigator',
                        'Navigator actions', subMenu=self.navigator_submenu)
        self.scroll = wx.MenuItem(self, self.ID_SCROLL,
                "Scro&ll to ongoing\t{}".format(shconf['scroll_to_ongoing']),
                "Order the list by State and scroll "
                "to the first ongoing event")
        self.find = wx.MenuItem(self, self.ID_FIND,
            "&Find in database\t{}".format(shconf('Items')['find_selected']),
            "Select the database items associated to the selected events")
        self.edit = wx.MenuItem(self, self.ID_EDIT,
                "&Edit selected\t{}".format(shconf('Items')['edit_selected']),
                "Open in the editor the database items associated "
                "to the selected events")

        self.snooze = wx.MenuItem(self, self.ID_SNOOZE, "&Snooze selected",
                                        "Snooze the selected alarms",
                                        subMenu=self.snooze_selected_submenu)
        self.snooze_all = wx.MenuItem(self, self.ID_SNOOZE_ALL,
                                "S&nooze all", "Snooze all the active alarms",
                                subMenu=self.snooze_all_submenu)

        self.dismiss = wx.MenuItem(self, self.ID_DISMISS,
                                        "&Dismiss selected\t{}".format(
                                        shconf('Items')['dismiss_selected']),
                                        "Dismiss the selected alarms")
        self.dismiss_all = wx.MenuItem(self, self.ID_DISMISS_ALL,
                    "Dis&miss all\t{}".format(shconf('Items')['dismiss_all']),
                    "Dismiss all the active alarms")
        self.export = wx.MenuItem(self, self.ID_EXPORT, 'E&xport view',
                                        'Export the current view to a file',
                                        subMenu=self.export_submenu)

        self.navigator.SetBitmap(wxgui_api.get_menu_icon('@navigator'))
        self.scroll.SetBitmap(wxgui_api.get_menu_icon('@scroll'))
        self.find.SetBitmap(wxgui_api.get_menu_icon('@dbfind'))
        self.edit.SetBitmap(wxgui_api.get_menu_icon('@edit'))
        self.snooze.SetBitmap(wxgui_api.get_menu_icon('@snooze'))
        self.snooze_all.SetBitmap(wxgui_api.get_menu_icon('@snooze'))
        self.dismiss.SetBitmap(wxgui_api.get_menu_icon('@dismiss'))
        self.dismiss_all.SetBitmap(wxgui_api.get_menu_icon('@dismiss'))
        self.export.SetBitmap(wxgui_api.get_menu_icon('@saveas'))

        self.AppendItem(self.navigator)
        self.AppendItem(self.scroll)
        self.AppendSeparator()
        self.AppendItem(self.find)
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.snooze)
        self.AppendItem(self.snooze_all)
        self.AppendItem(self.dismiss)
        self.AppendItem(self.dismiss_all)
        self.AppendSeparator()
        self.AppendItem(self.export)

        wxgui_api.bind_to_menu(self._scroll_to_ongoing, self.scroll)
        wxgui_api.bind_to_menu(self._find_in_tree, self.find)
        wxgui_api.bind_to_menu(self._edit_items, self.edit)
        wxgui_api.bind_to_menu(self._dismiss_selected_alarms, self.dismiss)
        wxgui_api.bind_to_menu(self._dismiss_all_alarms, self.dismiss_all)

        wxgui_api.bind_to_update_menu_items(self._update_items)
        wxgui_api.bind_to_reset_menu_items(self._reset_items)


        wxgui_api.insert_menu_main_item('S&chedule',
                                    wxgui_api.get_menu_view_position(), self)

    def _update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.navigator_submenu.update_items()

            tab = wxgui_api.get_selected_right_nb_tab()

            if tab is self.tasklist.panel:
                self.scroll.Enable()

                sel = self.occview.listview.GetFirstSelected()

                self.find.Enable(False)
                self.edit.Enable(False)
                self.snooze.Enable(False)
                self.dismiss.Enable(False)

                while sel > -1:
                    item = self.occview.occs[
                                    self.occview.listview.GetItemData(sel)]

                    canbreak = 0

                    # Check item is not a gap or an overlapping
                    if item.get_filename() is not None:
                        self.find.Enable()
                        self.edit.Enable()
                        canbreak += 1

                    if item.get_alarm() is False:
                        self.snooze.Enable()
                        self.dismiss.Enable()
                        canbreak += 1

                    if canbreak > 1:
                        break

                    sel = self.occview.listview.GetNextSelected(sel)

                # Note that "all" means all the visible active alarms; some
                # may be hidden in the current view; this is also why these
                # actions must be disabled if the tasklist is not focused
                if len(self.occview.get_active_alarms()) > 0:
                    self.snooze_all.Enable()
                    self.dismiss_all.Enable()
                else:
                    self.snooze_all.Enable(False)
                    self.dismiss_all.Enable(False)

                self.navigator.Enable()
                self.navigator_submenu.update_items_selected()

                self.export.Enable()

            else:
                self.navigator.Enable(False)
                self.scroll.Enable(False)
                self.find.Enable(False)
                self.edit.Enable(False)
                self.snooze.Enable(False)
                self.snooze_all.Enable(False)
                self.dismiss.Enable(False)
                self.dismiss_all.Enable(False)
                self.export.Enable(False)

    def _reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.navigator.Enable()
        self.scroll.Enable()
        self.find.Enable()
        self.edit.Enable()
        self.snooze.Enable()
        self.snooze_all.Enable()
        self.dismiss.Enable()
        self.dismiss_all.Enable()
        self.export.Enable()

        self.navigator_submenu.reset_items()

    def _scroll_to_ongoing(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.autoscroll.execute_force()

    def _find_in_tree(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.find_in_tree()

    def _edit_items(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.edit_items()

    def _dismiss_selected_alarms(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.dismiss_selected_alarms()

    def _dismiss_all_alarms(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.dismiss_all_alarms()


class NavigatorMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.ID_PREVIOUS = wx.NewId()
        self.ID_NEXT = wx.NewId()
        self.ID_APPLY = wx.NewId()
        self.ID_SET = wx.NewId()
        self.ID_RESET = wx.NewId()

        config = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                'GlobalShortcuts')('Navigator')

        self.previous = wx.MenuItem(self, self.ID_PREVIOUS,
                            "&Previous page\t{}".format(config['previous']),
                            "View the previous page of events")
        self.next = wx.MenuItem(self, self.ID_NEXT,
                                    "&Next page\t{}".format(config['next']),
                                    "View the next page of events")
        self.apply = wx.MenuItem(self, self.ID_APPLY,
                                "&Apply filters\t{}".format(config['apply']),
                                "Apply the configured filters")
        self.set = wx.MenuItem(self, self.ID_SET,
                                    "Se&t filters\t{}".format(config['set']),
                                    "Apply and save the configured filters")
        self.reset = wx.MenuItem(self, self.ID_RESET,
                                "&Reset filters\t{}".format(config['reset']),
                                "Reset the filters to the saved ones")

        self.previous.SetBitmap(wxgui_api.get_menu_icon('@left'))
        self.next.SetBitmap(wxgui_api.get_menu_icon('@right'))
        self.apply.SetBitmap(wxgui_api.get_menu_icon('@apply'))
        self.set.SetBitmap(wxgui_api.get_menu_icon('@save'))
        self.reset.SetBitmap(wxgui_api.get_menu_icon('@undo'))

        self.AppendSeparator()
        self.AppendItem(self.previous)
        self.AppendItem(self.next)
        self.AppendItem(self.apply)
        self.AppendItem(self.set)
        self.AppendItem(self.reset)

        wxgui_api.bind_to_menu(self._go_to_previous_page, self.previous)
        wxgui_api.bind_to_menu(self._go_to_next_page, self.next)
        wxgui_api.bind_to_menu(self._apply_filters, self.apply)
        wxgui_api.bind_to_menu(self._set_filters, self.set)
        wxgui_api.bind_to_menu(self._reset_filters, self.reset)

    def update_items(self):
        self.previous.Enable(False)
        self.next.Enable(False)
        self.apply.Enable(False)
        self.set.Enable(False)
        self.reset.Enable(False)

    def update_items_selected(self):
        self.previous.Enable()
        self.next.Enable()
        self.apply.Enable()
        self.set.Enable()
        self.reset.Enable()

    def reset_items(self):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.previous.Enable()
        self.next.Enable()
        self.apply.Enable()
        self.set.Enable()
        self.reset.Enable()

    def _go_to_previous_page(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.navigator.show_previous_page()

    def _go_to_next_page(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.navigator.show_next_page()

    def _apply_filters(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.navigator.apply()

    def _set_filters(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.navigator.set()

    def _reset_filters(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.navigator.reset()


class ExportMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.exporter = export.Exporter(tasklist.list_)

        self.ID_JSON = wx.NewId()
        self.ID_TSV = wx.NewId()
        self.ID_XML = wx.NewId()

        self.json = wx.MenuItem(self, self.ID_JSON,
                            "&JSON...", "Export to JSON format")
        self.tsv = wx.MenuItem(self, self.ID_TSV,
                            "&TSV...", "Export to tab-separated values format")
        self.xml = wx.MenuItem(self, self.ID_XML,
                            "&XML...", "Export to XML format")

        self.json.SetBitmap(wxgui_api.get_menu_icon('@file'))
        self.tsv.SetBitmap(wxgui_api.get_menu_icon('@file'))
        self.xml.SetBitmap(wxgui_api.get_menu_icon('@file'))

        self.AppendItem(self.json)
        self.AppendItem(self.tsv)
        self.AppendItem(self.xml)

        wxgui_api.bind_to_menu(self._export_to_json, self.json)
        wxgui_api.bind_to_menu(self._export_to_tsv, self.tsv)
        wxgui_api.bind_to_menu(self._export_to_xml, self.xml)

    def _export_to_json(self, event):
        if self.tasklist.is_shown():
            self.exporter.export_to_json()

    def _export_to_tsv(self, event):
        if self.tasklist.is_shown():
            self.exporter.export_to_tsv()

    def _export_to_xml(self, event):
        if self.tasklist.is_shown():
            self.exporter.export_to_xml()


class ViewMenu(object):
    def __init__(self, tasklist):
        self.tasklist = tasklist
        self.occview = tasklist.list_

        self.ID_EVENTS = wx.NewId()
        self.ID_SHOW = wx.NewId()
        self.ID_FOCUS = wx.NewId()
        self.ID_ALARMS = wx.NewId()
        self.ID_TOGGLE_NAVIGATOR = wx.NewId()
        self.ID_GAPS = wx.NewId()
        self.ID_OVERLAPS = wx.NewId()
        self.ID_AUTOSCROLL = wx.NewId()

        submenu = wx.Menu()
        self.alarms_submenu = AlarmsMenu(tasklist)

        config = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                    'GlobalShortcuts')('View')


        self.events = wx.MenuItem(wxgui_api.get_menu_view(), self.ID_EVENTS,
                        '&Schedule', 'Schedule navigation actions',
                        subMenu=submenu)
        self.show = wx.MenuItem(submenu, self.ID_SHOW,
                                "Show &panel\t{}".format(config['show']),
                                "Show the schedule panel", kind=wx.ITEM_CHECK)
        self.focus = wx.MenuItem(submenu, self.ID_FOCUS,
                        "&Focus\t{}".format(config['focus']),
                        "Set focus on the schedule tab")
        self.alarms = wx.MenuItem(submenu, self.ID_ALARMS, '&Active alarms',
                                        'Set the visibility of active alarms',
                                        subMenu=self.alarms_submenu)
        self.navigator = wx.MenuItem(submenu, self.ID_TOGGLE_NAVIGATOR,
                        "Show &navigator\t{}".format(config['show_navigator']),
                        "Show or hide the navigator bar", kind=wx.ITEM_CHECK)
        self.gaps = wx.MenuItem(submenu, self.ID_GAPS,
                            "Show &gaps\t{}".format(config['toggle_gaps']),
                            "Show any unallocated time in the shown interval",
                            kind=wx.ITEM_CHECK)
        self.overlaps = wx.MenuItem(submenu, self.ID_OVERLAPS,
                "Show &overlappings\t{}".format(config['toggle_overlappings']),
                "Show time intervals used by more than one event",
                kind=wx.ITEM_CHECK)
        self.autoscroll = wx.MenuItem(submenu, self.ID_AUTOSCROLL,
                                            "Enable a&uto-scroll",
                                            "Auto-scroll to the first ongoing "
                                            "event when refreshing",
                                            kind=wx.ITEM_CHECK)

        self.events.SetBitmap(wxgui_api.get_menu_icon('@tasklist'))
        self.focus.SetBitmap(wxgui_api.get_menu_icon('@jump'))
        self.alarms.SetBitmap(wxgui_api.get_menu_icon('@activealarms'))

        wxgui_api.insert_menu_right_tab_group(self.events)
        submenu.AppendItem(self.show)
        submenu.AppendItem(self.focus)
        submenu.AppendSeparator()
        submenu.AppendItem(self.alarms)
        submenu.AppendItem(self.navigator)
        submenu.AppendItem(self.gaps)
        submenu.AppendItem(self.overlaps)
        submenu.AppendItem(self.autoscroll)

        wxgui_api.bind_to_menu(self.tasklist.toggle_shown, self.show)
        wxgui_api.bind_to_menu(self._focus, self.focus)
        wxgui_api.bind_to_menu(self._toggle_navigator, self.navigator)
        wxgui_api.bind_to_menu(self._show_gaps, self.gaps)
        wxgui_api.bind_to_menu(self._show_overlappings, self.overlaps)
        wxgui_api.bind_to_menu(self._enable_autoscroll, self.autoscroll)

        wxgui_api.bind_to_reset_menu_items(self._reset_items)
        wxgui_api.bind_to_menu_view_update(self._update_items)

    def _update_items(self, kwargs):
        self.navigator.Check(check=self.tasklist.navigator.is_shown())
        self.gaps.Check(check=self.occview.show_gaps)
        self.overlaps.Check(check=self.occview.show_overlappings)
        self.autoscroll.Check(check=self.occview.autoscroll.is_enabled())

        self.alarms_submenu.update_items()

        if self.tasklist.is_shown():
            self.show.Check(check=True)

            if wxgui_api.get_databases_count() > 0:
                self.focus.Enable()
            else:
                self.focus.Enable(False)

            self.alarms.Enable()
            self.navigator.Enable()
            self.gaps.Enable()
            self.overlaps.Enable()
            self.autoscroll.Enable()
        else:
            self.show.Check(check=False)
            self.focus.Enable(False)
            self.alarms.Enable(False)
            self.navigator.Enable(False)
            self.gaps.Enable(False)
            self.overlaps.Enable(False)
            self.autoscroll.Enable(False)

    def _reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.show.Enable()
        self.focus.Enable()
        self.alarms.Enable()
        self.navigator.Enable()
        self.gaps.Enable()
        self.overlaps.Enable()
        self.autoscroll.Enable()

    def _focus(self, event):
        if self.tasklist.is_shown():
            wxgui_api.select_right_nb_tab(self.tasklist.panel)
            self.occview.set_focus()

    def _toggle_navigator(self, event):
        self.tasklist.navigator.toggle_shown()

    def _show_gaps(self, event):
        if self.tasklist.is_shown():
            self.occview.toggle_gaps()

    def _show_overlappings(self, event):
        if self.tasklist.is_shown():
            self.occview.toggle_overlappings()

    def _enable_autoscroll(self, event):
        self.occview.autoscroll.toggle()


class AlarmsMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist
        self.occview = tasklist.list_

        self.ID_IN_RANGE = wx.NewId()
        self.ID_AUTO = wx.NewId()
        self.ID_ALL = wx.NewId()

        self.inrange = wx.MenuItem(self, self.ID_IN_RANGE,
                        "Show in &range",
                        "Show only the active alarms in the filtered range",
                        kind=wx.ITEM_RADIO)
        self.auto = wx.MenuItem(self, self.ID_AUTO,
                    "Show &smartly",
                    "Show all the active alarms only if current time is shown",
                    kind=wx.ITEM_RADIO)
        self.all = wx.MenuItem(self, self.ID_ALL,
                        "Show &all",
                        "Always show all the active alarms",
                        kind=wx.ITEM_RADIO)

        self.modes_to_items = {
            'in_range': self.inrange,
            'auto': self.auto,
            'all': self.all,
        }

        self.AppendItem(self.inrange)
        self.AppendItem(self.auto)
        self.AppendItem(self.all)

        wxgui_api.bind_to_menu(self._set_in_range, self.inrange)
        wxgui_api.bind_to_menu(self._set_auto, self.auto)
        wxgui_api.bind_to_menu(self._set_all, self.all)

    def update_items(self):
        self.modes_to_items[self.occview.active_alarms_mode].Check()

    def _set_in_range(self, event):
        if self.tasklist.is_shown():
            self.occview.active_alarms_mode = 'in_range'
            self.occview.refresh()

    def _set_auto(self, event):
        if self.tasklist.is_shown():
            self.occview.active_alarms_mode = 'auto'
            self.occview.refresh()

    def _set_all(self, event):
        if self.tasklist.is_shown():
            self.occview.active_alarms_mode = 'all'
            self.occview.refresh()


class TabContextMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.navigator_submenu = TabContextNavigatorMenu(tasklist)
        self.alarms_submenu = TabContextAlarmsMenu(tasklist)
        self.snooze_all_submenu = SnoozeAllConfigMenu(tasklist,
                                                            tasklist.mainmenu)
        self.export_submenu = TabContextExportMenu(tasklist)

        self.show = wx.MenuItem(self, self.tasklist.viewmenu.ID_SHOW,
                                                                "Hide &panel")
        self.navigator = wx.MenuItem(self, self.tasklist.mainmenu.ID_NAVIGATOR,
                                'Na&vigator', subMenu=self.navigator_submenu)
        self.alarms = wx.MenuItem(self, self.tasklist.viewmenu.ID_ALARMS,
                                '&Active alarms', subMenu=self.alarms_submenu)
        self.gaps = wx.MenuItem(self, self.tasklist.viewmenu.ID_GAPS,
                                            "Show &gaps", kind=wx.ITEM_CHECK)
        self.overlaps = wx.MenuItem(self,
                    self.tasklist.viewmenu.ID_OVERLAPS, "Show &overlappings",
                    kind=wx.ITEM_CHECK)
        self.scroll = wx.MenuItem(self,
                    self.tasklist.mainmenu.ID_SCROLL, "Scro&ll to ongoing")
        self.autoscroll = wx.MenuItem(self,
                                        self.tasklist.viewmenu.ID_AUTOSCROLL,
                                        "Enable a&uto-scroll",
                                        kind=wx.ITEM_CHECK)
        self.snooze_all = wx.MenuItem(self,
                                self.tasklist.mainmenu.ID_SNOOZE_ALL,
                                "S&nooze all", subMenu=self.snooze_all_submenu)
        self.dismiss_all = wx.MenuItem(self,
                        self.tasklist.mainmenu.ID_DISMISS_ALL, "Dis&miss all")
        self.export = wx.MenuItem(self, self.tasklist.mainmenu.ID_EXPORT,
                                'E&xport view', subMenu=self.export_submenu)

        self.show.SetBitmap(wxgui_api.get_menu_icon('@close'))
        self.navigator.SetBitmap(wxgui_api.get_menu_icon('@navigator'))
        self.alarms.SetBitmap(wxgui_api.get_menu_icon('@activealarms'))
        self.scroll.SetBitmap(wxgui_api.get_menu_icon('@scroll'))
        self.snooze_all.SetBitmap(wxgui_api.get_menu_icon('@snooze'))
        self.dismiss_all.SetBitmap(wxgui_api.get_menu_icon('@dismiss'))
        self.export.SetBitmap(wxgui_api.get_menu_icon('@saveas'))

        self.AppendItem(self.show)
        self.AppendSeparator()
        self.AppendItem(self.navigator)
        self.AppendItem(self.alarms)
        self.AppendItem(self.gaps)
        self.AppendItem(self.overlaps)
        self.AppendSeparator()
        self.AppendItem(self.scroll)
        self.AppendItem(self.autoscroll)
        self.AppendSeparator()
        self.AppendItem(self.snooze_all)
        self.AppendItem(self.dismiss_all)
        self.AppendSeparator()
        self.AppendItem(self.export)

    def update(self):
        if len(self.tasklist.list_.get_active_alarms()) > 0:
            self.snooze_all.Enable()
            self.dismiss_all.Enable()
        else:
            self.snooze_all.Enable(False)
            self.dismiss_all.Enable(False)

        self.gaps.Check(check=self.tasklist.list_.show_gaps)
        self.overlaps.Check(check=self.tasklist.list_.show_overlappings)
        self.autoscroll.Check(
                            check=self.tasklist.list_.autoscroll.is_enabled())

        self.navigator_submenu.update_items()
        self.alarms_submenu.update_items()


class TabContextNavigatorMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.navigator = wx.MenuItem(self,
                self.tasklist.viewmenu.ID_TOGGLE_NAVIGATOR,
                "&Show", "Show or hide the navigator bar", kind=wx.ITEM_CHECK)
        self.previous = wx.MenuItem(self,
                        self.tasklist.mainmenu.navigator_submenu.ID_PREVIOUS,
                        "&Previous page")
        self.next = wx.MenuItem(self,
                            self.tasklist.mainmenu.navigator_submenu.ID_NEXT,
                            "&Next page")
        self.apply = wx.MenuItem(self,
                            self.tasklist.mainmenu.navigator_submenu.ID_APPLY,
                            "&Apply filters")
        self.set = wx.MenuItem(self,
                            self.tasklist.mainmenu.navigator_submenu.ID_SET,
                            "Se&t filters")
        self.reset = wx.MenuItem(self,
                            self.tasklist.mainmenu.navigator_submenu.ID_RESET,
                            "&Reset filters")

        self.previous.SetBitmap(wxgui_api.get_menu_icon('@left'))
        self.next.SetBitmap(wxgui_api.get_menu_icon('@right'))
        self.apply.SetBitmap(wxgui_api.get_menu_icon('@apply'))
        self.set.SetBitmap(wxgui_api.get_menu_icon('@save'))
        self.reset.SetBitmap(wxgui_api.get_menu_icon('@undo'))

        self.AppendItem(self.navigator)
        self.AppendSeparator()
        self.AppendItem(self.previous)
        self.AppendItem(self.next)
        self.AppendItem(self.apply)
        self.AppendItem(self.set)
        self.AppendItem(self.reset)

    def update_items(self):
        self.navigator.Check(check=self.tasklist.navigator.is_shown())


class TabContextAlarmsMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.occview = tasklist.list_

        self.inrange = wx.MenuItem(self,
                                tasklist.viewmenu.alarms_submenu.ID_IN_RANGE,
                                "Show in &range", kind=wx.ITEM_RADIO)
        self.auto = wx.MenuItem(self,
                                tasklist.viewmenu.alarms_submenu.ID_AUTO,
                                "Show &smartly", kind=wx.ITEM_RADIO)
        self.all = wx.MenuItem(self,
                                tasklist.viewmenu.alarms_submenu.ID_ALL,
                                "Show &all", kind=wx.ITEM_RADIO)

        self.modes_to_items = {
            'in_range': self.inrange,
            'auto': self.auto,
            'all': self.all,
        }

        self.AppendItem(self.inrange)
        self.AppendItem(self.auto)
        self.AppendItem(self.all)

    def update_items(self):
        self.modes_to_items[self.occview.active_alarms_mode].Check()


class TabContextExportMenu(wx.Menu):
    def __init__(self, tasklist):
        wx.Menu.__init__(self)

        self.json = wx.MenuItem(self, tasklist.mainmenu.export_submenu.ID_JSON,
                                                                    "&JSON...")
        self.tsv = wx.MenuItem(self, tasklist.mainmenu.export_submenu.ID_TSV,
                                                                    "&TSV...")
        self.xml = wx.MenuItem(self, tasklist.mainmenu.export_submenu.ID_XML,
                                                                    "&XML...")

        self.json.SetBitmap(wxgui_api.get_menu_icon('@file'))
        self.tsv.SetBitmap(wxgui_api.get_menu_icon('@file'))
        self.xml.SetBitmap(wxgui_api.get_menu_icon('@file'))

        self.AppendItem(self.json)
        self.AppendItem(self.tsv)
        self.AppendItem(self.xml)


class ListContextMenu(wx.Menu):
    def __init__(self, tasklist, mainmenu):
        wx.Menu.__init__(self)
        self.tasklist = tasklist
        self.occview = tasklist.list_
        self.mainmenu = mainmenu

        self.snooze_selected_submenu = SnoozeSelectedConfigMenu(tasklist,
                                                mainmenu, accelerator=False)

        self.find = wx.MenuItem(self, self.mainmenu.ID_FIND,
                                                        "&Find in database")
        self.edit = wx.MenuItem(self, self.mainmenu.ID_EDIT, "&Edit selected")
        self.snooze = wx.MenuItem(self, self.mainmenu.ID_SNOOZE,
                                        "&Snooze selected",
                                        subMenu=self.snooze_selected_submenu)
        self.dismiss = wx.MenuItem(self, self.mainmenu.ID_DISMISS,
                                                           "&Dismiss selected")

        self.find.SetBitmap(wxgui_api.get_menu_icon('@dbfind'))
        self.edit.SetBitmap(wxgui_api.get_menu_icon('@edit'))
        self.snooze.SetBitmap(wxgui_api.get_menu_icon('@snooze'))
        self.dismiss.SetBitmap(wxgui_api.get_menu_icon('@dismiss'))

        self.AppendItem(self.find)
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.snooze)
        self.AppendItem(self.dismiss)

    def update(self):
        sel = self.occview.listview.GetFirstSelected()

        self.find.Enable(False)
        self.edit.Enable(False)
        self.snooze.Enable(False)
        self.dismiss.Enable(False)

        while sel > -1:
            item = self.occview.occs[self.occview.listview.GetItemData(sel)]

            canbreak = 0

            # Check item is not a gap or an overlapping
            if item.get_filename() is not None:
                self.find.Enable()
                self.edit.Enable()
                canbreak += 1

            if item.get_alarm() is False:
                self.snooze.Enable()
                self.dismiss.Enable()
                canbreak += 1

            if canbreak > 1:
                break

            sel = self.occview.listview.GetNextSelected(sel)


class _SnoozeConfigMenu(wx.Menu):
    def __init__(self, mainmenu, ID_SNOOZE_FOR, ID_SNOOZE_FOR_N_index):
        wx.Menu.__init__(self)
        self.snoozetimes = {}

        for ID_SNOOZE_FOR_Ns, time, number, unit in mainmenu.snoozetimesconf:
            ID_SNOOZE_FOR_N = ID_SNOOZE_FOR_Ns[ID_SNOOZE_FOR_N_index]
            self.snoozetimes[time] = self.Append(ID_SNOOZE_FOR_N, "For " +
                                                      str(number) + ' ' + unit)
            wxgui_api.bind_to_menu(self._snooze_for_loop(time),
                                                        self.snoozetimes[time])

        self.AppendSeparator()
        self.snoozefor = self.Append(ID_SNOOZE_FOR, "&For...")

        wxgui_api.bind_to_menu(self.snooze_for_custom, self.snoozefor)

    def _snooze_for_loop(self, time):
        return lambda event: self.snooze_for(time)


class SnoozeSelectedConfigMenu(_SnoozeConfigMenu):
    def __init__(self, tasklist, mainmenu, accelerator=True):
        _SnoozeConfigMenu.__init__(self, mainmenu,
                                                mainmenu.ID_SNOOZE_FOR_SEL, 0)
        self.tasklist = tasklist
        config = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                    'GlobalShortcuts')('Items')
        accel = "\t{}".format(config['snooze_selected']) if accelerator else ""
        self.snoozefor.SetText(self.snoozefor.GetText() + accel)

    def snooze_for(self, time):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.list_.snooze_selected_alarms_for(time)

    def snooze_for_custom(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.list_.snooze_selected_alarms_for_custom()


class SnoozeAllConfigMenu(_SnoozeConfigMenu):
    def __init__(self, tasklist, mainmenu, accelerator=True):
        # Note that "all" means all the visible active alarms; some may be
        # hidden in the current view
        _SnoozeConfigMenu.__init__(self, mainmenu,
                                                mainmenu.ID_SNOOZE_FOR_ALL, 1)
        self.tasklist = tasklist
        config = coreaux_api.get_plugin_configuration('wxtasklist')(
                                                    'GlobalShortcuts')('Items')
        accel = "\t{}".format(config['snooze_all']) if accelerator else ""
        self.snoozefor.SetText(self.snoozefor.GetText() + accel)

    def snooze_for(self, time):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.list_.snooze_all_alarms_for(time)

    def snooze_for_custom(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.tasklist.list_.snooze_all_alarms_for_custom()
