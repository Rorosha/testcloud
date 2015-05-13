#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
Exceptions used with testCloud
"""


class TestCloudException(BaseException):
    """Common ancestor for all TestCloud exceptions"""
    pass


class TestCloudImageError(TestCloudException):
    """Exception for errors having to do with images and image fetching"""
    pass

