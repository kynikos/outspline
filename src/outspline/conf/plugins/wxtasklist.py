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

from collections import OrderedDict as OD

data = (
    OD((
        ("enabled", "on"),
        ("debug_mode", "off"),
        ("refresh_delay", "25"),
        ("maximum_items", "300"),
        ("first_weekday", "0"),
        ("show_navigator", "yes"),
        ("navigator_buttons", "previous,next,reset,set,apply"),
        ("active_alarms", "auto"),
        ("show_gaps", "no"),
        ("show_overlappings", "no"),
        ("autoscroll", "on"),
        ("autoscroll_padding", "0"),
        ("snooze_times", "5 60 1440"),
    )),
    OD((
        ("ColumnWidths", (
            OD((
                ("database", "100"),
                ("heading", "300"),
                ("start", "160"),
                ("duration", "100"),
                ("end", "160"),
                ("state", "80"),
                ("alarm", "160"),
            )),
            OD()
        )),
        ("Formats", (
            OD((
                ("database", "short"),
                ("start", "%H:%M %a %d %b %Y"),
                ("duration", "expanded"),
                ("end", "start"),
                ("alarm", "start"),
            )),
            OD()
        )),
        ("Colors", (
            OD((
                ("past", "auto"),
                ("ongoing", "#0F52BA"),
                ("future", "system"),
                ("active", "#FF7E00"),
                ("gap", "#228B22"),
                ("overlapping", "#ED1C24"),
            )),
            OD()
        )),
        ("DefaultFilter", (
            OD((
                ("mode", "relative"),
                ("low", "-5"),
                ("high", "1439"),
                ("type", "to"),
                ("unit", "minutes"),
            )),
            OD()
        )),
        ("GlobalShortcuts", (
            OD((
                ("scroll_to_ongoing", "Ctrl+;"),
            )),
            OD((
                ("Items", (
                    OD((
                        ("find_selected", "Ctrl+'"),
                        ("edit_selected", ""),
                        ("snooze_selected", "Ctrl+["),
                        ("snooze_all", "Ctrl+{"),
                        ("dismiss_selected", "Ctrl+]"),
                        ("dismiss_all", "Ctrl+}"),
                    )),
                    OD()
                )),
                ("Navigator", (
                    OD((
                        ("previous", "Ctrl+,"),
                        ("next", "Ctrl+."),
                        ("apply", ""),
                        ("set", ""),
                        ("reset", "Ctrl+r"),
                    )),
                    OD()
                )),
                ("View", (
                    OD((
                        ("show", "Ctrl+F11"),
                        ("focus", ""),
                        ("show_navigator", "F11"),
                        ("toggle_gaps", "Ctrl+<"),
                        ("toggle_overlappings", "Ctrl+>"),
                    )),
                    OD()
                )),
            ))
        )),
        ("ContextualShortcuts", (
            OD((
                ("prev_page", "Shift+h"),
                ("next_page", "Shift+l"),
                ("apply", "a"),
                ("set", "Shift+a"),
                ("reset", "r"),
                ("autoscroll", "u"),
                ("toggle_autoscroll", "Shift+u"),
                ("find", "f"),
                ("edit", "e"),
                ("snooze", "s"),
                ("snooze_all", "Shift+s"),
                ("dismiss", "d"),
                ("dismiss_all", "Shift+d"),
                ("toggle_navigator", "n"),
                ("toggle_gaps", "g"),
                ("toggle_overlappings", "o"),
            )),
            OD()
        )),
    ))
)
