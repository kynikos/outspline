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

import wx

from outspline.static.wxclasses.time import TimeSpanCtrl
from outspline.static.wxclasses.misc import NarrowSpinCtrl

import outspline.coreaux_api as coreaux_api
import outspline.core_api as core_api
import outspline.interfaces.wxgui_api as wxgui_api
import outspline.extensions.organism_alarms_api as organism_alarms_api

import list as list_
import filters as filters_


class MainMenu(wx.Menu):
    tasklist = None
    occview = None
    ID_SHOW = None
    show = None
    filters = None
    ID_FILTERS = None
    filters_submenu = None
    addfilter = None
    ID_ADD_FILTER = None
    editfilter = None
    ID_EDIT_FILTER = None
    removefilter = None
    ID_REMOVE_FILTER = None
    gaps = None
    ID_GAPS = None
    overlaps = None
    ID_OVERLAPS = None
    scroll = None
    ID_SCROLL = None
    autoscroll = None
    ID_AUTOSCROLL = None
    find = None
    ID_FIND = None
    edit = None
    ID_EDIT = None
    snooze = None
    ID_SNOOZE = None
    snooze_all = None
    ID_SNOOZE_ALL = None
    dismiss = None
    ID_DISMISS = None
    dismiss_all = None
    ID_DISMISS_ALL = None

    def __init__(self, tasklist):
        wx.Menu.__init__(self)

        self.tasklist = tasklist
        self.occview = tasklist.list_

        self.ID_SHOW = wx.NewId()
        self.ID_FILTERS = wx.NewId()
        self.ID_ADD_FILTER = wx.NewId()
        self.ID_EDIT_FILTER = wx.NewId()
        self.ID_REMOVE_FILTER = wx.NewId()
        self.ID_GAPS = wx.NewId()
        self.ID_OVERLAPS = wx.NewId()
        self.ID_SCROLL = wx.NewId()
        self.ID_AUTOSCROLL = wx.NewId()
        self.ID_FIND = wx.NewId()
        self.ID_EDIT = wx.NewId()
        self.ID_SNOOZE = wx.NewId()
        self.ID_SNOOZE_ALL = wx.NewId()
        self.ID_DISMISS = wx.NewId()
        self.ID_DISMISS_ALL = wx.NewId()

        self.show = wx.MenuItem(self, self.ID_SHOW,
                                                "Show &panel\tCTRL+SHIFT+F5",
                                                "Show the occurrences panel",
                                                kind=wx.ITEM_CHECK)

        self.filters_submenu = FiltersMenu(self.tasklist)

        self.filters = wx.MenuItem(self, self.ID_FILTERS, 'F&ilters',
                            'Select a filter', subMenu=self.filters_submenu)
        self.addfilter = wx.MenuItem(self, self.ID_ADD_FILTER,
                                            "&Add filter", "Add a new filter")
        self.editfilter = wx.MenuItem(self, self.ID_EDIT_FILTER,
                        "Edi&t filter", "Edit the currently selected filter")
        self.removefilter = wx.MenuItem(self, self.ID_REMOVE_FILTER,
                    "&Remove filter", "Remove the currently selected filter")
        self.gaps = wx.MenuItem(self, self.ID_GAPS, "Show &gaps\tCTRL+-",
                            "Show any unallocated time in the shown interval",
                            kind=wx.ITEM_CHECK)
        self.overlaps = wx.MenuItem(self, self.ID_OVERLAPS,
                        "Show &overlappings\tCTRL+=",
                        "Show time intervals used by more than one occurrence",
                        kind=wx.ITEM_CHECK)
        self.scroll = wx.MenuItem(self, self.ID_SCROLL,
                                        "Scro&ll to ongoing\tF5",
                                        "Order the list by State and scroll "
                                        "to the first ongoing occurrence")
        self.autoscroll = wx.MenuItem(self, self.ID_AUTOSCROLL,
                                            "Enable a&uto-scroll",
                                            "Auto-scroll to the first ongoing "
                                            "occurrence at pre-defined events",
                                            kind=wx.ITEM_CHECK)
        self.find = wx.MenuItem(self, self.ID_FIND, "&Find in database\tF6",
            "Select the database items associated to the selected occurrences")
        self.edit = wx.MenuItem(self, self.ID_EDIT, "&Edit selected\tCTRL+F6",
                            "Open in the editor the database items associated "
                            "to the selected occurrences")

        self.snooze = wx.MenuItem(self, self.ID_SNOOZE, "&Snooze selected",
                            "Snooze the selected alarms",
                            subMenu=SnoozeSelectedConfigMenu(self.tasklist))
        self.snooze_all = wx.MenuItem(self, self.ID_SNOOZE_ALL,
                                "S&nooze all", "Snooze all the active alarms",
                                subMenu=SnoozeAllConfigMenu(self.tasklist))

        self.dismiss = wx.MenuItem(self, self.ID_DISMISS,
                        "&Dismiss selected\tF8", "Dismiss the selected alarms")
        self.dismiss_all = wx.MenuItem(self, self.ID_DISMISS_ALL,
                    "Dis&miss all\tCTRL+F8", "Dismiss all the active alarms")

        self.filters.SetBitmap(wx.ArtProvider.GetBitmap('@filters',
                                                                  wx.ART_MENU))
        self.addfilter.SetBitmap(wx.ArtProvider.GetBitmap('@add-filter',
                                                                  wx.ART_MENU))
        self.editfilter.SetBitmap(wx.ArtProvider.GetBitmap('@edit-filter',
                                                                  wx.ART_MENU))
        self.removefilter.SetBitmap(wx.ArtProvider.GetBitmap('@remove-filter',
                                                                  wx.ART_MENU))
        self.scroll.SetBitmap(wx.ArtProvider.GetBitmap('@movedown',
                                                                wx.ART_MENU))
        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        self.edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))
        self.snooze.SetBitmap(wx.ArtProvider.GetBitmap('@alarms', wx.ART_MENU))
        self.snooze_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarms',
                                                                  wx.ART_MENU))
        self.dismiss.SetBitmap(wx.ArtProvider.GetBitmap('@alarmoff',
                                                                  wx.ART_MENU))
        self.dismiss_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarmoff',
                                                                  wx.ART_MENU))

        self.AppendItem(self.show)
        self.AppendItem(self.filters)
        self.AppendSeparator()
        self.AppendItem(self.addfilter)
        self.AppendItem(self.editfilter)
        self.AppendItem(self.removefilter)
        self.AppendSeparator()
        self.AppendItem(self.gaps)
        self.AppendItem(self.overlaps)
        self.AppendSeparator()
        self.AppendItem(self.scroll)
        self.AppendItem(self.autoscroll)
        self.AppendSeparator()
        self.AppendItem(self.find)
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.snooze)
        self.AppendItem(self.snooze_all)
        self.AppendItem(self.dismiss)
        self.AppendItem(self.dismiss_all)

        wxgui_api.bind_to_menu(self.tasklist.toggle_shown, self.show)
        wxgui_api.bind_to_menu(self.add_filter, self.addfilter)
        wxgui_api.bind_to_menu(self.edit_filter, self.editfilter)
        wxgui_api.bind_to_menu(self.remove_filter, self.removefilter)
        wxgui_api.bind_to_menu(self.show_gaps, self.gaps)
        wxgui_api.bind_to_menu(self.show_overlappings, self.overlaps)
        wxgui_api.bind_to_menu(self.scroll_to_ongoing, self.scroll)
        wxgui_api.bind_to_menu(self.enable_autoscroll, self.autoscroll)
        wxgui_api.bind_to_menu(self.find_in_tree, self.find)
        wxgui_api.bind_to_menu(self.edit_items, self.edit)
        wxgui_api.bind_to_menu(self.dismiss_selected_alarms, self.dismiss)
        wxgui_api.bind_to_menu(self.dismiss_all_alarms, self.dismiss_all)

        wxgui_api.bind_to_update_menu_items(self.update_items)
        wxgui_api.bind_to_reset_menu_items(self.reset_items)

        wxgui_api.insert_menu_main_item('&Occurrences',
                                    wxgui_api.get_menu_logs_position(), self)

    def update_items(self, kwargs):
        if kwargs['menu'] is self:
            self.show.Check(check=self.tasklist.is_shown())
            self.filters.Enable(False)
            self.addfilter.Enable(False)
            self.editfilter.Enable(False)
            self.removefilter.Enable(False)
            self.gaps.Enable(False)
            self.gaps.Check(check=self.occview.show_gaps)
            self.overlaps.Enable(False)
            self.overlaps.Check(check=self.occview.show_overlappings)
            self.scroll.Enable(False)
            self.autoscroll.Enable(False)
            self.autoscroll.Check(check=self.occview.autoscroll.is_enabled())
            self.find.Enable(False)
            self.edit.Enable(False)
            self.snooze.Enable(False)
            self.snooze_all.Enable(False)
            self.dismiss.Enable(False)
            self.dismiss_all.Enable(False)

            tab = wxgui_api.get_selected_right_nb_tab()

            if tab is self.tasklist.panel:
                self.filters.Enable()
                self.addfilter.Enable()
                self.editfilter.Enable()
                self.scroll.Enable()

                if len(self.filters.GetSubMenu().GetMenuItems()) > 1:
                    self.removefilter.Enable()

                sel = self.occview.listview.GetFirstSelected()

                while sel > -1:
                    item = self.occview.occs[
                                    self.occview.listview.GetItemData(sel)]

                    canbreak = 0

                    # Check item is not a gap or an overlapping
                    if item.filename is not None:
                        self.find.Enable()
                        self.edit.Enable()
                        canbreak += 1

                    if item.alarm is False:
                        self.snooze.Enable()
                        self.dismiss.Enable()
                        canbreak += 1

                    if canbreak > 1:
                        break

                    sel = self.occview.listview.GetNextSelected(sel)

                # Note that "all" means all the visible active alarms; some
                # may be hidden in the current view; this is also why these
                # actions must be disabled if the tasklist is not focused
                if len(self.occview.activealarms) > 0:
                    self.snooze_all.Enable()
                    self.dismiss_all.Enable()

                self.filters_submenu.update()

            if self.tasklist.is_shown():
                # Already appropriately checked above
                self.gaps.Enable()
                self.overlaps.Enable()
                self.autoscroll.Enable()

    def reset_items(self, kwargs):
        # Re-enable all the actions so they are available for their
        # accelerators
        self.show.Enable()
        self.filters.Enable()
        self.addfilter.Enable()
        self.editfilter.Enable()
        self.removefilter.Enable()
        self.gaps.Enable()
        self.overlaps.Enable()
        self.scroll.Enable()
        self.autoscroll.Enable()
        self.find.Enable()
        self.edit.Enable()
        self.snooze.Enable()
        self.snooze_all.Enable()
        self.dismiss.Enable()
        self.dismiss_all.Enable()

    def add_filter(self, event):
        self.tasklist.filters.create()

    def edit_filter(self, event):
        self.tasklist.filters.edit_selected()

    def remove_filter(self, event):
        self.tasklist.filters.remove_selected()

    def show_gaps(self, event):
        if self.tasklist.is_shown():
            self.occview.show_gaps = not self.occview.show_gaps
            self.occview.delay_restart()

    def show_overlappings(self, event):
        if self.tasklist.is_shown():
            self.occview.show_overlappings = not self.occview.show_overlappings
            self.occview.delay_restart()

    def scroll_to_ongoing(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            self.occview.autoscroll.execute_force()

    def enable_autoscroll(self, event):
        if self.occview.autoscroll.is_enabled():
            self.occview.autoscroll.disable()
        else:
            self.occview.autoscroll.enable()

    def find_in_tree(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            sel = self.occview.listview.GetFirstSelected()

            if sel > -1:
                for filename in core_api.get_open_databases():
                    wxgui_api.unselect_all_items(filename)

                # Loop that selects a database tab (but doesn't select items)
                while sel > -1:
                    item = self.occview.occs[self.occview.listview.GetItemData(
                                                                        sel)]

                    if item.filename is not None:
                        wxgui_api.select_database_tab(item.filename)
                        # The item is selected in the loop below
                        break
                    else:
                        sel = self.occview.listview.GetNextSelected(sel)

                # Loop that doesn't select a database tab but selects items,
                # including the one found in the loop above
                while sel > -1:
                    item = self.occview.occs[self.occview.listview.GetItemData(
                                                                        sel)]

                    if item.filename is not None:
                        wxgui_api.add_item_to_selection(item.filename,
                                                                    item.id_)

                    sel = self.occview.listview.GetNextSelected(sel)

    def edit_items(self, event):
        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            sel = self.occview.listview.GetFirstSelected()

            while sel > -1:
                item = self.occview.occs[self.occview.listview.GetItemData(
                                                                        sel)]

                if item.filename is not None:
                    wxgui_api.open_editor(item.filename, item.id_)

                sel = self.occview.listview.GetNextSelected(sel)

    def dismiss_selected_alarms(self, event):
        core_api.block_databases()

        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            alarmsd = self.occview.get_selected_active_alarms()

            if len(alarmsd) > 0:
                organism_alarms_api.dismiss_alarms(alarmsd)
                # Let the alarm off event update the tasklist

        core_api.release_databases()

    def dismiss_all_alarms(self, event):
        # Note that "all" means all the visible active alarms; some may be
        # hidden in the current view
        core_api.block_databases()

        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            alarmsd = self.occview.activealarms

            if len(alarmsd) > 0:
                organism_alarms_api.dismiss_alarms(alarmsd)
                # Let the alarm off event update the tasklist

        core_api.release_databases()


class TabContextMenu(wx.Menu):
    tasklist = None
    filters = None
    filters_submenu = None
    addfilter = None
    editfilter = None
    removefilter = None
    gaps = None
    overlaps = None
    scroll = None
    autoscroll = None
    snooze_all = None
    dismiss_all = None

    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.filters_submenu = FiltersMenu(self.tasklist)

        self.filters = wx.MenuItem(self, self.tasklist.mainmenu.ID_FILTERS,
                                    'F&ilters', subMenu=self.filters_submenu)
        self.addfilter = wx.MenuItem(self,
                        self.tasklist.mainmenu.ID_ADD_FILTER, "&Add filter")
        self.editfilter = wx.MenuItem(self,
                        self.tasklist.mainmenu.ID_EDIT_FILTER, "Edi&t filter")
        self.removefilter = wx.MenuItem(self,
                    self.tasklist.mainmenu.ID_REMOVE_FILTER, "&Remove filter")
        self.gaps = wx.MenuItem(self, self.tasklist.mainmenu.ID_GAPS,
                                            "Show &gaps", kind=wx.ITEM_CHECK)
        self.overlaps = wx.MenuItem(self,
                    self.tasklist.mainmenu.ID_OVERLAPS, "Show &overlappings",
                    kind=wx.ITEM_CHECK)
        self.scroll = wx.MenuItem(self,
                    self.tasklist.mainmenu.ID_SCROLL, "Scro&ll to ongoing")
        self.autoscroll = wx.MenuItem(self,
                                        self.tasklist.mainmenu.ID_AUTOSCROLL,
                                        "Enable a&uto-scroll",
                                        kind=wx.ITEM_CHECK)
        self.snooze_all = wx.MenuItem(self,
                        self.tasklist.mainmenu.ID_SNOOZE_ALL, "S&nooze all",
                        subMenu=SnoozeAllConfigMenu(self.tasklist))
        self.dismiss_all = wx.MenuItem(self,
                        self.tasklist.mainmenu.ID_DISMISS_ALL, "Dis&miss all")

        self.filters.SetBitmap(wx.ArtProvider.GetBitmap('@filters',
                                                                  wx.ART_MENU))
        self.addfilter.SetBitmap(wx.ArtProvider.GetBitmap('@add-filter',
                                                                  wx.ART_MENU))
        self.editfilter.SetBitmap(wx.ArtProvider.GetBitmap('@edit-filter',
                                                                  wx.ART_MENU))
        self.removefilter.SetBitmap(wx.ArtProvider.GetBitmap('@remove-filter',
                                                                  wx.ART_MENU))
        self.scroll.SetBitmap(wx.ArtProvider.GetBitmap('@movedown',
                                                                wx.ART_MENU))
        self.snooze_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarms',
                                                                  wx.ART_MENU))
        self.dismiss_all.SetBitmap(wx.ArtProvider.GetBitmap('@alarmoff',
                                                                  wx.ART_MENU))

        self.AppendItem(self.filters)
        self.AppendSeparator()
        self.AppendItem(self.addfilter)
        self.AppendItem(self.editfilter)
        self.AppendItem(self.removefilter)
        self.AppendSeparator()
        self.AppendItem(self.scroll)
        self.AppendItem(self.autoscroll)
        self.AppendSeparator()
        self.AppendItem(self.gaps)
        self.AppendItem(self.overlaps)
        self.AppendSeparator()
        self.AppendItem(self.snooze_all)
        self.AppendItem(self.dismiss_all)

    def update(self):
        if len(self.tasklist.list_.activealarms) > 0:
            self.snooze_all.Enable()
            self.dismiss_all.Enable()
        else:
            self.snooze_all.Enable(False)
            self.dismiss_all.Enable(False)

        self.filters_submenu.update()

        self.gaps.Check(check=self.tasklist.list_.show_gaps)
        self.overlaps.Check(check=self.tasklist.list_.show_overlappings)
        self.autoscroll.Check(
                            check=self.tasklist.list_.autoscroll.is_enabled())


class ListContextMenu(wx.Menu):
    tasklist = None
    occview = None
    mainmenu = None
    find = None
    edit = None
    snooze = None
    dismiss = None

    def __init__(self, tasklist, mainmenu):
        wx.Menu.__init__(self)
        self.tasklist = tasklist
        self.occview = tasklist.list_
        self.mainmenu = mainmenu

        self.find = wx.MenuItem(self, self.mainmenu.ID_FIND,
                                                        "&Find in database")
        self.edit = wx.MenuItem(self, self.mainmenu.ID_EDIT, "&Edit selected")
        self.snooze = wx.MenuItem(self, self.mainmenu.ID_SNOOZE,
                                            "&Snooze selected",
                                            subMenu=SnoozeSelectedConfigMenu(
                                            self.tasklist, accelerator=False))
        self.dismiss = wx.MenuItem(self, self.mainmenu.ID_DISMISS,
                                                           "&Dismiss selected")

        self.find.SetBitmap(wx.ArtProvider.GetBitmap('@find', wx.ART_MENU))
        self.edit.SetBitmap(wx.ArtProvider.GetBitmap('@edit', wx.ART_MENU))
        self.snooze.SetBitmap(wx.ArtProvider.GetBitmap('@alarms', wx.ART_MENU))
        self.dismiss.SetBitmap(wx.ArtProvider.GetBitmap('@alarmoff',
                                                                  wx.ART_MENU))

        self.AppendItem(self.find)
        self.AppendItem(self.edit)
        self.AppendSeparator()
        self.AppendItem(self.snooze)
        self.AppendItem(self.dismiss)

    def update(self):
        self.find.Enable(False)
        self.edit.Enable(False)
        self.snooze.Enable(False)
        self.dismiss.Enable(False)

        sel = self.occview.listview.GetFirstSelected()

        while sel > -1:
            item = self.occview.occs[self.occview.listview.GetItemData(sel)]

            canbreak = 0

            # Check item is not a gap or an overlapping
            if item.filename is not None:
                self.find.Enable()
                self.edit.Enable()
                canbreak += 1

            if item.alarm is False:
                self.snooze.Enable()
                self.dismiss.Enable()
                canbreak += 1

            if canbreak > 1:
                break

            sel = self.occview.listview.GetNextSelected(sel)


class FiltersMenu(wx.Menu):
    tasklist = None
    namestoids = None

    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist

        self.update()

    def update(self):
        self.namestoids = {}

        for item in self.GetMenuItems():
            self.DeleteItem(item)

        filters = self.tasklist.filters.get_filters_sorted()

        for filter_ in filters:
            config = self.tasklist.filters.get_filter_configuration(filter_)

            id_ = wx.NewId()
            self.namestoids[filter_] = id_

            item = wx.MenuItem(self, id_, config['name'], kind=wx.ITEM_RADIO)
            self.AppendItem(item)

            wxgui_api.bind_to_menu(self.select_filter_loop(filter_, config),
                                                                        item)

        # This submenu is created both under the main menu and the tab context
        # menu, so update the checked item
        selfilter = self.tasklist.filters.get_selected_filter()
        self.Check(self.namestoids[selfilter], check=True)

    def select_filter_loop(self, filter_, config):
        return lambda event: self.tasklist.filters.select_filter(filter_,
                                                                        config)


class _SnoozeConfigMenu(wx.Menu):
    tasklist = None
    snoozetimes = None
    snoozefor = None

    def __init__(self, tasklist):
        wx.Menu.__init__(self)
        self.tasklist = tasklist
        self.snoozetimes = {}

        # Using a set here to remove any duplicates would lose the order of
        # the times
        snooze_times = coreaux_api.get_plugin_configuration('wxtasklist')[
                                                     'snooze_times'].split(' ')

        for stime in snooze_times:
            time = int(stime) * 60
            number, unit = TimeSpanCtrl._compute_widget_values(time)
            # Duplicate time values are not supported, just make sure they
            # don't crash the application
            self.snoozetimes[time] = self.Append(wx.NewId(), "For " +
                                                      str(number) + ' ' + unit)
            wxgui_api.bind_to_menu(self.snooze_for_loop(time),
                                                        self.snoozetimes[time])

        self.AppendSeparator()
        self.snoozefor = self.Append(wx.NewId(), "For...")

        wxgui_api.bind_to_menu(self.snooze_for_custom, self.snoozefor)

    def snooze_for_loop(self, time):
        return lambda event: self.snooze_for(time)

    def snooze_for(self, time):
        core_api.block_databases()

        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            alarmsd = self.get_alarms()

            if len(alarmsd) > 0:
                organism_alarms_api.snooze_alarms(alarmsd, time)
                # Let the alarm off event update the tasklist

        core_api.release_databases()

    def snooze_for_custom(self, event):
        core_api.block_databases()

        tab = wxgui_api.get_selected_right_nb_tab()

        if tab is self.tasklist.panel:
            alarmsd = self.get_alarms()

            if len(alarmsd) > 0:
                dlg = SnoozeDialog()

                if dlg.ShowModal() == wx.ID_OK:
                    organism_alarms_api.snooze_alarms(alarmsd, dlg.get_time())
                    # Let the alarm off event update the tasklist

        core_api.release_databases()


class SnoozeDialog(wx.Dialog):
    number = None
    unit = None

    def __init__(self):
        wx.Dialog.__init__(self, parent=wxgui_api.get_main_frame(),
                                                title="Snooze configuration")

        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap(
                                        'appointment-soon', wx.ART_CMN_DIALOG))
        hsizer.Add(icon, flag=wx.ALIGN_TOP | wx.RIGHT, border=12)

        ssizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, label='Snooze for:')
        ssizer.Add(label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=4)

        self.number = NarrowSpinCtrl(self, min=1, max=999,
                                                        style=wx.SP_ARROW_KEYS)
        self.number.SetValue(5)
        ssizer.Add(self.number, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                                                    border=4)

        self.unit = wx.ComboBox(self, value='minutes',
                                choices=('minutes', 'hours', 'days', 'weeks'),
                                style=wx.CB_READONLY)
        ssizer.Add(self.unit, flag=wx.ALIGN_CENTER_VERTICAL)

        hsizer.Add(ssizer, flag=wx.ALIGN_TOP)

        vsizer.Add(hsizer, flag=wx.ALIGN_CENTER | wx.ALL, border=12)

        buttons = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        vsizer.Add(buttons,
                        flag=wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                        border=12)

        self.Fit()

    def get_time(self):
        mult = {'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800}
        return self.number.GetValue() * mult[self.unit.GetValue()]


class SnoozeSelectedConfigMenu(_SnoozeConfigMenu):
    def __init__(self, tasklist, accelerator=True):
        _SnoozeConfigMenu.__init__(self, tasklist)
        accel = "\tF7" if accelerator else ""
        self.snoozefor.SetText(self.snoozefor.GetText() + accel)

    def get_alarms(self):
        return self.tasklist.list_.get_selected_active_alarms()


class SnoozeAllConfigMenu(_SnoozeConfigMenu):
    def __init__(self, tasklist, accelerator=True):
        _SnoozeConfigMenu.__init__(self, tasklist)
        accel = "\tCTRL+F7" if accelerator else ""
        self.snoozefor.SetText(self.snoozefor.GetText() + accel)

    def get_alarms(self):
        # Note that "all" means all the visible active alarms; some may be
        # hidden in the current view
        return self.tasklist.list_.activealarms


