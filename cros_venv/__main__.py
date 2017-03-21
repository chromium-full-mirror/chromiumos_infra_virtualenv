# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Create or update a virtualenv.

$ python -m cros_venv path/to/venv path/to/requirements.txt

This creates a virtualenv at path/to/venv with the given requirements
installed.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging

from cros_venv import venvlib


def main():
    """See module docstring."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('venv_dir')
    parser.add_argument('reqs_file')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    configure_logging(args.verbose)

    venv = venvlib.Venv(
        venv_dir=args.venv_dir,
        reqs_file=args.reqs_file)
    venv.ensure()


def configure_logging(verbose):
    if verbose:
        logging.basicConfig(level='DEBUG')
    else:
        logging.getLogger().addHandler(logging.NullHandler())


if __name__ == '__main__':
    main()
