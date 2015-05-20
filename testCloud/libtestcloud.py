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
import pwd
import re
import shutil
import logging

import requests

from testCloud.exceptions import TestCloudImageError

config_data = config.get_config()

log = logging.getLogger('libtestcloud')
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Image(object):
    """Handles base cloud images and prepares them for boot. This includes
    downloading images from remote systems (http, https supported) or copying
    from mounted local filesystems.
    """

    def __init__(self, uri):
        """Create a new Image object for TestCloud

        :param uri: URI for the image to be represented. this URI must be of a
            supported type (http, https, file)
        :raises TaskotronImageError: if the URI is not of a supported type or cannot be parsed
        """

        self.uri = uri

        uri_data = self._process_uri(uri)

        self.name = uri_data['name']
        self.uri_type = uri_data['type']

        if self.uri_type == 'file':
            self.remote_path = uri_data['path']
        else:
            self.remote_path = uri

        self.local_path = config_data.PRISTINE + self.name

    def _process_uri(self, uri):
        """Process the URI given to find the type, path and imagename contained
        in that URI.

        :param uri: string URI to be processed
        :return: dictionary containing 'type', 'name' and 'path'
        :raise TestCloudImageError: if the URI is invalid or uses an unsupported transport
        """

        type_match = re.search(r'(http|https|file)://([\w\.\-/]+)', uri)

        if not type_match:
            raise TestCloudImageError('invalid uri: only http, https and file uris are supported: {}'.format(uri))

        uri_type = type_match.group(1)
        uri_path = type_match.group(2)

        name_match = re.findall('([\w\.\-]+)', uri)

        if not name_match:
            raise TestCloudImageError('invalid uri: could not find image name: {}'.format(uri))

        image_name = name_match[-1]
        return {'type': uri_type, 'name': image_name, 'path': uri_path}


    def _download_remote_image(self, remote_url, local_path):
        """Download a remote image to the local system, outputting download
        progress as it's downloaded.

        :param remote_url: URL of the image
        :param local_path: local path (including filename) that the image
            will be downloaded to
        """

        u = requests.get(remote_url, stream=True)

        try:
            with open(local_path + ".part", 'wb') as f:
                file_size = int(u.headers['content-length'])

                log.info("Downloading {0} ({1} bytes)".format(self.name, file_size))
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
                        #  Rename the file since download has completed
                        os.rename(local_path + ".part", local_path)
                        log.info("Succeeded at downloading {0}".format(self.name))
                        break

        except OSError:
            log.error("Problem writing to {}.".format(config_data.PRISTINE))

    def _handle_file_url(self, source_path, dest_path):
        if not os.path.exists(dest_path):
            shutil.copy(source_path, dest_path)


    def _adjust_image_selinux(self, image_path):
        """If SElinux is enabled on the system, change the context of that image
        file such that libguestfs and qemu can use it.

        :param image_path: path to the image to change the context of
        """

        selinux_active = subprocess.call(['selinuxenabled'])

        if selinux_active != 0:
            log.debug('SELinux not enabled, not changing context of'
                      'image {}'.format(image_path))
            return

        image_context = subprocess.call(['chcon',
                                         '-u', 'system_u',
                                         '-t', 'virt_content_t',
                                         image_path])
        if image_context == 0:
            log.debug('successfully changed SELinux context for '
                      'image {}'.format(image_path))
        else:
            log.error('Error while changing SELinux context on '
                      'image {}'.format(image_path))


    def prepare(self):
        """Prepare the image for local use by either downloading the image from
        a remote location or copying it into the image cache from a locally
        mounted filesystem"""

        # Create the proper local upload directory if it doesn't exist.
        if not os.path.exists(config_data.PRISTINE):
            os.makedirs(config_data.PRISTINE)

        log.debug("Local downloads will be stored in {}.".format(
            config_data.PRISTINE))

        if self.uri_type == 'file':
            self._handle_file_url(self.remote_path, self.local_path)
        else:
            self._download_remote_image(self.remote_path, self.local_path)

        self._adjust_image_selinux(self.local_path)

        return self.local_path

    def save_pristine(self):
        """Save a copy of the downloaded image to the config_dataured PRISTINE dir.
        Only call this after an image has been downloaded.
        """

        subprocess.call(['cp',
                        self.local_path,
                        config_data.PRISTINE])

        log.debug('Copied fresh image to {0}...'.format(config_data.PRISTINE))

    def load_pristine(self):
        """Load a pristine image to /tmp instead of downloading.
        """
        subprocess.call(['cp',
                         config_data.PRISTINE + self.name,
                         config_data.LOCAL_DOWNLOAD_DIR])

        log.debug('Copied fresh image to {} ...'.format(config_data.LOCAL_DOWNLOAD_DIR))


class Instance(object):
    """The Instance class handles the creation, location and customization
    of existing testCloud instances (which are qcow2 backed from an Image)"""

    def __init__(self, name, image):
        self.name = name
        self.image = image.name
        self.backing_store = image.local_path
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

        # Ensure correct permissions on the instance qcow2.
        log.info("Ensuring the instance qcow2 has correct permissions...")

        qemu = pwd.getpwnam('qemu')

        os.chown(self.image_path, qemu.pw_uid, qemu.pw_gid)


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

        log.info("Resized image for Atomic testing...")
        return

    def create_seed_image(self, meta_path, img_path):
        """Create a virtual filesystem needed for boot with virt-make-fs on a
        given path (it should probably be somewhere in '/tmp'."""

        make_image = subprocess.call(['virt-make-fs',
                                      '--type=msdos',
                                      '--label=cidata',
                                      meta_path,
                                      img_path + '/{}-seed.img'.format(self.name)])

        # Check the subprocess.call return value for success
        if make_image == 0:
            self.set_seed(img_path + '/{}-seed.img'.format(self.name))
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
                     '--import',
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
                              ])

        if self.graphics:
            boot_args.extend(['--noautoconsole'])

        if self.vnc:
            boot_args.extend(['-vnc', '0.0.0.0:1'])

        vm = subprocess.Popen(boot_args)

        log.info("Successfully booted your local cloud image!")
        log.info("PID: %d" % vm.pid)

        return vm

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

class DomainNotFoundError(BaseException):
    """Exception to raise if the queried domain can't be found."""

    def __init__(self):
        self.value = "Could not find the requested virsh domain, did it register?"

    def __str__(self):
        return repr(self.value)
