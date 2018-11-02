#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.filecompare

fc = diffuse.filecompare.FileCompare(2)
fc._undo_manager.begin_block()
fc.insert_pane(0)
fc.load_file(0, 'test.txt', [ 'utf-8' ])
fc._undo_manager.end_block()
print(fc)

fc._undo_manager.undo()
print(fc)

fc._undo_manager.redo()
print(fc)

fc._undo_manager.begin_block()
fc.insert_pane(1)
fc.load_file(1, 'test2.txt', [ 'utf-8' ])
fc._undo_manager.end_block()
print(fc)

fc._undo_manager.begin_block()
fc.isolate(1, 3, 4)
fc._undo_manager.end_block()
print(fc)
