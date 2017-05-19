# Commented out default values with details are displayed below. If you want
# to change the values, make sure this file is available in one of the three
# supported config locations:
# - conf/settings.py in the git checkout
# - ~/.config/testcloud/settings.py
# - /etc/testcloud/settings.py


#DOWNLOAD_PROGRESS = True
#LOG_FILE = None


## Directories for data and cached downloaded images ##

#DATA_DIR = "/var/lib/testcloud/"
#STORE_DIR = "/var/lib/testcloud/backingstores"


## Data for cloud-init ##

#PASSWORD = 'passw0rd'
#HOSTNAME = 'testcloud'

#META_DATA = """instance-id: iid-123456
#local-hostname: %s
#"""
## Read http://cloudinit.readthedocs.io/en/latest/topics/examples.html to see
## what options you can use here.
#USER_DATA = """#cloud-config
#password: %s
#chpasswd: { expire: False }
#ssh_pwauth: True
#"""
#ATOMIC_USER_DATA = """#cloud-config
#password: %s
#chpasswd: { expire: False }
#ssh_pwauth: True
#runcmd:
#  - [ sh, -c, 'echo -e "ROOT_SIZE=4G\nDATA_SIZE=10G" > /etc/sysconfig/docker-storage-setup']
#"""


## Extra cmdline args for the qemu invocation ##
## Customize as needed :)

#CMD_LINE_ARGS = []

# The timeout, in seconds, to wait for an instance to boot before
# failing the boot process. Setting this to 0 disables waiting and
# returns immediately after starting the boot process.
#BOOT_TIMEOUT = 30

# ram size, in MiB
#RAM = 512

# Desired size, in GiB of instance disks. 0 leaves disk capacity
# identical to source image
#DISK_SIZE = 0
