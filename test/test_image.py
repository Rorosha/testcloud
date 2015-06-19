#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

""" This module is for testing the behaviour of the Image class."""

import pytest

from testcloud import image
from testcloud.exceptions import TestcloudImageError


class TestImage:

    def test_image_download_path(self):
        pass

    def test_image_name(self):
        pass

    def test_download(self):
        pass

#    def test_save_pristine(self):
#        pass
#
#    def test_load_pristine(self):
#        pass


class TestImageUriProcess(object):
    """The basic idea of what these tests do is to make sure that uris are
    parsed properly. http, https and file are OK and supported. ftp is an
    an example of a type which is not currently supported and should raise an
    exception."""

    def setup_method(self, method):
        self.image_name = 'image.img'
        self.len_data = 3

    def test_http_ur1(self):
        ref_type = 'http'
        ref_path = 'localhost/images/{}'.format(self.image_name)
        ref_uri = '{}://{}'.format(ref_type, ref_path)

        test_image = image.Image(ref_uri)
        test_data = test_image._process_uri(ref_uri)

        assert len(test_data) == self.len_data
        assert test_data['type'] == ref_type
        assert test_data['name'] == self.image_name
        assert test_data['path'] == ref_path

    def test_https_uri(self):
        ref_type = 'https'
        ref_path = 'localhost/images/{}'.format(self.image_name)
        ref_uri = '{}://{}'.format(ref_type, ref_path)

        test_image = image.Image(ref_uri)
        test_data = test_image._process_uri(ref_uri)

        assert len(test_data) == self.len_data
        assert test_data['type'] == ref_type
        assert test_data['name'] == self.image_name
        assert test_data['path'] == ref_path

    def test_file_uri(self):
        ref_type = 'file'
        ref_path = '/srv/images/{}'.format(self.image_name)
        ref_uri = '{}://{}'.format(ref_type, ref_path)

        test_image = image.Image(ref_uri)
        test_data = test_image._process_uri(ref_uri)

        assert len(test_data) == self.len_data
        assert test_data['type'] == ref_type
        assert test_data['name'] == self.image_name
        assert test_data['path'] == ref_path

    def test_invalid_uri_type(self):
        ref_type = 'ftp'
        ref_path = '/localhost/images/{}'.format(self.image_name)
        ref_uri = '{}://{}'.format(ref_type, ref_path)

        with pytest.raises(TestcloudImageError):
            image.Image(ref_uri)

    def test_invalid_uri(self):
        ref_uri = 'leprechaunhandywork'

        with pytest.raises(TestcloudImageError):
            image.Image(ref_uri)
