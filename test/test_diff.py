#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.join('lib', 'python3', 'dist-packages'))))

import diffuse.diff

a, b = sys.argv[1], sys.argv[2]
m = diffuse.diff.patience_diff(a, b)
print('diff(%s, %s) = %s' % (repr(a), repr(b), repr(m)))
