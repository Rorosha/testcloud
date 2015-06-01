#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is the primary user entry point for testCloud
"""

import argparse
import logging

from . import config
from . import image
from . import instance

# these are used in commented out code, may be reactivated
#import os
from time import sleep
from . import util
#import libvirt
from .exceptions import DomainNotFoundError

config_data = config.get_config()

log = logging.getLogger('libtestcloud')
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("url",
                        help="URL to qcow2 image is required.",
                        type=str)
    parser.add_argument("--ram",
                        help="Specify the amount of ram for the VM.",
                        type=int,
                        default=512)
    parser.add_argument("--no-graphic",
                        help="Turn off graphical display.",
                        action="store_true")
    parser.add_argument("--vnc",
                        help="Turns on vnc at :1 to the instance.",
                        action="store_true")
    parser.add_argument("--atomic",
                        help="Use this flag if you're booting an Atomic Host.",
                        action="store_true")
    parser.add_argument("--pristine",
                        help="Use a clean copy of an image.",
                        action="store_true")
    parser.add_argument("--name",
                        help="A unique name to use for your instance.",
                        default='testCloud')

    return parser

def main():
    parser = get_argparser()
    args = parser.parse_args()

    # get/find image
    # look for existing instance
    # if not exist:
    #   prepare metadata
    #   boot vm

    tc_image = image.Image(args.url)
    tc_image.prepare()

    instance_path = instance.find(args.name, tc_image.name)

    # for the moment, rebooting existing instances is noworky, so blow up early
    if instance_path is not None:
        raise NotImplementedError("testCloud does not yet support booting " \
                                  "existing instances. Please remove {} before"\
                                  " continuing".format(instance_path))

    else:
        tc_instance = instance.Instance(args.name, tc_image)

        # prepare instance
        tc_instance.prepare()

        # boot instance
        tc_instance.spawn_vm()

    # look for data about instance (mac, IP, etc.)

#    install(args.url,
#            args.name,
#            args.ram,
#            graphics=args.no_graphic,
#            vnc=args.vnc,
#            atomic=args.atomic,
#            pristine=args.pristine)
#
    #  It takes a bit for the instance to get registered in virsh,
    #  so here we keep asking for the domain we created until virsh
    #  finally decides to cough up the information.

    log.info("Don't worry about these 'QEMU Driver' errors. libvirt is whiny " + \
          "and has no method to shut it up...\n")

    for _ in xrange(100):
        vm_xml = util.get_vm_xml(args.name)
        if vm_xml is not None:
            break

        else:
            sleep(.2)
    else:
        raise DomainNotFoundError

    vm_mac = util.find_mac(vm_xml)
    vm_mac = vm_mac[0]

    #  The arp cache takes some time to populate, so this keeps looking
    #  for the entry until it shows up.

    for _ in xrange(100):
        vm_ip = util.find_ip_from_mac(vm_mac.attrib['address'])

        if vm_ip: break
        sleep(.2)

    print("The IP of your VM is: {}".format(vm_ip))


if __name__ == '__main__':
    main()
