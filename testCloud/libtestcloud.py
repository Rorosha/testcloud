#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015, Red Hat, Inc.
# License: GPL-2.0+ <http://spdx.org/licenses/GPL-2.0+>
# See the LICENSE file for more details on Licensing

"""
This is a module for downloading fedora cloud images (and probably any other
qcow2) and then booting them locally with qemu.
"""

import sys
import os
import subprocess
import glob
from . import config

import requests

config_data = config.get_config()

class Image(object):
    """The Image class handles the download, storage and retrieval of
    cloud images."""

    def __init__(self, url):
        self.url = url
        self.name = url.split('/')[-1]
        self.path = config_data.PRISTINE + self.name

    def download(self):
        """ Downloads files (qcow2s, specifically) from a list of URLs with an
        optional progress bar. Returns a list of raw image files. """

        # Create the proper local upload directory if it doesn't exist.
        if not os.path.exists(config_data.PRISTINE):
            os.makedirs(config_data.PRISTINE)

        print("Local downloads will be stored in {}.".format(
            config_data.PRISTINE))

        u = requests.get(self.url, stream=True)

        try:
            with open(self.path, 'wb') as f:
                file_size = int(u.headers['Content-Length'])

                print("Downloading {0} ({1} bytes)".format(self.name, file_size))
                bytes_downloaded = 0
                block_size = 4096

                while True:

                    try:

                        for data in u.iter_content(block_size):

                            bytes_downloaded += len(data)
                            f.write(data)
                            bytes_remaining = float(bytes_downloaded) / file_size
                            if config_data.DOWNLOAD_PROGRESS:
                                # TODO: Improve this progress indicator by making
                                # it more readable and user-friendly.
                                status = r"{0}/{1} [{2:.2%}]".format(bytes_downloaded,
                                                                     file_size,
                                                                     bytes_remaining)
                                status = status + chr(8) * (len(status) + 1)
                                sys.stdout.write(status)

                    except TypeError:
                        print("Succeeded at downloading {0}".format(self.name))
                        break

        except OSError:
            print("Problem writing to {}.".format(config_data.PRISTINE))

    def save_pristine(self):
        """Save a copy of the downloaded image to the config_dataured PRISTINE dir.
        Only call this after an image has been downloaded.
        """

        subprocess.call(['cp',
                        self.path,
                        config_data.PRISTINE])

        print('Copied fresh image to {0}...'.format(config_data.PRISTINE))

    def load_pristine(self):
        """Load a pristine image to /tmp instead of downloading.
        """
        subprocess.call(['cp',
                         config_data.PRISTINE + self.name,
                         config_data.LOCAL_DOWNLOAD_DIR])

        print('Copied fresh image to {} ...'.format(config_data.LOCAL_DOWNLOAD_DIR))


class Instance(object):
    """The Instance class handles the creation, location and customization
    of existing testCloud instances (which are qcow2 backed from an Image)"""

    def __init__(self, name, image):
        self.name = name
        self.image = image.name
        self.backing_store = image.path
        self.image_path = config_data.LOCAL_DOWNLOAD_DIR + self.name + \
                ".qcow2"
        self.ram = 512
        self.vnc = False
        self.graphics = False
        self.atomic = False
        self.seed = None
        self.kernel = None
        self.initrd = None

    def create_instance(self):
        """Create a instance using the backing store provided by Image."""

        subprocess.call(['qemu-img',
                         'create',
                         '-f',
                         'qcow2',
                         '-b',
                         self.backing_store,
                         self.image_path
                         ])

    def exists(self):
        """Check to see if this instance already exists."""

        pass

    def expand_qcow(self, size="+10G"):
        """Expand the storage for a qcow image. Currently only used for Atomic
        Hosts."""

        subprocess.call(['qemu-img',
                         'resize',
                         self.image_path,
                         size])

        print("Resized image for Atomic testing...")
        return

    def create_seed_image(self, meta_path, img_path):
        """Create a virtual filesystem needed for boot with virt-make-fs on a
        given path (it should probably be somewhere in '/tmp'."""

        make_image = subprocess.call(['virt-make-fs',
                                      '--type=msdos',
                                      '--label=cidata',
                                      meta_path,
                                      img_path + '/seed.img'])

        # Check the subprocess.call return value for success
        if make_image == 0:
            self.set_seed(img_path + '/seed.img')
            return "seed.img created at %s" % img_path

        return "creation of the seed.img failed."

    def set_seed(self, path):
        """Set the seed image for the instance."""
        self.seed = path

    def download_initrd_and_kernel(self, path=config_data.LOCAL_DOWNLOAD_DIR):
        """Download the necessary kernel and initrd for booting a specified
        cloud image."""

        subprocess.call(['virt-builder', '--get-kernel',
                         self.image_path],
                        cwd=path)

        self.kernel = glob.glob("%s/*vmlinuz*" % path)[0]
        self.initrd = glob.glob("%s/*initramfs*" % path)[0]

        if self.kernel is None or self.initrd is None:
            raise IndexError("Unable to find kernel or initrd, did they " +
                             "download?")
            sys.exit(1)

    def spawn(self, expand_disk=False):
        """Boot the cloud image redirecting local port 8888 to 80 on the vm as
        well as local port 2222 to 22 on the vm so http and ssh can be
        accessed.

        Pass True to expand_disk if booting a fresh atomic image or you want to
        grow the disk size for some other reason at boot.

        """

        boot_args = ['/usr/bin/virt-install',
                     '-n',
                     self.name,
                     '-r',
                     str(self.ram),
                     '--os-type=linux',  # This should be configurable later
                     '--disk',
                     '{},device=disk,bus=virtio,format=qcow2'.format(
                         self.image_path),
                     '--disk',
                     '{},device=disk,bus=virtio'.format(self.seed),
                     ]

        # Extend with the customizations from the config_data file
        boot_args.extend(config_data.CMD_LINE_ARGS)

        if expand_disk:
            self.expand_qcow()

        if not self.atomic:
            self.download_initrd_and_kernel()

            boot_args.extend(['--boot',
                              'kernel={0},initrd={1},kernel_args={2}'.format(
                                  self.kernel,
                                  self.initrd,
                                  '"root=/dev/vda1 ro ds=nocloud-net"'),
                              '--import',
                              '--noautoconsole'
                              ])

        if self.graphics:
            boot_args.extend(['-nographic'])

        if self.vnc:
            boot_args.extend(['-vnc', '0.0.0.0:1'])

        vm = subprocess.Popen(boot_args)

        print("Successfully booted your local cloud image!")
        print("PID: %d" % vm.pid)

        return vm

    def boot(self):
        """Boot an already spawned instance."""

        subprocess.Popen(['virsh',
                          'start',
                          self.name
                          ])
