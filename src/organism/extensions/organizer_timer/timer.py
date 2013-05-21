# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.


class NextOccurrences():
    def __init__(self):
        self.occs = {}
        self.next = None

    def add(self, last_search, occ):
        filename = occ['filename']
        id_ = occ['id_']

        if self.next and self.next in (occ['alarm'], occ['start'], occ['end']):
            try:
                self.occs[filename][id_]
            except KeyError:
                try:
                    self.occs[filename]
                except KeyError:
                    self.occs[filename] = {}
                self.occs[filename][id_] = []
            self.occs[filename][id_].append(occ)
            return True
        else:
            return self._update_next(last_search, occ)

    def _update_next(self, last_search, occ):
        tl = [occ['start'], occ['end'], occ['alarm']]
        # When sorting, None values are put first
        tl.sort()

        for t in tl:
            # Note that "last_search < t" is always False if t is None
            if last_search < t and (not self.next or t < self.next):
                self.next = t
                self.occs = {occ['filename']: {occ['id_']: [occ]}}
                return True
        else:
            return False

    def except_(self, filename, id_, start, end, inclusive):
        # Test if the item has some rules, for safety, also for coherence with
        # organizer.items.OccurrencesRange.except_
        try:
            occsc = self.occs[filename][id_][:]
        except KeyError:
            pass
        else:
            for occ in occsc:
                if start <= occ['start'] <= end or (inclusive and
                                           occ['start'] <= start <= occ['end']):
                    self.occs[filename][id_].remove(occ)
        # Do not reset self.next to None in case there are no occurrences left:
        # this lets restart_timer, and consequently search_alarms, ignore the
        # excepted alarms at the following search

    def try_delete_one(self, filename, id_, start, end, alarm):
        try:
            occsc = self.occs[filename][id_][:]
        except KeyError:
            return False
        else:
            for occd in occsc:
                if (start, end, alarm) == (occd['start'], occd['end'],
                                                                 occd['alarm']):
                    self.occs[filename][id_].remove(occd)
                    if not self.occs[filename][id_]:
                        del self.occs[filename][id_]
                    if not self.occs[filename]:
                        del self.occs[filename]
                    # Delete only one occurrence, hence the name try_delete_one
                    return True

    def get_dict(self):
        return self.occs

    def get_next_alarm(self):
        return self.next

    def get_time_span(self):
        minstart = None
        maxend = None
        for filename in self.occs:
            for id_ in self.occs[filename]:
                for occ in self.occs[filename][id_]:
                    # This assumes that start <= end
                    if minstart is None or occ['start'] < minstart:
                        minstart = occ['start']
                    if maxend is None or occ['end'] > maxend:
                        maxend = occ['end']
        return (minstart, maxend)
