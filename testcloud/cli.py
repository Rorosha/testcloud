#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is the primary user entry point for testcloud
"""

import argparse
import logging
from time import sleep

from . import config
from . import image
from . import instance
from . import util
from .exceptions import DomainNotFoundError, TestcloudCliError

config_data = config.get_config()

log = logging.getLogger('libtestcloud')
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

description = """Testcloud is a small wrapper program designed to quickly and
simply boot images designed for cloud systems."""


################################################################################
# instance handling functions
################################################################################

def _list_instance(args):
    """Handler for 'list' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """
    instances = instance.list_instances()

    print("{:<40} {:<10}".format("Name", "State"))
    print("--------------------------------------------------")
    for inst in instances.keys():
        if args.all or instances[inst] == 'running':
            print("{:<40} {:<10}".format(inst, instances[inst]))

    print("")


def _create_instance(args):
    """Handler for 'instance create' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """

    log.debug("create instance")

    tc_image = image.Image(args.url)
    tc_image.prepare()

    existing_instance = instance.find_instance(args.name, tc_image)

    # can't create existing instances
    if existing_instance is not None:
        raise TestcloudCliError("A testcloud instance named {} already "
                                "exists at {}. Use 'testcloud instance start "
                                "{}' to start the instance or remove it before"
                                " re-creating ".format(args.name,
                                                       existing_instance.path,
                                                       args.name))

    else:
        tc_instance = instance.Instance(args.name, tc_image)

        # prepare instance
        tc_instance.prepare()

        # boot instance
        tc_instance.spawn_vm()

        # find vm ip
        vm_ip = find_vm_ip(args.name)
        print("The IP of vm {}:  {}".format(args.name, vm_ip))


def _start_instance(args):
    """Handler for 'instance start' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """
    log.debug("start instance: {}".format(args.name))

    tc_instance = instance.find_instance(args.name)

    if tc_instance is None:
        raise TestcloudCliError("Cannot start instance {} because it does "
                                "not exist".format(args.name))

    tc_instance.start()


def _stop_instance(args):
    """Handler for 'instance stop' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """
    log.debug("stop instance: {}".format(args.name))

    tc_instance = instance.find_instance(args.name)

    if tc_instance is None:
        raise TestcloudCliError("Cannot stop instance {} because it does "
                                "not exist".format(args.name))

    tc_instance.stop()


def _destroy_instance(args):
    """Handler for 'instance destroy' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """
    log.debug("destroy instance: {}".format(args.name))

    tc_instance = instance.find_instance(args.name)

    if tc_instance is None:
        raise TestcloudCliError("Cannot remove instance {} because it does "
                                "not exist".format(args.name))

    tc_instance.destroy()


################################################################################
# image handling functions
################################################################################
def _list_image(args):
    """Handler for 'image list' command. Does not expect anything else in args.

    :param args: args from argparser
    """
    log.debug("list images")
    images = image.list_images()
    print("Current Images:")
    for img in images:
        print("  {}".format(img))


def _destroy_image(args):
    """Handler for 'image destroy' command. Expects the following elements in args:
        * name(str)

    :param args: args from argparser
    """

    log.debug("destroying image {}".format(args.name))

    tc_image = image.find_image(args.name)

    if tc_image is None:
        log.error("image {} not found, cannot destroy".format(args.name))

    tc_image.destroy()


def get_argparser():
    parser = argparse.ArgumentParser(description=description)
    subparsers = parser.add_subparsers(title="Command Types",
                                       description="Types of commands available",
                                       help="<command> help")

    instarg = subparsers.add_parser("instance", help="help on instance options")
    instarg.add_argument("-c",
                         "--connection",
                         default="qemu:///system",
                         help="libvirt connection url to use")
    instarg_subp = instarg.add_subparsers(title="instance commands",
                                          description="Commands available for instance operations",
                                          help="<command> help")

    # instance list
    instarg_list = instarg_subp.add_parser("list", help="list instances")
    instarg_list.set_defaults(func=_list_instance)
    instarg_list.add_argument("--all",
                              help="list all instances, running and stopped",
                              action="store_true")

    # instance start
    instarg_start = instarg_subp.add_parser("start", help="start instance")
    instarg_start.add_argument("name",
                               help="name of instance to start")
    instarg_start.set_defaults(func=_start_instance)

    # instance stop
    instarg_stop = instarg_subp.add_parser("stop", help="stop instance")
    instarg_stop.add_argument("name",
                              help="name of instance to stop")
    instarg_stop.set_defaults(func=_stop_instance)

    # instance destroy
    instarg_destroy = instarg_subp.add_parser("destroy", help="destroy instance")
    instarg_destroy.add_argument("name",
                                 help="name of instance to destroy")
    instarg_destroy.set_defaults(func=_destroy_instance)

    # instance create
    instarg_create = instarg_subp.add_parser("create", help="create instance")
    instarg_create.set_defaults(func=_create_instance)
    instarg_create.add_argument("name",
                                help="name of instance to create")
    instarg_create.add_argument("--ram",
                                help="Specify the amount of ram for the VM.",
                                type=int,
                                default=512)
    instarg_create.add_argument("--no-graphic",
                                help="Turn off graphical display.",
                                action="store_true")
    instarg_create.add_argument("--vnc",
                                help="Turns on vnc at :1 to the instance.",
                                action="store_true")
    instarg_create.add_argument("--atomic",
                                help="Use this flag if you're booting an Atomic Host.",
                                action="store_true")
    # this might work better as a second, required positional arg
    instarg_create.add_argument("-u",
                                "--url",
                                help="URL to qcow2 image is required.",
                                type=str)

    imgarg = subparsers.add_parser("image", help="help on image options")
    imgarg_subp = imgarg.add_subparsers(title="subcommands",
                                        description="Types of commands available",
                                        help="<command> help")

    # image list
    imgarg_list = imgarg_subp.add_parser("list", help="list images")
    imgarg_list.set_defaults(func=_list_image)

    # image destroy
    imgarg_destroy = imgarg_subp.add_parser("destroy", help="destroy image")
    imgarg_destroy.add_argument("name",
                                help="name of image to destroy")
    imgarg_destroy.set_defaults(func=_destroy_image)

    return parser


def main():
    parser = get_argparser()
    args = parser.parse_args()

    args.func(args)


def find_vm_ip(name):
    """Finds the ip of a local vm given it's name used by libvirt.

    :param name: name of the VM (as used by libvirt)
    :returns: ip address of VM
    :rtype: str
    """

    log.info("Don't worry about these 'QEMU Driver' errors. libvirt is whiny " +
             "and has no method to shut it up...\n")

    for _ in xrange(100):
        vm_xml = util.get_vm_xml(name)
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

        if vm_ip:
            break

        sleep(.2)

    return vm_ip


if __name__ == '__main__':
    main()
