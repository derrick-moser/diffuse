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

import weakref

class Signal:
    def __init__(self):
        self._callbacks = {}
        self._next_id = 0

    def __repr__(self):
        return '<Signal callbacks=%s/>' % (repr(self._callbacks), )

    def add_callback(self, callback, callback_data=None):
        cur_id = self._next_id
        self._next_id += 1
        self._callbacks[cur_id] = weakref.WeakMethod(callback), callback_data
        return cur_id

    def remove_callback(self, cur_id):
        del self._callbacks[cur_id]

    def emit(self, data=None):
        cbs, r = [], []
        for k, v in self._callbacks.items():
            callback, callback_data = v
            cb = callback()
            if cb:
                cbs.append((cb, callback_data))
            else:
                r.append(k)
        for callback, callback_data in cbs:
            callback(self, callback_data, data)
        for k in r:
            del self._callbacks[k]
