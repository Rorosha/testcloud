#########
testcloud
#########

testcloud is a small helper script to download and boot cloud images locally.
Currently only Fedora qcow2 images are tested and supported.

Requirements
------------

Packages:
 - libvirt
 - libvirt-python
 - libguestfs
 - libguestfs-tools
 - python-requests (for whatever python version you're running)

Optional:
 - py.test (if you plan on running or working on the tests)

All of these packages are in the Fedora repos (and likely other distros as
well).

For the moment, the follwing directories need to exist with permissions that
allow modification by any permitted user::

  /var/lib/testcloud/
  /var/lib/testcloud/instances
  /var/lib/testcloud/backingstores

This will be automagical in a future version of testcloud and is a side-effect
of the current refactoring/transition process.

If you are running testcloud as a non-administrative user (ie. not in wheel) or
on a system that doesn't have a polkit agent running (custom setups, headless
systems etc.), you may need to adjust local polkit configuration to allow non-root
users to manage VMs with libvirt. Add the following data into ``/etc/polkit-1/localauthority/50-local.d/50-nonrootlivirt.pkla``::

  [nonroot libvirt system connection]
  Identity=unix-group:testcloud
  Action=org.libvirt.unix.manage
  ResultActive=yes
  ResultInactive=yes
  ResultAny=yes

After writing that file, restart polkit (``systemctl restart polkit``) and if
the user in question is a member of the unix group ``testcloud``, that user
should be able to run testcloud with no additional permissions.

Basic Usage
-----------

The usage varies slightly between using the git checkout and installing the
module. To run testcloud straight from the git checkout, use

.. code:: bash

    python run_testCloud.py instance create <instance name> -u <url for qcow2 image>

After installing via pip or setup.py, you can run

.. code:: bash

    testcloud instance create <instance name> -u <url for qcow2 image>

This will download the qcow2 and store it in /var/lib/testcloud/backingstores/<qcow2 filename>.
This will be used as a backing store for your instance under /var/tmp/instances/<instance
name>. These instances will be viewable within virt-manager. To see your running
instances run:

.. code:: bash

    testcloud instance list

Instances can be stopped, started and removed as well through this interface. To
see a list of options, run:

.. code:: bash

    testcloud instance -h

Options
-------

There are currently only two options (all optional) you can use when invoking
this script: '--ram' and '--no-graphic'.

The --ram option takes an int for how much ram you want the guest to have, the
``--no-graphic option`` is merely a flag to suppress a GUI from appearing.

Once the image has booted, you can log in from the GUI or ssh. To log in with
ssh, run the following command:

.. code:: bash

    ssh fedora@<ip of instance>

The user is 'fedora' and the password is 'passw0rd'

Now you have a working local cloud image to test against.

Configuration
-------------

The default configuration should work for many people but those defaults can
be overridden through the use of a ``settings.py`` file containing the values to
use when overriding default settings. The example file in
``conf/settings-example.py`` shows the possible configuration values which can
be changed.

Note that in order for those new values to be picked up, the filename must be
``settings.py`` and that file must live in one of the following locations:

- ``conf/settings.py`` in the git checkout
- ``~/.config/testcloud/settings.py``
- ``/etc/testcloud/settings.py``

Testing
-------

There is a small testsuite you can run with:

.. code:: bash

    py.test test/

This is a good place to contribute if you're looking to help out.

Issue Tracking and Roadmap
--------------------------

Our project tracker is on the Fedora QA-devel
`Phabricator <https://phab.qadevel.cloud.fedoraproject.org/tag/testcloud/>`_
instance.

Credit
------

Thanks to `Oddshocks <https://github.com/oddshocks>`_ for the koji downloader code :)

License
-------

This code is licensed GPLv2+. See the LICENSE file for details.
