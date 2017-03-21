# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This package contains modules for creating and updating virtualenvs.

To run:

    $ python2 -m venv

See __main__.py for details.

To run the tests:

    $ python2 -m unittest discover venv
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

import cros_venv

# Directory of cros_venv package
_CROS_VENV_DIR = os.path.abspath(cros_venv.__path__[0])

# Root directory of infra_virtualenv repo
REPO_DIR = os.path.dirname(_CROS_VENV_DIR)
