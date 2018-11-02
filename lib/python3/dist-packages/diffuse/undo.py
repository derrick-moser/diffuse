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

class UndoManager:
    def __init__(self):
        self._enabled = False
        self._depth = 0
        self._block = None
        self._undos = []
        self._redos = []

    def __repr__(self):
        return '<UndoManager block=%s, depth=%d, undos=%s, redos=%s/>' % (repr(self._block), self._depth, repr(self._undos), repr(self._redos))

    def enable(self):
        self._enabled = True

    def begin_block(self):
        if self._block is None:
            self._block = []
        self._depth += 1

    def end_block(self):
        self._depth -= 1
        if self._depth == 0:
            if self._block:
                self._undos.append(self._block)
            self._block = None

    def apply(self, action):
        if self._enabled:
            self._block.append(action)
            self._redos = []
        action.redo()

    def redo(self):
        assert self._block is None
        if self._redos:
            actions = self._redos.pop()
            actions.reverse()
            for a in actions:
                a.redo()
            self._undos.append(actions)

    def undo(self):
        assert self._block is None
        if self._undos:
            actions = self._undos.pop()
            actions.reverse()
            for a in actions:
                a.undo()
            self._redos.append(actions)

    def clear(self):
        assert self._block is None
        self._undos = []
        self._redos = []
