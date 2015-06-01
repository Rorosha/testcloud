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
import subprocess
import logging

import libvirt
import xml.etree.ElementTree as ET

from . import config

log = logging.getLogger('testCloud.util')
config_data = config.get_config()


def create_dirs():
    """Create the dirs in the download dir we need to store things."""
    os.makedirs(config_data.LOCAL_DOWNLOAD_DIR + 'testCloud/meta')
    if not os.path.exists(config_data.PRISTINE):
        os.makedirs(config_data.PRISTINE)
        log.debug("Created image store: {0}".format(config_data.PRISTINE))
    return "Created tmp directories."


def clean_dirs():
    """Remove dirs after a test run."""
    if os.path.exists(config_data.LOCAL_DOWNLOAD_DIR + 'testCloud'):
        shutil.rmtree(config_data.LOCAL_DOWNLOAD_DIR + 'testCloud')
    return "All cleaned up!"


def list_pristine():
    """List the pristine images currently saved."""
    images = glob.glob(config_data.PRISTINE + '/*')
    for image in images:
        print('\t- {0}'.format(image.split('/')[-1]))

def get_vm_xml(instance_name):
    """Query virsh for the xml of an instance by name."""

    con = libvirt.openReadOnly('qemu:///system')
    try:
        domain = con.lookupByName(instance_name)

    except libvirt.libvirtError as e:
       return None

    result = domain.XMLDesc()

    return str(result)

def find_mac(xml_string):
    """Pass in a virsh xmldump and return a list of any mac addresses listed.
    Typically it will just be one.
    """

    xml_data = ET.fromstring(xml_string)

    macs = xml_data.findall("./devices/interface/mac")

    return macs

def find_ip_from_mac(mac):
    """Look through ``arp -an`` output for the IP of the provided MAC address.
    """

    arp_list = subprocess.check_output(["arp", "-an"]).split("\n")
    for entry in arp_list:
        if mac in entry:
            return entry.split()[1][1:-1]
