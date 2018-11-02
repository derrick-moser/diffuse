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

import os
import diffuse.signal, diffuse.undo, diffuse.diff

# split into lines on either Mac, Windows, or Unix line endings
def _split_lines(s):
    i, n, sf, ss, cr, nl = 0, len(s), s.find, [], -1, -1
    sa = ss.append
    while i < n:
        if cr < i:
            # find the next '\r'
            cr = sf('\r', i)
            if cr == -1:
                cr = n
        if nl < i:
            # find the next '\n'
            nl = sf('\n', i)
            if nl == -1:
                nl = n
        if cr < nl:
            # found Mac or Windows line ending
            if cr + 1 < n and s[cr + 1] == '\n':
                # it is a Windows line ending
                cr += 1
            sa(s[i:cr + 1])
            i = cr + 1
        else:
            # found Unix line ending or EOF
            if nl == n:
                # it is EOF
                nl -= 1
            sa(s[i:nl + 1])
            i = nl + 1
    return ss

def _make_block(n):
    return [ n ] if n else []

def _cut_blocks(blocks, i0, i1):
    pre, mid, post, i = [], [], [], 0
    for b in blocks:
        if i < i0:
            n = min(b, i0 - i)
            pre.append(n)
            i += n
            b -= n
        if b:
            if i < i1:
                n = min(b, i1 - i)
                mid.append(n)
                i += n
                b -= n
            if b:
                post.append(b)
    return pre, mid, post

class Line:
    def __init__(self, s=None, i=None):
        self._text = s
        self._edit = None
        self._line_number = i

    def __repr__(self):
        return '<Edit line_number=%d, text=%s, edit=%s/>' % (self._line_number, repr(self._text), repr(self._edit))

class File:
    def __init__(self, undo_manager, nlines):
        self._undo_manager = undo_manager
        # file name
        self._name = None
        # name of codec used to translate the file contents to unicode text
        self._encoding = None
        # the VCS object
        self._vcs = None
        # revision used to retrieve file from the VCS
        self._revision = None
        # alternate text to display instead of the actual file name
        self._label = None
        # 'stat' for files read from disk -- used to warn about changes to
        # the file on disk before saving
        self._stat = None
        # most recent 'stat' for files read from disk -- used on focus
        # change to warn about changes to file on disk
        self._last_stat = None

        # we assign a unique ID after every destructive change
        self._content_id = 0
        # content ID corresponding to the file on disk
        self._saved_content_id = 0
        # next unique content ID
        self._next_content_id = 1

        self._contents = nlines * [ None ]

        self._signals = sigs = {}
        for name in 'file-info-changed', 'contents-changed':
            sigs[name] = diffuse.signal.Signal()

        # FIXME: where should these live?
        #self._annotation_author = None
        #self._annotation_date = None
        #self._annotation_revision = None

    def __repr__(self):
        return '<File name=%s, encoding=%s, revision=%s contents=%s/>' % (repr(self._name), repr(self._encoding), repr(self._revision), repr(self._contents))

    class FileInfoAction:
        def __init__(self, f, pre_name, post_name, pre_encoding, post_encoding):
            self._data = f, pre_name, post_name, pre_encoding, post_encoding
        def redo(self):
            f, pre_name, post_name, pre_encoding, post_encoding = self._data
            f._file_info_changed(post_name, post_encoding)
        def undo(self):
            f, pre_name, post_name, pre_encoding, post_encoding = self._data
            f._file_info_changed(pre_name, pre_encoding)

    def _file_info_changed(self, name, encoding):
        self._name = name
        self._encoding = encoding
        self._signals['file-info-changed'].emit()

    def set_file_info(self, name, encoding, stat, content_id):
        self._stat = stat
        self._last_stat = stat
        self._saved_content_id = content_id
        self._undo_manager.apply(self.FileInfoAction(self, self._name, name, self._encoding, encoding))

    class ContentsAction:
        def __init__(self, f, i, pre, post, pre_content_id, post_content_id):
            self._data = f, i, pre, post, pre_content_id, post_content_id
        def redo(self):
            f, i, pre, post, pre_content_id, post_content_id = self._data
            f._contents_changed(i, pre, post, post_content_id)
        def undo(self):
            f, i, pre, post, pre_content_id, post_content_id = self._data
            f._contents_changed(i, post, pre, pre_content_id)

    def _contents_changed(self, i, pre, post, content_id):
        self._contents[i:i + len(pre)] = post
        self._content_id = content_id
        self._signals['contents-changed'].emit((i, pre, post))

    def set_contents(self, i1, i2, post):
        post_content_id = self._next_content_id
        self._next_content_id += 1
        self._undo_manager.apply(self.ContentsAction(self, i1, self._contents[i1:i2], post, self._content_id, post_content_id))

# FIXME: this can be greatly improved upon
# merge pane will have a map from lines to the conflict to which it belongs
class Conflict:
    def __init__(self):
        # conflict range... editing the merge source causes all later conflict ranges to change
        self._first_line = first_line
        self._last_line = last_line
        # true if the conflict has been resolved
        self._resolved = False
        # file used to copy the lines or None
        self._src = None

class MergeLine:
    def __init__(self, src):
        # source Line
        self._src = src
        self._edit = None

class FileCompare:
    def __init__(self, n):
        self._undo_manager = diffuse.undo.UndoManager()
        self._panes = [ File(self._undo_manager, 0) for i in range(n) ]
        self._blocks = []
        self._signals = sigs = {}
        for name in ('panes_changed', ): #'blocks_changed'
            sigs[name] = diffuse.signal.Signal()

    def __repr__(self):
        return '<FileCompare undo_manager=%s, panes=%s, blocks=%s, signals=%s/>' % (self._undo_manager, self._panes, self._blocks, self._signals)

    def n_panes(self):
        return len(self._panes)

    def get_n_lines(self):
        return len(self._panes[0]._contents)

    def enable_undos(self):
        self._undo_manager.enable()

    class PaneAction:
        def __init__(self, fc, p, pre, post):
            self._data = fc, p, pre, post
        def redo(self):
            fc, p, pre, post = self._data
            fc._panes_changed(p, pre, post)
        def undo(self):
            fc, p, pre, post = self._data
            fc._panes_changed(p, post, pre)

    def _panes_changed(self, p, pre, post):
        self._panes[p:p + len(pre)] = post
        self._signals['panes_changed'].emit((p, pre, post))

    def insert_pane(self, p):
        self._undo_manager.apply(self.PaneAction(self, p, [], [ File(self._undo_manager, sum(self._blocks)) ]))

    def _remove_pane(self, p):
        # NB: caller should remove un-needed rows
        # FIXME: should this remove unused rows too?
        self._undo_manager.apply(self.PaneAction(self, p, self._panes[p:p + 1], []))

    def swap_panes(self, p1, p2):
        pane1, pane2 = self._panes[p1:p1 + 1], self._panes[p2:p2 + 1]
        self._undo_manager.apply(self.PaneAction(self, p1, pane1, pane2))
        self._undo_manager.apply(self.PaneAction(self, p2, pane2, pane1))

    class BlockAction:
        def __init__(self, blocks, i, pre, post):
            self._data = blocks, i, pre, post
        def redo(self):
            blocks, i, pre, post = self._data
            blocks[i:i + len(pre)] = post
        def undo(self):
            blocks, i, pre, post = self._data
            blocks[i:i + len(post)] = pre

    def _remove_null_rows(self, contents_list, blocks):
        new_contents, new_blocks, n, bi, bs, processed  = [ [] for c in contents_list ], [], len(contents_list[0]), -1, 0, 0
        na, pairing = new_blocks.append, list(zip(contents_list, [ c.append for c in new_contents ]))
        for i in range(n):
            for contents in contents_list:
                if contents[i]:
                    for pre, a in pairing:
                        a(pre[i])
                    break
            else:
                # found a row that needs removal
                while bs < i:
                    delta = bs - processed
                    if delta:
                        na(delta)
                        processed += delta
                    bi += 1
                    bs += blocks[bi]
                # process removed line
                if bs <= i:
                    bi += 1
                    bs += blocks[bi]
                processed += 1
        while bs < n:
            delta = bs - processed
            if delta:
                na(delta)
                processed += delta
            bi += 1
            bs += blocks[bi]
        if processed < bs:
            na(bs - processed)
        return new_contents, new_blocks

    def get_string(self, p, i):
        e = self._panes[p]._contents[i]
        if e is not None:
            if e._edit is not None:
                return e._edit
            if e._text is not None:
                return e._text
        return ''

    def _get_compare_string(self, e):
        if e._edit is not None:
            return e._edit
        if e._text is not None:
            return e._text
        return ''

    def _auto_align(self, contents_left, contents_right, b_left, b_right):
        # FIXME: it may be faster to rebuild everything
        new_contents_left = [ [] for c in contents_left ]
        new_contents_right = [ [] for c in contents_right ]
        pairing_left = list(zip(contents_left, [ c.extend for c in new_contents_left ]))
        pairing_right = list(zip(contents_right, [ c.extend for c in new_contents_right ]))

        new_contents, new_blocks = [], []
        new_contents.extend(new_contents_left)
        new_contents.extend(new_contents_right)

        idx_left, idx_right, count_left, count_right, bi_left, bi_right, bs_left, bs_right, nprocessed = 0, 0, 0, 0, -1, -1, 0, 0, 0

        c_left = contents_left[-1]
        c_right = contents_right[0]
        gcs = self._get_compare_string

        for i_left, i_right, n in diffuse.diff.patience_diff([ gcs(c) for c in c_left if c ], [ gcs(c) for c in c_right if c ]):
            for i in range(n + 1):
                # process matching lines
                goal = i_left + i
                start_left = idx_left
                while count_left < goal:
                    if c_left[idx_left]:
                        count_left += 1
                    idx_left += 1
                while idx_left < len(c_left) and c_left[idx_left] is None:
                    idx_left += 1
                for contents, ne in pairing_left:
                    ne(contents[start_left:idx_left])

                goal = i_right + i
                start_right = idx_right
                while count_right < goal:
                    if c_right[idx_right]:
                        count_right += 1
                    idx_right += 1
                while idx_right < len(c_right) and c_right[idx_right] is None:
                    idx_right += 1
                for contents, ne in pairing_right:
                    ne(contents[start_right:idx_right])

                # insert spacers
                delta_left, delta_right = idx_left - start_left, idx_right - start_right
                delta = delta_right - delta_left
                if delta > 0:
                    e = delta * [ None ]
                    for contents, ne in pairing_left:
                        ne(e)
                elif delta < 0:
                    e = -delta * [ None ]
                    for contents, ne in pairing_right:
                        ne(e)

                while delta_left or delta_right:
                    cut = False
                    if delta_left:
                        if delta_right:
                            n = min(delta_left, delta_right)
                        else:
                            n = delta_left
                    else:
                        n = delta_right

                    if delta_left and n > bs_left - start_left:
                        cut = True
                        n = bs_left - start_left
                        bi_left += 1
                        bs_left += b_left[bi_left]
                    if delta_right and n > bs_right - start_right:
                        cut = True
                        n = bs_right - start_right
                        bi_right += 1
                        bs_right += b_right[bi_right]

                    nprocessed += n
                    if cut:
                        if nprocessed:
                            new_blocks.append(nprocessed)
                        nprocessed = 0

                    if delta_left:
                        start_left += n
                        delta_left -= n
                    if delta_right:
                        start_right += n
                        delta_right -= n

        if nprocessed:
            new_blocks.append(nprocessed)
        return new_contents, new_blocks

    def _auto_align3(self, c_left, c_mid, c_right, b_left, b_mid, b_right):
        if c_left:
            if len(c_left) == 0:
                b_left = []
            elif len(c_left) == 1:
                b_left = _make_block(len(c_left[0]))
            c_left, b_left = self._remove_null_rows(c_left, b_left)
            c_mid, b_mid = self._auto_align(c_left, c_mid, b_left, b_mid)

        if c_right:
            if len(c_right) == 0:
                b_right = []
            elif len(c_right) == 1:
                b_right = _make_block(len(c_right[0]))
            c_right, b_right = self._remove_null_rows(c_right, b_right)
            c_mid, b_mid = self._auto_align(c_mid, c_right, b_mid, b_right)

        return c_mid, b_mid

    def _manual_align(self, p, i0_left, i1_left, i0_right, i1_right):
        start, end, b_pre, b_mid, b_post, i = min(i0_left, i0_right), max(i1_left, i1_right), [], [], [], 0
        for b in self._blocks:
            if i + b <= start:
                b_pre.append(b)
            elif i < end:
                b_mid.append(b)
            else:
                b_post.append(b)
            i += b

        if len(p_left) == 1:
            b0_left, b1_left, b2_left = _make_block(i0_left - start), _make_block(i1_left - i0_left), _make_block(end - i1_left)
        else:
            b0_left, b1_left, b2_left = _cut_blocks(b_mid, i0_left - start, i1_left - start)

        p_left, p_right = self._panes[:p + 1], self._panes[p + 1:]
        c0_left = [ pane._contents[start:i0_left] for pane in p_left ]
        c1_left = [ pane._contents[i0_left:i1_left] for pane in p_left ]
        c2_left = [ pane._contents[i1_left:end] for pane in p_left ]
        c0_left, b0_left = self._remove_null_rows(c0_left, b0_left)
        c1_left, b1_left = self._remove_null_rows(c1_left, b1_left)
        c2_left, b2_left = self._remove_null_rows(c2_left, b2_left)

        if len(p_right) == 1:
            b0_right, b1_right, b2_right = _make_block(i0_right - start), _make_block(i1_right - i0_right), _make_block(end - i1_right)
        else:
            b0_right, b1_right, b2_right = _cut_blocks(b_mid, i0_right - start, i1_right - start)

        c0_right = [ pane._contents[start:i0_right] for pane in p_right ]
        c1_right = [ pane._contents[i0_right:i1_right] for pane in p_right ]
        c2_right = [ pane._contents[i1_right:end] for pane in p_right ]
        c0_right, b0_right = self._remove_null_rows(c0_right, b0_right)
        c1_right, b1_right = self._remove_null_rows(c1_right, b1_right)
        c2_right, b2_right = self._remove_null_rows(c2_right, b2_right)

        c0, b0 = self._auto_align(c0_left, c0_right, b0_left, b0_right)
        c1, b1 = self._auto_align(c1_left, c1_right, b1_left, b1_right)
        c2, b2 = self._auto_align(c2_left, c2_right, b2_left, b2_right)

        for a, b, c in zip(c0, c1, c2):
            a.extend(b)
            a.extend(c)
        b0.extend(b1)
        b0.extend(b2)

        for pane, contents in zip(self._panes, c0):
            pane.set_contents(start, end, contents)

        npre = len(b_pre)
        self._undo_manager.apply(self.BlockAction(self._blocks, npre, npre + len(b_mid), b0))

    def _replace_contents(self, p, i0, i1, contents):
        b_pre, blocks, b_post = _cut_blocks(self._blocks, i0, i1)
        c_mid, b_mid = [ contents ], _make_block(len(contents))

        p_left, p_mid, p_right = self._panes[:p], [ self._panes[p] ], self._panes[p + 1:]

        c_left = [ pane._contents[i0:i1] for pane in p_left ]
        c_right = [ pane._contents[i0:i1] for pane in p_right ]

        c_mid, b_mid = self._auto_align3(c_left, c_mid, c_right, blocks, b_mid, blocks)
        for pane, contents in zip(self._panes, c_mid):
            pane.set_contents(i0, i1, contents)

        b_pre.extend(b_mid)
        b_pre.extend(b_post)
        self._undo_manager.apply(self.BlockAction(self._blocks, 0, self._blocks[:], b_pre))

    # FIXME: name and encoding should come from elsewhere
    # FIXME: auto align, load_file, and reloadFile has a lot in common
    def load_file(self, p, name, encodings, isreload=False):
        pane = self._panes[p]
        pre = pane._contents

        stat = os.stat(name)
        s = open(name, 'rb').read()
        for encoding in encodings:
            try:
                post = [ Line(s, i) for i, s in enumerate(_split_lines(s.decode(encoding))) ]
                pane.set_file_info(name, encoding, stat, pane._next_content_id)
                break
            except UnicodeDecodeError:
                pass
        else:
            raise UnicodeDecodeError()

        blocks, new_blocks_contents, new_blocks_end = self._blocks, [], []

        if isreload:
            bn, bi, bs, count, idx = len(blocks), 0, 0, 0, 0

            # FIXME: should 'pre' be cleaned of uncommitted edits?
            gcs = self._get_compare_string
            for idx_0, idx_1, n_match in diffuse.diff.patience_diff([ gcs(c) for c in pre if c ], [ gcs(c) for c in post ]):
                idx_0_matched = idx_0 + n_match
                while bi < bn and count <= idx_0_matched:
                    bs_old = bs
                    b = blocks[bi]
                    bs += b
                    bi += 1

                    old_count = count
                    count += sum([ 1 for c in pre[bs_old:bs] if c ])
                    # keep cut if it falls inside the matched segment
                    if idx_0 < old_count < idx_0_matched:
                        new_blocks_end.append(old_bs)
                        old_idx = idx
                        idx = idx_1 + old_count - idx_0
                        new_blocks_contents.append(post[old_idx:idx])
            new_blocks_end.append(bs)
            new_blocks_contents.append(post[idx:])
        else:
            new_blocks_end.append(len(pre))
            new_blocks_contents.append(post)

        p_left, p_right = self._panes[:p], self._panes[p + 1:]

        new_contents, new_blocks, bi, bs = [ [] for p in self._panes ], [], 0, 0
        for new_block_end, new_content in zip(new_blocks_end, new_blocks_contents):
            # find range of blocks ending here
            old_bs, old_bi = bs, bi
            while bs < new_block_end:
                bs += blocks[bi]
                bi += 1

            # merge new_content with the appropriate part of the other panes
            c_mid, b_mid = [ new_content ], _make_block(len(new_content))
            c_left = [ pane._contents[old_bs:bs] for pane in p_left ]
            c_right = [ pane._contents[old_bs:bs] for pane in p_right ]

            b = blocks[old_bi:bi]
            c_mid, b_mid = self._auto_align3(c_left, c_mid, c_right, b, b_mid, b)

            # add to new results
            for dest, c in zip(new_contents, c_mid):
                dest.extend(c)
            new_blocks.extend(b_mid)

        # finally update the actual data
        for pane, contents in zip(self._panes, new_contents):
            pane.set_contents(0, bs, contents)

        self._undo_manager.apply(self.BlockAction(self._blocks, 0, self._blocks[:], new_blocks))

    def isolate(self, p, i0, i1):
        if len(self._panes) < 2:
            return

        # insert cuts
        b_pre, b_mid, b_post = _cut_blocks(self._blocks, i0, i1)

        # isolate pane
        p_isolated = self._panes[p]
        c_isolated = [ c for c in p_isolated._contents[i0:i1] if c ]
        n = len(c_isolated)
        b_isolated = _make_block(n)

        panes = self._panes[:p]
        panes.extend(self._panes[p + 1:])
        c_rest = [ pane._contents[i0:i1] for pane in panes ]
        if len(panes) == 1:
            b_mid = _make_block(i1 - i0)

        c_rest, b_mid = self._remove_null_rows(c_rest, b_mid)

        c_isolated.extend(len(c_rest[0]) * [ None ])
        p_isolated.set_contents(i0, i1, c_isolated)

        for pane, contents in zip(panes, c_rest):
            c = n * [ None ]
            c.extend(contents)
            pane.set_contents(i0, i1, c)

        be = b_pre.extend
        for b in b_isolated, b_mid, b_post:
            be(b)
        self._undo_manager.apply(self.BlockAction(self._blocks, 0, self._blocks[:], b_pre))
