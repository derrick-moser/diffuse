#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.undo

class Action:
    def __init__(self, name):
        self._name = name

    def redo(self):
        print('redo', self._name)

    def undo(self):
        print('undo', self._name)

m = diffuse.undo.UndoManager()
m.begin_block()
m.apply(Action('a1'))
m.apply(Action('a2'))
m.end_block()
m.undo()
m.redo()
print(m)
