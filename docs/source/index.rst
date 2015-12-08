.. testCloud documentation master file, created by
   sphinx-quickstart on Wed May 20 14:59:21 2015.

.. This work is licensed under the Creative Commons Attribution 4.0
   International License. To view a copy of this license, visit
   http://creativecommons.org/licenses/by/4.0/.

==================================================
testCloud - the best pretend cloud you'll ever use
==================================================

testCloud is a relatively simple system which is capable of booting images
designed for cloud systems on a local system with minimial configuration.
testCloud is desiged to be (and remain) somewhat simple, trading fancy cloud
system features for ease of use and sanity in development.


Installing testCloud
====================

The easiest way to install and use testCloud is to install the package from
`the testCloud COPR <https://copr.fedoraproject.org/coprs/roshi/testCloud/>`_::

  dnf enable roshi/testCloud
  dnf install testCloud


Using testCloud
===============

The main testCloud interface uses the terminal and the binary named
``testcloud``. testCloud operations can be split into two major categories:
image commands and instance commands.

Image Commands
--------------

``testcloud image list``
  List all of the images currently cached by testCloud

``testcloud image destroy <image name>``
  Remove the image named ``<image name>`` from the local image backing store. Make sure
  to replace ``<image name>`` with the name of an image which is currently
  cached.

Instance Commands
-----------------

``testcloud instance list``
  List all of the instances currently running and spawned by testCloud. Adding
  the ``--all`` flag will list all instances spawned by testCloud whether the
  instance is currently running or not


``testcloud instance create <instance name> -u <image url>``
  Create a new testCloud instance using the name ``<instance name>`` and the
  image stored at the url ``<image url>``. Currently supported image url types
  are ``http(s)://`` and ``file://``. Run ``testcloud instance create --help``
  for information on other options for image creation.


``testcloud instance stop <instance name>``
  Stop the instance with name ``<instance name>``

``testcloud instance start <instance name>``
  Start the instance with name ``<instance name>``

``testcloud instance destroy <instance name>``
  Destroy the instance with name ``<instance name>``. This command will fail if
  the instance is not currently stopped


Getting Help
============

Self service methods for asking questions and filing tickets:

 * `Source Repository <https://github.com/Rorosha/testCloud>`_

 * `Currently Open Issues <https://phab.qadevel.cloud.fedoraproject.org/tag/testcloud/>`_

For other questions, the best places to ask are:

 * `The #fedora-qa IRC channel on Freenode <http://webchat.freenode.net/?channels=#fedora-qa>`_

 * `The qa-devel mailing list <https://admin.fedoraproject.org/mailman/listinfo/qa-devel>`_

Licenses
========

The testCloud library is licensed as `GNU General Public Licence v2.0 or later
<http://spdx.org/licenses/GPL-2.0+>`_.

The documentation for testCloud is licensed under a `Creative Commons
Atribution-ShareAlike 4.0 International License <https://creativecommons.org/licenses/by-sa/4.0/>`_.


Other Documentation
===================

.. toctree::
   :maxdepth: 2

   indepth
   api

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

