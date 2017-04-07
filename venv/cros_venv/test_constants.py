# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import unittest

from cros_venv import constants


class ConstantsTestCase(unittest.TestCase):
    """TestCase for constants."""

    def test_REPO_DIR(self):
        """Test that REPO_DIR is a git repo."""
        self.assertTrue(
            os.path.isdir(os.path.join(constants.REPO_DIR, '.git')))
