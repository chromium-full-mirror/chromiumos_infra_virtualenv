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
import os
import sys

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
    try:
        print(venv.ensure())
        logging.debug('Log file can be found at: %s', venv.logfile)
    except venvlib.VirtualenvMissingError as e:
        print('%s: error: %s' % (os.path.basename(sys.argv[0]), e),
              file=sys.stderr)
        sys.exit(1)
    except Exception:
        logging.error('Creating venv with reqs file "%s" failed',
                      args.reqs_file, exc_info=True)
        logging.error('Dumping entire creation log:\n%s', venv.logdata)
        sys.exit(1)


def configure_logging(verbose):
    if verbose:
        logging.basicConfig(level='DEBUG')
    else:
        logging.basicConfig(level='INFO')


if __name__ == '__main__':
    main()
