#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.signal

class Widget:
    def __init__(self, name):
        self._name = name

    def callback(self, sig, cb_data, data):
        print('callback(%s): %s %s %s' % (self._name, repr(sig), repr(cb_data), repr(data)))

w1 = Widget('w1')
w2 = Widget('w2')
s = diffuse.signal.Signal()
w1_id = s.add_callback(w1.callback)
s.emit('hello')
s.add_callback(w2.callback)
s.emit('there')
del w1
#s.removeCallback(w1_id)
s.emit('bob')
