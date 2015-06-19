#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

""" This module is for testing the behaviour of the Image class."""

import os

import mock

from testcloud import instance, image, config


class TestInstance:

    def test_expand_qcow(self):
        pass

    def test_create_seed(self):
        pass

    def test_set_seed_path(self):
        pass

    def test_download_initrd_and_kernel(self):
        pass

    def test_boot_base(self):
        pass

    def test_boot_atomic(self):
        pass

    def test_boot_pristine(self):
        pass


class TestFindInstance(object):

    def setup_method(self, method):
        self.conf = config.ConfigData()

    def test_non_existant_instance(self, monkeypatch):
        ref_name = 'test-123'
        ref_image = image.Image('file:///someimage.qcow2')

        stub_listdir = mock.Mock()
        stub_listdir.return_value = []
        monkeypatch.setattr(os, 'listdir', stub_listdir)

        test_instance = instance.find_instance(ref_name, ref_image)

        assert test_instance is None

    def test_find_exist_instance(self, monkeypatch):
        ref_name = 'test-123'
        ref_image = image.Image('file:///someimage.qcow2')
        ref_path = os.path.join(self.conf.DATA_DIR,
                                'instances/{}'.format(ref_name))

        stub_listdir = mock.Mock()
        stub_listdir.return_value = [ref_name]
        monkeypatch.setattr(os, 'listdir', stub_listdir)

        test_instance = instance.find_instance(ref_name, ref_image)

        assert test_instance.path == ref_path
