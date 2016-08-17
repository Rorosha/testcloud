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
import time

import libvirt
import shutil
import uuid
import jinja2

from . import config
from . import util
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

    :returns: dict of instance names and their ip address
    """

    instance_list = []

    instance_dir = os.listdir('{}/instances'.format(config_data.DATA_DIR))
    for dir in instance_dir:
        instance_details = {}
        instance_details['name'] = dir
        try:
            with open("{}/instances/{}/ip".format(config_data.DATA_DIR, dir), 'r') as inst:
                instance_details['ip'] = inst.readline().strip()

        except IOError:
            instance_details['ip'] = None

        instance_list.append(instance_details)

    return instance_list


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
        if inst['name'] == name:
            return Instance(name, image)
    return None


def list_instances(connection='qemu:///system'):
    """List instances known by testcloud and the state of each instance

    :param connection: libvirt compatible connection to use when listing domains
    :returns: dictionary of instance_name to domain_state mapping
    """
    system_domains = _list_system_domains(connection)
    all_instances = _list_instances()

    instances = []

    for instance in all_instances:
        if instance['name'] not in system_domains.keys():
            log.warn('{} is not registered, might want to delete it.'.format(instance['name']))
            instance['state'] = 'de-sync'

            instances.append(instance)

        else:

            # Add the state of the instance
            instance['state'] = system_domains[instance['name']]

            instances.append(instance)

    return instances


class Instance(object):
    """Handles creating, starting, stopping and removing virtual machines
    defined on the local system, using an existing :py:class:`Image`.
    """

    def __init__(self, name, image=None, hostname=None):
        self.name = name
        self.image = image
        self.path = "{}/instances/{}".format(config_data.DATA_DIR, self.name)
        self.seed_path = "{}/{}-seed.img".format(self.path, self.name)
        self.meta_path = "{}/meta".format(self.path)
        self.local_disk = "{}/{}-local.qcow2".format(self.path, self.name)
        self.xml_path = "{}/{}-domain.xml".format(self.path, self.name)

        self.ram = config_data.RAM
        # desired size of disk, in GiB
        self.disk_size = config_data.DISK_SIZE
        self.vnc = False
        self.graphics = False
        self.atomic = False
        self.seed = None
        self.kernel = None
        self.initrd = None
        self.hostname = hostname if hostname else config_data.HOSTNAME

        # get rid of
        self.backing_store = image.local_path if image else None
        self.image_path = config_data.STORE_DIR + self.name + ".qcow2"

    def prepare(self):
        """Create local directories and metadata needed to spawn the instance
        """
        # create the dirs needed for this instance
        self._create_dirs()

        # generate metadata
        self._create_user_data(config_data.PASSWORD)
        self._create_meta_data(self.hostname)

        # generate seed image
        self._generate_seed_image()

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

        imgcreate_command = ['qemu-img',
                             'create',
                             '-f',
                             'qcow2',
                             '-b',
                             self.image.local_path,
                             self.local_disk,
                             ]

        # make sure to expand the resultant disk if the size is set
        if self.disk_size > 0:
            imgcreate_command.append("{}G".format(self.disk_size))

        subprocess.call(imgcreate_command)

    def _get_domain(self, hypervisor="qemu:///system"):
        """Create the connection to libvirt to control instance lifecycle.
        returns: libvirt domain object"""
        conn = libvirt.open(hypervisor)
        return conn.lookupByName(self.name)

    def create_ip_file(self, ip):
        """Write the ip address found after instance creation to a file
           for easier management later. This is likely going to break
           and need a better solution."""

        with open("{}/instances/{}/ip".format(config_data.DATA_DIR,
                                              self.name), 'w') as ip_file:
            ip_file.write(ip)

    def write_domain_xml(self):
        """Load the default xml template, and populate it with the following:
         - name
         - uuid
         - locations of disks
         - network mac address
        """

        # Set up the jinja environment
        jinjaLoader = jinja2.FileSystemLoader(searchpath=[config.DEFAULT_CONF_DIR,
                                                          config_data.DATA_DIR])
        jinjaEnv = jinja2.Environment(loader=jinjaLoader)
        xml_template = jinjaEnv.get_template(config_data.XML_TEMPLATE)

        # Stuff our values in a dict
        instance_values = {'domain_name': self.name,
                           'uuid': uuid.uuid4(),
                           'memory': self.ram * 1024,  # MiB to KiB
                           'disk': self.local_disk,
                           'seed': self.seed_path,
                           'mac_address': util.generate_mac_address()}

        # Write out the final xml file for the domain
        with open(self.xml_path, 'w') as dom_template:
            dom_template.write(xml_template.render(instance_values))

        return

    def spawn_vm(self):
        """Create and boot the instance, using prepared data."""

        self.write_domain_xml()

        with open(self.xml_path, 'r') as xml_file:
            domain_xml = ''.join([x for x in xml_file.readlines()])

        conn = libvirt.open('qemu:///system')
        conn.defineXML(domain_xml)

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

    def boot(self, timeout=config_data.BOOT_TIMEOUT):
        """Deprecated alias for :py:meth:`start`"""

        log.warn("instance.boot has been depricated and will be removed in a "
                 "future release, use instance.start instead")

        self.start(timeout)

    def start(self, timeout=config_data.BOOT_TIMEOUT):
        """Start an existing instance and wait up to :py:attr:`timeout` seconds
        for a network interface to appear.

        :param int timeout: number of seconds to wait before timing out.
                            Setting this to 0 will disable timeout, default
                            is configured with :py:const:`BOOT_TIMEOUT` config
                            value.
        :raises TestcloudInstanceError: if there is an error while creating the
                                        instance or if the timeout is reached
                                        while looking for a network interface
        """

        log.debug("Creating domain {}".format(self.name))
        dom = self._get_domain()
        create_status = dom.create()

        # libvirt doesn't directly raise errors on boot failure, check the
        # return code to verify that the boot process was successful from
        # libvirt's POV
        if create_status != 0:
            raise TestcloudInstanceError("Instance {} did not start "
                                         "successfully, see libvirt logs for "
                                         "details".format(self.name))
        log.debug("Polling domain for active network interface")

        poll_tick = 0.5
        timeout_ticks = timeout / poll_tick
        count = 0

        # poll libvirt for domain interfaces, returning when an interface is
        # found, indicating that the boot process is post-cloud-init
        while count <= timeout_ticks:
            domif = dom.interfaceAddresses(0)

            if len(domif) > 0 or timeout_ticks == 0:
                log.info("Successfully booted instance {}".format(self.name))
                return

            count += 1
            time.sleep(poll_tick)

        # If we get here, the boot process has timed out
        raise TestcloudInstanceError("Instance {} has failed to boot in {} "
                                     "seconds".format(self.name, timeout))

    def stop(self):
        """Stop the instance

        :raises TestcloudInstanceError: if the instance does not exist
        """

        log.debug("stopping instance {}.".format(self.name))

        system_domains = _list_system_domains("qemu:///system")
        domain_exists = self.name in system_domains

        if not domain_exists:
            raise TestcloudInstanceError(
                    "Instance doesn't exist: {}".format(self.name))

        if system_domains[self.name] == 'shutoff':
            log.debug('Instance already shut off, not stopping: {}'.format(
                self.name))
            return

        # stop (destroy) the vm
        self._get_domain().destroy()

    def remove(self, autostop=True):
        """Remove an already stopped instance

        :param bool autostop: if the instance is running, stop it first
        :raises TestcloudInstanceError: if the instance does not exist, or is still
                                        running and ``autostop==False``
        """

        log.debug("removing instance {} from libvirt.".format(self.name))

        # this should be changed if/when we start supporting configurable
        # libvirt connections
        system_domains = _list_system_domains("qemu:///system")

        # Check that the domain is registered with libvirt
        domain_exists = self.name in system_domains
        if domain_exists and system_domains[self.name] == 'running':

            if autostop:
                self.stop()
            else:
                raise TestcloudInstanceError(
                    "Cannot remove running instance {}. Please stop the "
                    "instance before removing.".format(self.name))

        # remove from libvirt, assuming that it's stopped already
        if domain_exists:
            self._get_domain().undefine()
            log.debug("Unregistering domain from libvirt.")

        log.debug("removing instance {} from disk".format(self.path))

        # remove from disk
        shutil.rmtree(self.path)

    def destroy(self):
        '''A deprecated method. Please call :meth:`remove` instead.'''

        log.debug('DEPRECATED: destroy() method was deprecated. Please use remove()')
        self.remove()
