.. testcloud documentation master file, created by
   sphinx-quickstart on Wed May 20 14:59:21 2015.

.. This work is licensed under the Creative Commons Attribution 4.0
   International License. To view a copy of this license, visit
   http://creativecommons.org/licenses/by/4.0/.

==================================================
testcloud - the best pretend cloud you'll ever use
==================================================

testcloud is a relatively simple system which is capable of booting images
designed for cloud systems on a local system with minimial configuration.
testcloud is desiged to be (and remain) somewhat simple, trading fancy cloud
system features for ease of use and sanity in development.


Installing testcloud
====================

testcloud is available from the Fedora repositories for F23 and later.

  dnf install testcloud


Using testcloud
===============

The main testcloud interface uses the terminal and the binary named
``testcloud``. testcloud operations can be split into two major categories:
image commands and instance commands.

Image Commands
--------------

``testcloud image list``
  List all of the images currently cached by testcloud

``testcloud image remove <image name>``
  Remove the image named ``<image name>`` from the local image backing store. Make sure
  to replace ``<image name>`` with the name of an image which is currently
  cached.

Instance Commands
-----------------

``testcloud instance list``
  List all of the instances currently running and spawned by testcloud. Adding
  the ``--all`` flag will list all instances spawned by testcloud whether the
  instance is currently running or not


``testcloud instance create <instance name> -u <image url>``
  Create a new testcloud instance using the name ``<instance name>`` and the
  image stored at the url ``<image url>``. Currently supported image url types
  are ``http(s)://`` and ``file://``. Run ``testcloud instance create --help``
  for information on other options for image creation.


``testcloud instance stop <instance name>``
  Stop the instance with name ``<instance name>``

``testcloud instance start <instance name>``
  Start the instance with name ``<instance name>``

``testcloud instance remove <instance name>``
  Remove the instance with name ``<instance name>``. This command will fail if
  the instance is not currently stopped


Getting Help
============

Self service methods for asking questions and filing tickets:

 * `Source Repository <https://github.com/Rorosha/testcloud>`_

 * `Currently Open Issues <https://phab.qadevel.cloud.fedoraproject.org/tag/testcloud/>`_

For other questions, the best places to ask are:

 * `The #fedora-qa IRC channel on Freenode <http://webchat.freenode.net/?channels=#fedora-qa>`_

 * `The qa-devel mailing list <https://admin.fedoraproject.org/mailman/listinfo/qa-devel>`_

Licenses
========

The testcloud library is licensed as `GNU General Public Licence v2.0 or later
<http://spdx.org/licenses/GPL-2.0+>`_.

The documentation for testcloud is licensed under a `Creative Commons
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

