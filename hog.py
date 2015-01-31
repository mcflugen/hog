#! /usr/bin/env python
from __future__ import print_function

import os
import sys
import types
import pwd
import time
from collections import defaultdict
from datetime import datetime, timedelta
from stat import *

import pandas


def itertree(top):
    for root, dir, files in os.walk(top):
        for fname in files:
            if not os.path.islink(fname):
                yield os.path.abspath(os.path.join(root, fname))


class Hogs(object):
    def __init__(self):
        self._hogs = defaultdict(int)
        self._files = defaultdict(int)
        self._last = defaultdict(float)

    def add(self, path):
        try:
            stat = os.lstat(path)
            uid = stat.st_uid
        except OSError as err:
            pass
        else:
            self._hogs[uid] += stat.st_size
            self._files[uid] += 1
            self._last[uid] = max(self._last[uid], stat.st_mtime)

    @classmethod
    def from_path(clazz, paths):
        hogs = clazz()
        if isinstance(paths, types.StringTypes):
            paths = [paths]
        for path in paths:
            for fname in itertree(path):
                hogs.add(fname)
        return hogs

    @staticmethod
    def _atime2age(atimes):
        age = {}
        now = datetime.now()
        for user in atimes:
            age[user] = (now - datetime.fromtimestamp(atimes[user])).days
        return age

    @staticmethod
    def _uid2name(uids):
        return dict([(uid, uid_to_name(uid)) for uid in uids])

    def to_dataframe(self, columns=None, ascending=True):
        df = pandas.DataFrame.from_dict({'user': Hogs._uid2name(self._hogs),
                                         'bytes': self._hogs,
                                         'files': self._files,
                                         'last': Hogs._atime2age(self._last)})

        df.set_index('user', inplace=True)
        df.sort(columns=columns, ascending=ascending, inplace=True)
        return df


def uid_to_name(uid):
    try:
        user = pwd.getpwuid(uid)
    except KeyError:
        return str(uid)
    else:
        return user.pw_name


unit_prefix = ['', 'K', 'M', 'G', 'T', 'P']


def bytes_to_string(bytes):
    import math

    try:
        log_1024 = int(math.log(bytes)/math.log(1024))
    except ValueError:
        log_1024 = 0
    return '%.1f %s' % (bytes / (1024. ** log_1024), unit_prefix[log_1024])


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Find disk hogs.')
    parser.add_argument('dirs', metavar='path', nargs='*',
                         help='Were to look for hogs', default=['.'])
    parser.add_argument('--sort-by', choices=['uid', 'bytes', 'files', 'last'],
                         help='Sort hogs', default='bytes')
    parser.add_argument('--reverse', action='store_true',
                         help='Biggest hogs first')
    parser.add_argument('--silent', action='store_true', default=False,
                         help='No output to screen')
    parser.add_argument('--pickle', type=str, default=None,
                        help='Save as pickle file')
    args = parser.parse_args()

    hogs = Hogs.from_path(args.dirs)

    df = hogs.to_dataframe(columns=args.sort_by, ascending=not args.reverse)

    if args.pickle:
        df.to_pickle(args.pickle)

    if not args.silent:
        print(df.to_string(formatters={'bytes': bytes_to_string}))


if __name__ == '__main__':
    main()
