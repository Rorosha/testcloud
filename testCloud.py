#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is the main script for running testCloud.
"""

import os

import config
import util
import libtestcloud as libtc


def run(
    image_url, ram=512, graphics=False, vnc=False, atomic=False,
        pristine=False):
    """Run through all the steps."""

    print "Cleaning dirs..."
    util.clean_dirs()
    util.create_dirs()

    base_path = '/tmp/testCloud'

    # Create the data cloud-init needs
    print "Creating meta-data..."
    util.create_user_data(base_path, "passw0rd", atomic=atomic)
    util.create_meta_data(base_path, "testcloud")

    # Instantiate the image and the instance from the image

    image = libtc.Image(image_url)

    vm = libtc.Instance(image)

    # Set all the instance attributes passed from the cmdline
    vm.ram = ram
    vm.vnc = vnc
    vm.graphics = graphics
    vm.atomic = atomic

    vm.create_seed_image(base_path + '/meta', base_path)

    if not os.path.isfile(config.PRISTINE + vm.image):
        print "downloading new image..."
        image.download()

        print "Copying pristine image from {0}...".format(config.PRISTINE)
        print config.PRISTINE + vm.image
        image.save_pristine()

    else:
        print "Using existing image..."
        if not os.path.isfile(image.path):
            image.load_pristine()
        if pristine:
            print "Copying from pristine image..."

        # Remove existing image from /tmp if it exists
        if os.path.exists(image.path):
            os.remove(image.path)

        image.load_pristine()

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
    args = parser.parse_args()

    gfx = False
    vnc = False
    atomic = False
    pristine = False

    if args.no_graphic:
        gfx = True

    if args.vnc:
        vnc = True

    if args.atomic:
        atomic = True

    if args.pristine:
        pristine = True

    run(args.url,
        args.ram,
        graphics=gfx,
        vnc=vnc,
        atomic=atomic,
        pristine=pristine)

if __name__ == '__main__':
    main()
