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

import csv
import json
import xml.dom.minidom as dom
import errno
import wx

import outspline.coreaux_api as coreaux_api

import msgboxes


class Exporter(object):
    def __init__(self, occview):
        self.occview = occview
        self.config = coreaux_api.get_plugin_configuration('wxtasklist')

    def export_to_json(self):
        # Preserve the current sort order
        obj = [self.occview.get_item_values_by_position(i) \
                        for i in xrange(self.occview.get_shown_items_count())]

        with self._open_file(msgboxes.save_to_json(), 'w') as file_:
            json.dump(obj, file_, indent=4)

    def export_to_tsv(self):
        with self._open_file(msgboxes.save_to_tsv(), 'wb') as file_:
            writer = csv.DictWriter(file_, ("filename", "heading", "start",
                                        "end", "alarm"), dialect='excel-tab')
            writer.writeheader()

            # Preserve the current sort order
            for i in xrange(self.occview.get_shown_items_count()):
                obj = self.occview.get_item_values_by_position(i)
                writer.writerow(obj)

    def export_to_xml(self):
        impl = dom.getDOMImplementation()
        doc = impl.createDocument(None, "view", None)
        root = doc.documentElement

        # Preserve the current sort order
        for i in xrange(self.occview.get_shown_items_count()):
            event = doc.createElement('event')
            obj = self.occview.get_item_values_by_position(i)

            for key in obj:
                keyel = doc.createElement(key)
                text = doc.createTextNode(str(obj[key]))
                keyel.appendChild(text)
                event.appendChild(keyel)

            root.appendChild(event)

        with self._open_file(msgboxes.save_to_xml(), 'w') as file_:
            doc.writexml(file_, addindent="    ", newl="\n")

    def _open_file(self, dialog, mode):
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()

            try:
                file_ = open(filename, mode)
            except IOError as err:
                if err.errno in (errno.EACCES, errno.ENOENT):
                    msgboxes.warn_user_rights(filename).ShowModal()
                else:
                    raise
            else:
                return file_
