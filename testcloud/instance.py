#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
Representation of a Testcloud spawned (or to-be-spawned) virtual machine
"""

import os
import sys
import subprocess
import glob
import logging

import libvirt
import shutil

from . import config
from .exceptions import TestcloudInstanceError

config_data = config.get_config()

log = logging.getLogger('testcloud.instance')

# mapping libvirt constants to a known set of strings
DOMAIN_STATUS_ENUM = {libvirt.VIR_DOMAIN_NOSTATE: 'no state',
                      libvirt.VIR_DOMAIN_RUNNING: 'running',
                      libvirt.VIR_DOMAIN_BLOCKED: 'blocked',
                      libvirt.VIR_DOMAIN_PAUSED:  'paused',
                      libvirt.VIR_DOMAIN_SHUTDOWN: 'shutdown',
                      libvirt.VIR_DOMAIN_SHUTOFF: 'shutoff',
                      libvirt.VIR_DOMAIN_CRASHED: 'crashed',
                      libvirt.VIR_DOMAIN_PMSUSPENDED: 'suspended'
                      }


def _list_instances():
    """List existing instances currently known to testcloud

    :returns: list of instance names
    """

    instance_dir = '{}/instances'.format(config_data.DATA_DIR)
    return os.listdir(instance_dir)


def _list_system_domains(connection):
    """List known domains for a given hypervisor connection.

    :param connection: libvirt compatible hypervisor connection
    :returns: dictionary mapping of name:state
    :rtype: dict
    """

    domains = {}
    conn = libvirt.openReadOnly(connection)
    for domain in conn.listAllDomains():
        # the libvirt docs seem to indicate that the second int is for state
        # details, only used when state is ERROR, so only looking at the first
        # int returned for domain.state()

        domains[domain.name()] = DOMAIN_STATUS_ENUM[domain.state()[0]]

    return domains


def find_instance(name, image=None):
    """Find an instance using a given name and image, if it exists.

    :param name: name of instance to find
    :param image: :py:class:`testcloud.image.Image`
    :returns: :py:class:`Instance` if the instance exists, None if it doesn't
    """

    instances = _list_instances()
    for inst in instances:
        if name == inst:
            return Instance(name, image)
    return None


def list_instances(connection='qemu:///system'):
    """List instances known by testcloud and the state of each instance

    :param connection: libvirt compatible connection to use when listing domains
    :returns: dictionary of instance_name to domain_state mapping
    """
    system_domains = _list_system_domains(connection)
    all_instances = _list_instances()

    instances = {}
    for instance in all_instances:
        if instance not in all_instances:
            raise TestcloudInstanceError("instance {} exists in instances/ "
                                         "but is not a libvirt domain on "
                                         "{}".format(instance, connection))
        instances[instance] = system_domains[instance]

    return instances


class Instance(object):
    """Handles creating, starting, stopping and destroying virtual machines
    defined on the local system, using an existing :py:class:`Image`.
    """

    def __init__(self, name, image=None):
        self.name = name
        self.image = image
        self.path = "{}/instances/{}".format(config_data.DATA_DIR, self.name)
        self.seed_path = "{}/{}-seed.img".format(self.path, self.name)
        self.meta_path = "{}/meta".format(self.path)
        self.local_disk = "{}/{}-local.qcow2".format(self.path, self.name)

        self.ram = 512
        self.vnc = False
        self.graphics = False
        self.atomic = False
        self.seed = None
        self.kernel = None
        self.initrd = None

        # get rid of
        self.backing_store = image.local_path if image else None
        self.image_path = config_data.CACHE_DIR + self.name + ".qcow2"

    def prepare(self):
        """Create local directories and metadata needed to spawn the instance
        """
        # create the dirs needed for this instance
        self._create_dirs()

        # generate metadata
        self._create_user_data(config_data.PASSWORD)
        self._create_meta_data(config_data.HOSTNAME)

        # generate seed image
        self._generate_seed_image()

        # extract kernel and initrd
        self._extract_initrd_and_kernel()

        # deal with backing store
        self._create_local_disk()

    def _create_dirs(self):
        if not os.path.isdir(self.path):

            log.debug("Creating instance directories")
            os.makedirs(self.path)
            os.makedirs(self.meta_path)

    def _create_user_data(self, password, overwrite=False, atomic=False):
        """Save the right  password to the 'user-data' file needed to
        emulate cloud-init. Default username on cloud images is "fedora"

        Will not overwrite an existing user-data file unless
        the overwrite kwarg is set to True."""

        if atomic:
            file_data = config_data.ATOMIC_USER_DATA % password

        else:
            file_data = config_data.USER_DATA % password

        data_path = '{}/meta/user-data'.format(self.path)

        if (os.path.isfile(data_path) and overwrite) or not os.path.isfile(data_path):
            with open(data_path, 'w') as user_file:
                user_file.write(file_data)
            log.debug("Generated user-data for instance {}".format(self.name))
        else:
            log.debug("user-data file already exists for instance {}. Not"
                      " regerating.".format(self.name))

    def _create_meta_data(self, hostname, overwrite=False):
        """Save the required hostname data to the 'meta-data' file needed to
        emulate cloud-init.

        Will not overwrite an existing user-data file unless
        the overwrite kwarg is set to True."""

        file_data = config_data.META_DATA % hostname

        meta_path = "{}/meta-data".format(self.meta_path)
        if (os.path.isfile(meta_path) and overwrite) or not os.path.isfile(meta_path):
            with open(meta_path, 'w') as meta_data_file:
                meta_data_file.write(file_data)

            log.debug("Generated meta-data for instance {}".format(self.name))
        else:
            log.debug("meta-data file already exists for instance {}. Not"
                      " regerating.".format(self.name))

    def _generate_seed_image(self):
        """Create a virtual filesystem needed for boot with virt-make-fs on a
        given path (it should probably be somewhere in '/tmp'."""

        log.debug("creating seed image {}".format(self.seed_path))

        make_image = subprocess.call(['virt-make-fs',
                                      '--type=msdos',
                                      '--label=cidata',
                                      self.meta_path,
                                      self.seed_path])

        # Check the subprocess.call return value for success
        if make_image == 0:
            log.info("Seed image generated successfully")
        else:
            log.error("Seed image generation failed. Exiting")
            raise TestcloudInstanceError("Failure during seed image generation")

    def _extract_initrd_and_kernel(self):
        """Download the necessary kernel and initrd for booting a specified
        cloud image."""

        if self.image is None:
            raise TestcloudInstanceError("attempted to access image "
                                         "information for instance {} but "
                                         "that information was not supplied "
                                         "at creation time".format(self.name))

        log.info("extracting kernel and initrd from {}".format(self.image.local_path))
        subprocess.call(['virt-builder', '--get-kernel',
                         self.image.local_path],
                        cwd=self.path)

        self.kernel = glob.glob("%s/*vmlinuz*" % self.path)[0]
        self.initrd = glob.glob("%s/*initramfs*" % self.path)[0]

        if self.kernel is None or self.initrd is None:
            raise IndexError("Unable to find kernel or initrd, did they " +
                             "download?")
            sys.exit(1)

    def _create_local_disk(self):
        """Create a instance using the backing store provided by Image."""

        if self.image is None:
            raise TestcloudInstanceError("attempted to access image "
                                         "information for instance {} but "
                                         "that information was not supplied "
                                         "at creation time".format(self.name))

        subprocess.call(['qemu-img',
                         'create',
                         '-f',
                         'qcow2',
                         '-b',
                         self.image.local_path,
                         self.local_disk
                         ])

    def spawn_vm(self):
        """Create and boot the instance, using prepared data."""

        boot_args = ['/usr/bin/virt-install',
                     '--connect',
                     'qemu:///system',
                     '--import',
                     '-n',
                     self.name,
                     '-r',
                     str(self.ram),
                     '--os-type=linux',  # This should be configurable later
                     '--disk',
                     '{},device=disk,bus=virtio,format=qcow2'.format(
                         self.local_disk),
                     '--disk',
                     '{},device=disk,bus=virtio'.format(self.seed_path),
                     ]

        # Extend with the customizations from the config_data file
        boot_args.extend(config_data.CMD_LINE_ARGS)

        if self.graphics:
            boot_args.extend(['--noautoconsole'])

        if self.vnc:
            boot_args.extend(['-vnc', '0.0.0.0:1'])

        vm = subprocess.Popen(boot_args)

        log.info("Successfully booted your local cloud image!")
        log.info("PID: %d" % vm.pid)

        return vm

    def expand_qcow(self, size="+10G"):
        """Expand the storage for a qcow image. Currently only used for Atomic
        Hosts."""

        log.info("expanding qcow2 image {}".format(self.image_path))
        subprocess.call(['qemu-img',
                         'resize',
                         self.image_path,
                         size])

        log.info("Resized image for Atomic testing...")
        return

    def set_seed(self, path):
        """Set the seed image for the instance."""
        self.seed = path

    def boot(self):
        """Boot an already spawned instance."""

        subprocess.Popen(['virsh',
                          'start',
                          self.name
                          ])

    def _destroy_virsh_instance(self):
        """Remove an instance from virsh."""

        for cmd in ['destroy', 'undefine']:
            subprocess.Popen(['virsh',
                              cmd,
                              self.name
                              ])

    def _run_virsh_command(self, command):
        subprocess.Popen(['virsh',
                          '-c',
                          'qemu:///system',
                          command,
                          self.name
                          ])

    def start(self):
        """Start the instance"""

        log.debug("starting instance {} with virsh".format(self.name))

        # stop (destroy) the vm using virsh
        self._run_virsh_command('start')

    def stop(self):
        """Stop the instance"""

        log.debug("stopping instance {} with virsh".format(self.name))

        # stop (destroy) the vm using virsh
        self._run_virsh_command('destroy')

    def destroy(self):
        """Destroy an already stopped instance

        :raises TestcloudInstanceError: if the image does not exist or is still
                                        running
        """

        log.debug("removing instance {} from libvirt with "
                  "virsh".format(self.name))

        # this should be changed if/when we start supporting configurable
        # libvirt connections
        system_domains = _list_system_domains("qemu:///system")
        if self.name in system_domains and \
                system_domains[self.name] == 'running':

            raise TestcloudInstanceError("Cannot remove running instance {}. "
                                         "Please stop the instance before "
                                         "removing.".format(self.name))

        # remove from virsh, assuming that it's stopped already
        self._run_virsh_command('undefine')

        log.debug("removing instance {} from disk".format(self.path))

        # remove from disk
        shutil.rmtree(self.path)
