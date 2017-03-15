# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Virtualenv management"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import itertools
import os
import shutil
import subprocess
import sys

import cros_venv
from cros_venv import flock

_PACKAGE_DIR = os.path.join(cros_venv.WORKTREE_DIR, 'pip_packages')
_VENV_PY = '/usr/bin/python2.7'

# BASE_DEPENDENCIES are pip requirements automatically included in every
# virtualenv so we have control over which versions of bootstrap
# packages are installed.
_BASE_DEPENDENCIES = ('setuptools==28.2.0', 'pip==8.1.2')


class Venv(object):
    """Wraps all operations on a virtualenv directory."""

    def __init__(self, venv_dir, reqs_file):
        self._venv_dir = venv_dir
        self._reqs_file = reqs_file

    @property
    def _venv_python(self):
        return os.path.join(self._venv_dir, 'bin', 'python')

    @property
    def _lock_file(self):
        return os.path.join(self._venv_dir, '.create_venv.lock')

    @property
    def _installed_reqs_file(self):
        return os.path.join(self._venv_dir, '.installed.txt')

    def _lock(self):
        """Return lock context for the virtualenv."""
        return flock.FileLock(self._lock_file)

    @property
    def _site_packages(self):
        return os.path.join(
            self._venv_dir, 'lib', 'python%s' % sys.version[:3],
            'site-packages')

    def ensure(self):
        """Create or update virtualenv."""
        _makedirs_exist_ok(self._venv_dir)
        with self._lock():
            if not self._venv_initialized():
                self._init_venv()
            if not self._reqs_up_to_date():
                self._install_reqs()

    def _venv_initialized(self):
        """Check if virtualenv is initialized."""
        return all(os.path.exists(path)
                   for path in (self._venv_python, self._site_packages))

    def _init_venv(self):
        """Initialize virtualenv."""
        subprocess.check_call([
            'virtualenv', self._venv_dir,
            '-p', _VENV_PY,
            '--extra-search-dir', _PACKAGE_DIR,
            # TODO(ayatane): Ubuntu Precise ships with virtualenv 1.7,
            # which requires specifying --setuptools, else distribute is
            # used (distribute is deprecated).  virtualenv after 1.10
            # uses setuptools by default.  virtualenv >1.10 accepts the
            # --setuptools option but does not document it.  Once we no
            # longer have any hosts on virtualenv 1.7, the --setuptools
            # option can be removed.
            '--setuptools'])

    def _reqs_up_to_date(self):
        """Return whether the virtualenv reqs file is up to date."""
        if not os.path.exists(self._installed_reqs_file):
            return False
        with open(self._installed_reqs_file) as installed, \
             open(self._reqs_file) as specified:
            return _iter_equal(installed, specified)

    def _install_reqs(self):
        """Install indicated packages into virtualenv.

        The corresponding requirements file is also copied after
        installation.
        """
        subprocess.check_call(
            [self._venv_python, '-m', 'pip', 'install',
             '--no-index', '-f', 'file://' + _PACKAGE_DIR]
            + list(_BASE_DEPENDENCIES)
            + ['-r', self._reqs_file]
        )
        shutil.copyfile(self._reqs_file, self._installed_reqs_file)


def _iter_equal(first, second):
    """Return whether two iterables are equal.

    If one iterable is shorter, it will be filled with None and compared
    with the other.
    """
    return all(x == y for x, y in itertools.izip_longest(first, second))


def _makedirs_exist_ok(path):
    """Make directories recursively, ignoring if directory already exists."""
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
