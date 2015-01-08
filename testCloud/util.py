#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This module contains helper functions for the housekeeping tasks of testCloud.
"""

import os
import shutil
import glob

import config


def create_user_data(path, password, overwrite=False, atomic=False):
    """Save the right  password to the 'user-data' file needed to
    emulate cloud-init. Default username on cloud images is "fedora"

    Will not overwrite an existing user-data file unless
    the overwrite kwarg is set to True."""

    if atomic:
        file_data = config.ATOMIC_USER_DATA % password

    else:
        file_data = config.USER_DATA % password

    if os.path.isfile(path + '/meta/user-data'):
        if overwrite:

            with open(path + '/meta/user-data', 'w') as user_file:
                user_file.write(file_data)

                return "user-data file generated."
        else:
            return "user-data file already exists"

    with open(path + '/meta/user-data', 'w') as user_file:
        user_file.write(file_data)

    return "user-data file generated."


def create_meta_data(path, hostname, overwrite=False):
    """Save the required hostname data to the 'meta-data' file needed to
    emulate cloud-init.

    Will not overwrite an existing user-data file unless
    the overwrite kwarg is set to True."""

    file_data = config.META_DATA % hostname

    if os.path.isfile(path + '/meta/meta-data'):
        if overwrite:

            with open(path + '/meta/meta-data', 'w') as meta_data_file:
                meta_data_file.write(file_data)

                return "meta-data file generated."
        else:
            return "meta-data file already exists"

    with open(path + '/meta/meta-data', 'w') as meta_data_file:
        meta_data_file.write(file_data)

    return "meta-data file generated."


def create_dirs():
    """Create the dirs in the download dir we need to store things."""
    os.makedirs(config.LOCAL_DOWNLOAD_DIR + 'testCloud/meta')
    if not os.path.exists(config.PRISTINE):
        os.makedirs(config.PRISTINE)
        print "Created image store: {0}".format(config.PRISTINE)
    return "Created tmp directories."


def clean_dirs():
    """Remove dirs after a test run."""
    if os.path.exists(config.LOCAL_DOWNLOAD_DIR + 'testCloud'):
        shutil.rmtree(config.LOCAL_DOWNLOAD_DIR + 'testCloud')
    return "All cleaned up!"


def list_pristine():
    """List the pristine images currently saved."""
    images = glob.glob(config.PRISTINE + '/*')
    for image in images:
        print '\t- {0}'.format(image.split('/')[-1])
