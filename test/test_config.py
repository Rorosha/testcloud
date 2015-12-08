#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

from testcloud import config


REF_DATA_DIR = "/some/random/dir/for/testing/"
REF_STORE_DIR = "/some/random/dir/for/testing/backingstore/"
REF_CONF_CONTENTS = """DATA_DIR = "{}"
STORE_DIR = "{}/backingstores"
""".format(REF_DATA_DIR, REF_STORE_DIR)


class TestConfig(object):
    def setup_method(self, method):
        config._config = None

    def test_get_config_object(self, monkeypatch):
        '''Simple test to grab a config object, will return default config
        values.
        '''

        monkeypatch.setattr(config, 'CONF_DIRS', [])
        ref_conf = config.ConfigData()

        test_conf = config.get_config()

        assert ref_conf.META_DATA == test_conf.META_DATA

    def test_missing_config_file(self, monkeypatch):
        '''Make sure that None is returned if no config files are found'''
        monkeypatch.setattr(config, 'CONF_DIRS', [])

        test_config_filename = config._find_config_file()
        assert test_config_filename is None

    # these are actually functional tests since they touch the filesystem but
    # leaving them here as we have no differentiation between unit and
    # functional tests at the moment
    def test_load_config_object(self, tmpdir):
        '''load config object from file, make sure it's loaded properly'''

        refdir = tmpdir.mkdir('conf')
        ref_conf_filename = '{}/{}'.format(refdir, config.CONF_FILE)
        with open(ref_conf_filename, 'w+') as ref_conffile:
            ref_conffile.write(REF_CONF_CONTENTS)

        test_config = config._load_config(ref_conf_filename)

        assert test_config.DATA_DIR == REF_DATA_DIR

    def test_merge_config_file(self, tmpdir):
        '''merge loaded config object with defaults, make sure that the defaults
        are overridden.
        '''

        refdir = tmpdir.mkdir('conf')
        ref_conf_filename = '{}/{}'.format(refdir, config.CONF_FILE)
        with open(ref_conf_filename, 'w+') as ref_conffile:
            ref_conffile.write(REF_CONF_CONTENTS)

        test_config_obj = config._load_config(ref_conf_filename)

        test_config = config.ConfigData()
        assert test_config.DATA_DIR != REF_DATA_DIR

        test_config.merge_object(test_config_obj)
        assert test_config.DATA_DIR == REF_DATA_DIR

    def test_load_merge_config_file(self, tmpdir, monkeypatch):
        '''get config, making sure that an addional config file is found. make
        sure that default values are properly overridden.
        '''

        refdir = tmpdir.mkdir('conf')
        ref_conf_filename = '{}/{}'.format(refdir, config.CONF_FILE)
        with open(ref_conf_filename, 'w+') as ref_conffile:
            ref_conffile.write(REF_CONF_CONTENTS)

        monkeypatch.setattr(config, 'CONF_DIRS', [str(refdir)])
        test_config = config.get_config()

        assert test_config.DATA_DIR == REF_DATA_DIR
