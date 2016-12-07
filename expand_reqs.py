#!/usr/bin/env python
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Expand recursive requirements in pip requirements.txt files.

$ ./expand_reqs.py <requirements.txt

Run tests using: python -m unittest expand_reqs
"""

import os
import shutil
import sys
import tempfile
import unittest


def main():
    for line in expand_reqs(sys.stdin):
        print line


def expand_reqs(infile):
    """Yield each line in infile, recursing into included requirements files."""
    for line in infile:
        line = line.strip()
        yield line
        requirements = _get_requirements_file(line)
        if requirements and os.path.exists(requirements):
            with open(requirements) as subfile:
                for subline in expand_reqs(subfile):
                    yield subline
            yield '# END %s' % line


def _get_requirements_file(line):
    """Return the requirements file specified by the input line.

    A requirements line looks like: -r requirements.txt

    Args:
        line: String input

    Returns:
        Requirements file path as string if present, else an empty string.
    """
    parts = line.split()
    if len(parts) == 2 and parts[0] == '-r':
        return parts[1]
    else:
        return ''


class TmpdirTestCase(unittest.TestCase):
    """TestCase subclass providing a tmpdir fixture."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._old_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmpdir)


class ExpandReqsTestCase(TmpdirTestCase):
    """Tests for expand_reqs()."""

    def setUp(self):
        super(ExpandReqsTestCase, self).setUp()
        self.flat = 'flat.txt'
        self.recursive = 'recursive.txt'
        with open(self.flat, 'w') as f:
            f.write('foo\nbar')
        with open(self.recursive, 'w') as f:
            f.write('spam\neggs\n-r flat.txt')

    def test_no_recurse(self):
        with open(self.flat) as f:
            self.assertEqual(
                list(expand_reqs(f)),
                ['foo', 'bar'])

    def test_recurse(self):
        with open(self.recursive) as f:
            self.assertEqual(
                list(expand_reqs(f)),
                ['spam', 'eggs', '-r flat.txt',
                 'foo', 'bar', '# END -r flat.txt'])


class GetRequirementsFileTestCase(unittest.TestCase):
    """Tests for _get_requirements_file()."""

    def test_no_match(self):
        self.assertEqual(_get_requirements_file('foo'), '')

    def test_match(self):
        self.assertEqual(_get_requirements_file('-r foo.txt'), 'foo.txt')

    def test_match_with_whitespace(self):
        self.assertEqual(_get_requirements_file('  -r foo.txt  \n'), 'foo.txt')


if __name__ == '__main__':
    main()
