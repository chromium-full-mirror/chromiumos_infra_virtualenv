# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""TestCase classes"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import shutil
import tempfile
import os
import unittest


class TmpdirTestCase(unittest.TestCase):
    """TestCase subclass providing a tmpdir fixture."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._old_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmpdir)
