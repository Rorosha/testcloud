#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014, Red Hat, Inc.
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
import config
import urllib2


class Image(object):
    """The Image class handles the download, storage and retrieval of
    cloud images."""

    def __init__(self, url):
        self.url = url
        self.name = url.split('/')[-1]
        self.path = config.LOCAL_DOWNLOAD_DIR + self.name

    def download(self):
        """ Downloads files (qcow2s, specifically) from a list of URLs with an
        optional progress bar. Returns a list of raw image files. """

        # This code was blatantly stolen from fedimg - but it was depreciated,
        # that's the internet version of sitting in front of someone's house
        # with a sign saying "FREE." Thanks oddshocks!

        # Create the proper local upload directory if it doesn't exist.
        if not os.path.exists(config.LOCAL_DOWNLOAD_DIR):
            os.makedirs(config.LOCAL_DOWNLOAD_DIR)

        print "Local downloads will be stored in {}.".format(
            config.LOCAL_DOWNLOAD_DIR)

        # When qcow2s are downloaded and converted, they are added here
        raw_files = list()

        urls = []
        urls.append(self.url)

        for url in list(urls):
            file_name = url.split('/')[-1]
        local_file_name = config.LOCAL_DOWNLOAD_DIR + file_name
        u = urllib2.urlopen(url)

        try:
            with open(local_file_name, 'wb') as f:
                meta = u.info()
                file_size = int(meta.getheaders("Content-Length")[0])

                print "Downloading {0} ({1} bytes)".format(url, file_size)
                bytes_downloaded = 0
                block_size = 8192

                while True:
                    buff = u.read(block_size)  # buffer
                    if not buff:

                        raw_files.append(local_file_name)

                        print "Succeeded at downloading {0}".format(file_name)
                        break

                    bytes_downloaded += len(buff)
                    f.write(buff)
                    bytes_remaining = float(bytes_downloaded) / file_size
                    if config.DOWNLOAD_PROGRESS:
                        # TODO: Improve this progress indicator by making
                        # it more readable and user-friendly.
                        status = r"{0} [{1:.2%}]".format(bytes_downloaded,
                                                         bytes_remaining)
                        status = status + chr(8) * (len(status) + 1)
                        sys.stdout.write(status)

        except OSError:
            print "Problem writing to {}.".format(config.LOCAL_DOWNLOAD_DIR)

    def save_pristine(self):
        """Save a copy of the downloaded image to the configured PRISTINE dir.
        Only call this after an image has been downloaded.
        """

        subprocess.call(['cp',
                        self.path,
                        config.PRISTINE])

        print 'Copied fresh image to {0}...'.format(config.PRISTINE)

    def load_pristine(self):
        """Load a pristine image to /tmp instead of downloading.
        """
        subprocess.call(['cp',
                         config.PRISTINE + self.name,
                         config.LOCAL_DOWNLOAD_DIR])

        print 'Copied fresh image to {} ...'.format(config.LOCAL_DOWNLOAD_DIR)


class Instance(object):
    """The Instance class handles the creation, location and customization
    of existing testCloud instances (which are qcow2 backed from an Image)"""

    def __init__(self, image):
        self.image = image.name
        self.image_path = image.path
        self.ram = 512
        self.vnc = False
        self.graphics = False
        self.atomic = False
        self.seed = None
        self.kernel = None
        self.initrd = None

    def expand_qcow(self, size="+10G"):
        """Expand the storage for a qcow image. Currently only used for Atomic
        Hosts."""

        subprocess.call(['qemu-img',
                         'resize',
                         self.image_path,
                         size])

        print "Resized image for Atomic testing..."
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

    def download_initrd_and_kernel(self, path=config.LOCAL_DOWNLOAD_DIR):
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

    def boot(self):
        """Boot the cloud image redirecting local port 8888 to 80 on the vm as
        well as local port 2222 to 22 on the vm so http and ssh can be
        accessed.
        """

        boot_args = ['/usr/bin/qemu-kvm',
                     '-m',
                     str(self.ram),
                     '-drive',
                     'file=%s,if=virtio' % self.image_path,
                     '-drive',
                     'file=%s,if=virtio' % self.seed,
                     ]

        # Extend with the customizations from the config file
        boot_args.extend(config.CMD_LINE_ARGS)

        if self.atomic:
            self.expand_qcow()

        if not self.atomic:
            boot_args.extend(['-kernel',
                              '%s' % self.kernel,
                              '-initrd',
                              '%s' % self.initrd,
                              '-append',  # cloud-init needs these two lines
                              'root=/dev/vda1 ro ds=nocloud-net',
                              ])

        if self.graphics:
            boot_args.extend(['-nographic'])

        if self.vnc:
            boot_args.extend(['-vnc', '0.0.0.0:1'])

        vm = subprocess.Popen(boot_args)

        print "Successfully booted your local cloud image!"
        print "PID: %d" % vm.pid

        return vm
