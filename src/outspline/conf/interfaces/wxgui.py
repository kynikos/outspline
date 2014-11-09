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

from collections import OrderedDict as OD

data = (
    OD((
        ("enabled", "on"),
        ("initial_geometry", "900x700"),
        ("maximized", "no"),
        ("remember_geometry", "yes"),
        ("autohide_menubar", "no"),
        ("remember_session", "yes"),
        ("show_logs", "yes"),
        ("max_editor_tab_length", "20"),
        ("text_process_tab", "no"),
        ("text_min_upd_time", "2"),
        ("max_exceptions", "1"),
        ("plugin_focus_color", "system"),
        ("extended_shortcuts", "off"),
    )),
    OD((
        ("History", (
            OD((
                ("debug", "no"),
                ("color_done", "#FF7E00"),
                ("color_undone", "none"),
                ("color_saved", "#0F52BA"),
            )),
            OD()
        )),
        ("TreeIcons", (
            OD((
                ("symbol", "+"),
                ("color", "#0F52BA"),
            )),
            OD()
        )),
        ("SessionFiles", (OD(), OD())),
        ("Shortcuts", (
            # Shortcuts that can't/shouldn't be overridden in menus (list not
            #  exhaustive):
            # F1      help
            # Ctrl+F1
            # F7      hide caret in TextCtrl
            # F10     open main menu
            # Ctrl+Shift+F10
            # Ctrl++  zoom in
            # Ctrl+-  zoom out
            # Ctrl+/
            # Ctrl+PgUp
            # Ctrl+PgDn
            # Ctrl+Up
            # Ctrl+Down
            # Ctrl+Left
            # Ctrl+Right
            # Enter
            # Esc
            # +       stolen by DataViewCtrl
            # -       stolen by DataViewCtrl
            # /       stolen by DataViewCtrl
            # Ctrl+a  stolen by DataViewCtrl
            # Ctrl+Shift+a  stolen by DataViewCtrl
            # Ctrl+f  stolen by DataViewCtrl (if the first column is set with
            #         string items)
            # Ctrl+n  stolen by DataViewCtrl
            # Ctrl+p  stolen by DataViewCtrl

            # Shortcuts that should be still available (but double check):
            # Ctrl+b
            # Ctrl+d
            # Ctrl+Shift+e
            # Ctrl+g
            # Ctrl+Shift+g
            # Ctrl+h          May be used by the extended accelerators
            # Ctrl+Shift+h    May be used by the extended accelerators
            # Ctrl+j          May be used by the extended accelerators
            # Ctrl+Shift+j    May be used by the extended accelerators
            # Ctrl+k          May be used by the extended accelerators
            # Ctrl+Shift+k    May be used by the extended accelerators
            # Ctrl+l          May be used by the extended accelerators
            # Ctrl+Shift+l    May be used by the extended accelerators
            # Ctrl+m
            # Ctrl+Shift+m
            # Ctrl+Shift+o
            # Ctrl+Shift+r
            # Ctrl+t
            # Ctrl+Shift+t
            # Ctrl+u
            # Ctrl+Shift+F1
            # Ctrl+Shift+F2
            # Ctrl+F3
            # Ctrl+Shift+F3
            # Ctrl+Shift+F4
            # Ctrl+F5
            # Ctrl+Shift+F5
            # Ctrl+F6
            # Ctrl+Shift+F6
            # Ctrl+F7
            # Ctrl+Shift+F7
            # Ctrl+Shift+F8
            # Ctrl+Shift+F9
            # Ctrl+F10
            # Ctrl+Shift+F11
            # F12
            # Ctrl+F12
            # Ctrl+Shift+F12
            OD(),
            OD((
                ("File", (
                    OD((
                        ("new_database", "Ctrl+Shift+n"),
                        ("open_database", "Ctrl+o"),
                        ("save_database", "Ctrl+s"),
                        ("save_all_databases", "Ctrl+Shift+s"),
                        ("properties", ""),
                        ("close_database", "Ctrl+Shift+w"),
                        ("close_all_databases", ""),
                        ("exit", "Ctrl+q"),
                    )),
                    OD()
                )),
                ("Database", (
                    OD((
                        ("undo", "Ctrl+Shift+z"),
                        ("redo", "Ctrl+Shift+y"),
                        ("create_item", "Ctrl+i"),
                        ("create_child", "Ctrl+Shift+i"),
                        ("move_up", "Ctrl+Shift+u"),
                        ("move_down", "Ctrl+Shift+d"),
                        ("move_to_parent", "Ctrl+Shift+p"),
                        ("edit", "Ctrl+e"),
                        ("delete", "Ctrl+Delete"),
                    )),
                    OD()
                )),
                ("Edit", (
                    OD((
                        ("select_all", "Ctrl+a"),
                        ("cut", "Ctrl+x"),
                        ("copy", "Ctrl+c"),
                        ("paste", "Ctrl+v"),
                        ("find", "Ctrl+Shift+f"),
                        ("apply", "Ctrl+Enter"),
                        ("apply_all", "Ctrl+Shift+Enter"),
                    )),
                    OD()
                )),
                ("View", (
                    OD(),
                    OD((
                        ("Databases", (
                            OD((
                                ("cycle", "F3"),
                                ("cycle_reverse", "F2"),
                                ("focus", "Ctrl+F2"),
                                ("focus_1", "Ctrl+1"),
                                ("focus_2", "Ctrl+2"),
                                ("focus_3", "Ctrl+3"),
                                ("focus_4", "Ctrl+4"),
                                ("focus_5", ""),
                                ("focus_6", ""),
                                ("focus_7", ""),
                                ("focus_8", ""),
                                ("focus_9", ""),
                                ("focus_last", "Ctrl+5"),
                            )),
                            OD()
                        )),
                        ("Logs", (
                            OD((
                                ("show", "Ctrl+F9"),
                                ("cycle", "F9"),
                                ("cycle_reverse", "F8"),
                                ("focus", "Ctrl+F8"),
                            )),
                            OD((
                                ("Items", (
                                    OD((
                                        ("select", ""),
                                    )),
                                    OD()
                                )),
                            ))
                        )),
                        ("RightNotebook", (
                            OD((
                                ("cycle", "F5"),
                                ("cycle_reverse", "F4"),
                                ("focus", "Ctrl+F4"),
                                ("focus_1", "Ctrl+6"),
                                ("focus_2", "Ctrl+7"),
                                ("focus_3", "Ctrl+8"),
                                ("focus_4", "Ctrl+9"),
                                ("focus_5", ""),
                                ("focus_6", ""),
                                ("focus_7", ""),
                                ("focus_8", ""),
                                ("focus_9", ""),
                                ("focus_last", "Ctrl+0"),
                                ("close", "Ctrl+w"),
                            )),
                            OD()
                        )),
                        ("Editors", (
                            OD((
                                ("focus_text_area", "F6"),
                            )),
                            OD()
                        )),
                    ))
                )),
            ))
        )),
        ("ExtendedShortcuts", (
            OD((
                ("up", "k"),
                ("down", "j"),
                ("left", "h"),
                ("right", "l"),
                ("focus_database", ","),
                ("focus_rightnb", "."),
                ("focus_logs", "'"),
            )),
            OD((
                ("LeftNotebook", (
                    OD((
                        ("cycle", "Ctrl+l"),
                        ("cycle_reverse", "Ctrl+h"),
                        ("focus_first", "Ctrl+Shift+h"),
                        ("focus_last", "Ctrl+Shift+l"),
                        ("show_logs", "Shift+'"),
                        ("save", "s"),
                        ("save_all", "Shift+s"),
                        ("close", "w"),
                        ("close_all", "Shift+w"),
                    )),
                    OD((
                        ("Database", (
                            OD((
                                ("expand", "l"),
                                ("collapse", "h"),
                                ("select", "a"),
                                ("unselect", "Shift+a"),
                                ("undo", "u"),
                                ("redo", "r"),
                                ("create_sibling", "i"),
                                ("create_child", "Shift+i"),
                                ("move_up", "m"),
                                ("move_down", "n"),
                                ("move_to_parent", "p"),
                                ("edit", "e"),
                                ("delete", "d"),
                            )),
                            OD()
                        )),
                        ("Logs", (
                            OD((
                                ("cycle", "Ctrl+j"),
                                ("cycle_reverse", "Ctrl+k"),
                            )),
                            OD((
                                ("History", (
                                    OD((
                                        ("undo", "u"),
                                        ("redo", "r"),
                                    )),
                                    OD()
                                )),
                            ))
                        )),
                    ))
                )),
                ("RightNotebook", (
                    OD((
                        ("cycle", "Ctrl+l"),
                        ("cycle_reverse", "Ctrl+h"),
                        ("focus_first", "Ctrl+Shift+h"),
                        ("focus_last", "Ctrl+Shift+l"),
                        ("close", "w"),
                    )),
                    OD((
                        ("Editor", (
                            OD((
                                ("apply", "a"),
                                ("find", "f"),
                                ("focus_text", "t"),
                            )),
                            OD()
                        )),
                    ))
                )),
            ))
        )),
    ))
)

