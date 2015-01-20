#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is the main script for running testCloud.
"""

import os
from time import sleep
import libvirt

from . import config
from . import util
from . import libtestcloud as libtc

config_data = config.get_config()

def install(
    image_url, instance_name, ram=512, graphics=False, vnc=False, atomic=False,
        pristine=False):
    """Run through all the steps."""

    print("Cleaning dirs...")
    util.clean_dirs()
    util.create_dirs()

    base_path = config_data.LOCAL_DOWNLOAD_DIR + '/testCloud'

    # Create the data cloud-init needs
    print("Creating meta-data...")
    util.create_user_data(base_path, config_data.PASSWORD, atomic=atomic)
    util.create_meta_data(base_path, config_data.HOSTNAME)

    # Instantiate the image and the instance from the image

    image = libtc.Image(image_url)

    vm = libtc.Instance(instance_name, image)

    # Set all the instance attributes passed from the cmdline
    vm.ram = ram
    vm.vnc = vnc
    vm.graphics = graphics
    vm.atomic = atomic

    vm.create_seed_image(base_path + '/meta', base_path)

    if not os.path.isfile(config_data.PRISTINE + vm.image):
        print("downloading new image...")
        image.download()
        image.load_pristine()

    else:
        print("Using existing image...")
        if not os.path.isfile(config_data.LOCAL_DOWNLOAD_DIR + image.name):
            image.load_pristine()
        if pristine:
            print("Copying from pristine image...")

            # Remove existing image if it exists
            if os.path.exists(config_data.LOCAL_DOWNLOAD_DIR + image.name):
                os.remove(config_data.LOCAL_DOWNLOAD_DIR + image.name)

            image.load_pristine()

    # Determine if we want to grow the disk. Currently we only do this if the
    # instance to be booted is a fresh Atomic image.

    expand_disk = False

    if atomic and pristine:
        expand_disk = True

    vm.create_instance()
    vm.spawn(expand_disk=expand_disk)


    return vm


def main():
    import argparse

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
    args = parser.parse_args()

    install(args.url,
            args.name,
            args.ram,
            graphics=args.no_graphic,
            vnc=args.vnc,
            atomic=args.atomic,
            pristine=args.pristine)

    #  It takes a bit for the instance to get registered in virsh,
    #  so here we keep asking for the domain we created until virsh
    #  finally decides to cough up the information.

    for _ in xrange(100):
        try:
            vm_xml = util.get_vm_xml(args.name)
            break

        except libvirt.libvirtError as e:
            if "Domain not found" not in str(e):
            sleep(.5)
    else:
        raise

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
