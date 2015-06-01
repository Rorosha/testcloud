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

class TestCloudCliError(TestCloudException):
    """Exception for errors having to do with TestCloud CLI processing"""
    pass

class TestCloudImageError(TestCloudException):
    """Exception for errors having to do with images and image fetching"""
    pass

class TestCloudInstanceError(TestCloudException):
    """Exception for errors having to do with instances and instance prep"""
    pass

class DomainNotFoundError(BaseException):
    """Exception to raise if the queried domain can't be found."""

    def __init__(self):
        self.value = "Could not find the requested virsh domain, did it register?"

    def __str__(self):
        return repr(self.value)
