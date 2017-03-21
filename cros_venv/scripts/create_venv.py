# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Create or update a virtualenv.

$ python -m cros_venv.scripts.create_venv path/to/requirements.txt

This creates a versioned virtualenv with the given requirements
installed.  The path to the created virtualenv is printed to stdout.
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
    parser.add_argument('reqs_file')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    configure_logging(args.verbose)

    with open(args.reqs_file, 'r') as f:
        spec = venvlib.make_spec(f)
    venv = venvlib.VersionedVenv(spec)
    print(venv.ensure())


def configure_logging(verbose):
    if verbose:
        logging.basicConfig(level='DEBUG')
    else:
        logging.getLogger().addHandler(logging.NullHandler())


if __name__ == '__main__':
    main()
