# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This package contains modules for creating and updating virtualenvs.

To run the tests, use the script bin/run_tests.

This package is used to create virtualenvs, so it cannot depend on any
libraries outside of the Python standard library.  The unit tests are
exempt and may depend on libraries installed through virtualenv (serving
as a self-test that create_venv works).
"""
