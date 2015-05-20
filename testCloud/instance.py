#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is a module for downloading fedora cloud images (and probably any other
qcow2) and then booting them locally with qemu.
"""

import os
import sys
import subprocess
import glob
import logging

from . import config
from .exceptions import TestCloudInstanceError

config_data = config.get_config()

log = logging.getLogger('testCloud.instance')

def find(name, image):
    instance_dir = '{}/instances'.format(config_data.DATA_DIR)
    instances = os.listdir(instance_dir)

    for inst in instances:
        if name == inst:
            return os.path.join(instance_dir, inst)

    return None

class Instance(object):
    """The Instance class handles the creation, location and customization
    of existing testCloud instances (which are qcow2 backed from an Image)"""

    def __init__(self, name, image):
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
        self.backing_store = image.local_path
        self.image_path = config_data.CACHE_DIR + self.name + ".qcow2"

    def prepare(self):
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
            log.debug("user-data file already exists for instance {}. Not"\
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
            log.debug("meta-data file already exists for instance {}. Not"\
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
            raise TestCloudInstanceError("Failure during seed image generation")

    def _extract_initrd_and_kernel(self):
        """Download the necessary kernel and initrd for booting a specified
        cloud image."""

        # still need to figure out if the image needs to be copied from
        # cache for each instance
        # for now, assuming that it doesn't

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

        subprocess.call(['qemu-img',
                         'create',
                         '-f',
                         'qcow2',
                         '-b',
                         self.image.local_path,
                         self.local_disk
                         ])


    def spawn_vm(self, expand_disk=False):
        """Boot the cloud image redirecting local port 8888 to 80 on the vm as
        well as local port 2222 to 22 on the vm so http and ssh can be
        accessed.

        Pass True to expand_disk if booting a fresh atomic image or you want to
        grow the disk size for some other reason at boot.

        """

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

#        if expand_disk:
#            self.expand_qcow()
#
#        if not self.atomic:
#            self.download_initrd_and_kernel()
#
#            boot_args.extend(['--boot',
#                              'kernel={0},initrd={1},kernel_args={2}'.format(
#                                  self.kernel,
#                                  self.initrd,
#                                  '"root=/dev/vda1 ro ds=nocloud-net"'),
#                              ])
#
        if self.graphics:
            boot_args.extend(['--noautoconsole'])

        if self.vnc:
            boot_args.extend(['-vnc', '0.0.0.0:1'])

        vm = subprocess.Popen(boot_args)

        log.info("Successfully booted your local cloud image!")
        log.info("PID: %d" % vm.pid)

        return vm



    def exists(self):
        """Check to see if this instance already exists."""

        pass

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

    def selfdestruct(self):
        """Remove an instance from virsh."""

        for cmd in ['destroy', 'undefine']:
            subprocess.Popen(['virsh',
                              cmd,
                              self.name
                              ])

