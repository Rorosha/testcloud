#########
testCloud
#########

testCloud is a small helper script to download and boot cloud images locally.
Currently only Fedora qcow2 images are tested and supported.

Requirements
------------

This script relies on the libvirt package - and boots images in Qemu.

Usage
-----

.. code:: bash

    python testCloud.py <url for qcow2 image>

There are currently only three options (all optional) you can use when invoking
this script: '--ram', '--no-graphic' and '--atomic'.

The --ram option takes an int for how much ram you want the guest to have, 
the --no-graphic option is merely a flag to suppress a GUI from appearing and
the --atomic option indicates that you wish to boot an 
`Atomic <http://projectatomic.io>`_ host.

Once the image has booted, you can log in from the GUI or ssh. To log in with 
ssh, run the following command:

.. code:: bash

    ssh -F ./ssh_config testCloud

The user is 'fedora' and the password is 'passw0rd'

Now you have a working local cloud image to test against.

Testing
-------

Currently there is no testsuite for this script. If it proves useful to someone
else, then we can make one. The best means of ensuring the code works and it's
not your image, is to test against the latest Fedora Cloud release image. Download
a qcow2 image from `here <http://cloud.fedoraproject.org/>`_.

Credit
------

Thanks to `Oddshocks <https://github.com/oddshocks>`_ for the koji downloader code :)

License
-------

This code is licensed GPLv2. See the LICENSE file for details.
