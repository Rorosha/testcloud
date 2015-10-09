#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This module contains helper functions for testcloud.
"""

import subprocess
import logging

import random
import libvirt
import xml.etree.ElementTree as ET

from . import config

log = logging.getLogger('testcloud.util')
config_data = config.get_config()


def get_vm_xml(instance_name):
    """Query virsh for the xml of an instance by name."""

    con = libvirt.openReadOnly('qemu:///system')
    try:
        domain = con.lookupByName(instance_name)

    except libvirt.libvirtError:
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


def generate_mac_address():
    """Create a workable mac address for our instances."""

    hex_mac = [0x52, 0x54, 0x00]  # These 3 are the prefix libvirt uses
    hex_mac += [random.randint(0x00, 0xff) for x in range(3)]
    mac = ':'.join(hex(x)[2:] for x in hex_mac)

    return mac
