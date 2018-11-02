#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Derrick Moser <derrick_moser@yahoo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

class PriorityQueue:
    def __init__(self):
        self._items = [ None ]
        self._lookup = {}

    def __repr__(self):
        return '<pq data=%s/>' % (repr(self._items[1:]), )

    def size(self):
        return len(self._items) - 1

    def empty(self):
        return len(self._items) == 1

    def clear(self):
        del self._items[1:]
        self._lookup.clear()

    def max_priority(self):
        return self._items[1][0]

    def max_item(self):
        return self._items[1][1]

    def insert(self, priority, item):
        t = (priority, item)
        try:
            i = self._lookup[item]
            self._items[i] = t
            if i == 1 or priority < self._items[i // 2][0]:
                self._move_down(i, t)
                return
        except KeyError:
            i = len(self._items)
            self._lookup[item] = i
            self._items.append(t)
        self._move_up(i, t)

    def pop(self):
        item = self._items[1][1]
        self._remove(1, item)
        return item

    def remove(self, item):
        try:
            self._remove(self._lookup[item], item)
        except KeyError:
            return

    def _remove(self, i, item):
        items = self._items
        del self._lookup[item]
        if len(items) == 2:
            del items[1]
            return

        items[i] = t = items[-1]
        del items[-1]
        self._lookup[t[1]] = i
        if i == 1 or t[0] < items[i // 2][0]:
            self._move_down(i, t)
            return

        self._move_up(i, t)

    def _move_up(self, i, t):
        priority, item = t
        items, lookup = self._items, self._lookup
        while i != 1:
            p = i // 2
            pp, pi = pt = items[p]
            if priority <= pp:
                return

            items[p] = t
            items[i] = pt
            lookup[item] = p
            lookup[pi] = i
            i = p

    def _move_down(self, i, t):
        priority, item = t
        items, lookup = self._items, self._lookup
        n = len(items)
        while 1:
            c1 = 2 * i
            if c1 >= n:
                return

            p1, i1 = t1 = items[c1]
            c2 = c1 + 1
            if c2 < n:
                p2, i2 = t2 = items[c2]
                if p1 < p2:
                    c1, p1, i1, t1 = c2, p2, i2, t2
            if p1 < priority:
                return

            items[c1] = t
            items[i] = t1
            lookup[item] = c1
            lookup[i1] = i
            i = c1
