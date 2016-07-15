.. This work is licensed under the Creative Commons Attribution 4.0
   International License. To view a copy of this license, visit
   http://creativecommons.org/licenses/by/4.0/.

===================
testcloud, in Depth
===================

The best way to understand exactly what testcloud is doing is to read through
the code but the following is a more human-comprehension-friendly method of
describing many of the details regarding how testcloud works.


Instances and Images
====================

Two of the more important higher-level concepts in testcloud are what we refer
to as Instances and Images.

testcloud Image
---------------

At this point, testcloud only supports qcow2 cloud images made from relatively
recent Fedora releases. There are plans to support more distros and more image
types in the future.

The image is representation of a cloud image, where it was downloaded from, how
to download the image and where it lives on the local filesystem. At this time,
images are assumed to already be downloaded if another image sharing the exact
same filename already exists - not the most resilient method ever conceived but
it does work in most cases.

testcloud Instance
------------------

A reasonable description of a testcloud instance is that it is a cloud image
backed virtual machine. This virtual machine can be created, stopped, started
or removed using the CLI interface from testcloud.

testcloud instances make heavy use of `libvirt <http://libvirt.org/>`_ and
virt-install, part of the `virt-manager <http://virt-manager.org/>`_ application.

General Process
===============

Each instance has its own directory in the ``DATA_DIR`` and the tuple of
(``INSTANCE_NAME``. ``IMAGE_FILENAME``) is considered to be unique. This method
of delineating unique instances isn't perfect (should probably use image hash
instead of filename) but it works well enough for now


Directories and Files
=====================

Globally, testcloud requires a few directories for storing images and instance
metadata.

``/var/lib/testcloud/``
  testcloud stores its data in here

``/var/lib/testcloud/backingstores``
  default location for cached images

``/var/lib/testcloud/instances``
  every instance has a unique directory, stored in here


Outside of the global directories, each instance has a directory (sharing the
instance name) inside ``/var/lib/testcloud/instances/``.


``/var/lib/testcloud/instances/<instancename>/``
  Directory to hold instance-specific data

``/var/lib/testcloud/instances/<instancename>/<instancename>-base.qcow2``
  copy-on-write image used as a backing store for the instance - this doesn't
  store the entire image - just the changes made from the base image the instance
  has been booted from

``/var/lib/testcloud/instances/<instancename>/<instancename>-seed.img``
  image holding cloud-init source data used on boot

``/var/lib/testcloud/instances/<instancename>/meta/``
  directory containing data from which the ``<instancename>-seed.img`` is built

``/var/lib/testcloud/instances/<instancename>/meta/meta-data``
  raw meta-data for cloud-init

``/var/lib/testcloud/instances/<instancename>/meta/user-data``
  raw user-data for cloud-init


Booting Instances
=================

The creation process for a testcloud instance roughly follows this process:

 * download the referenced image, if it doesn't already exist in the backingstores

 * create an instance directory for the new instance, if an instance with the
   same name already exists, quit with an error

 * create cloud-init metadata and the qcow2 backing store for the instance

 * use ``virt-install`` to create a new virtual machine, using the backing store
   and the cloud-init ``seed.img`` as data stores.

Once the instance is booted, it can be stopped, started again or deleted.
