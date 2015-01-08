import os


DOWNLOAD_PROGRESS = True

# Directories testCloud cares about

PRISTINE = "/home/{}/.cache/testcloud/images".format(os.getlogin())
LOCAL_DOWNLOAD_DIR = "/var/tmp/"

# Data for cloud-init

META_DATA = """instance-id: iid-123456
local-hostname: %s
"""
USER_DATA = """#cloud-config
password: %s
chpasswd: { expire: False }
ssh_pwauth: True
"""
ATOMIC_USER_DATA = """#cloud-config
password: %s
chpasswd: { expire: False }
ssh_pwauth: True
runcmd:
  - [ sh, -c, 'echo -e "ROOT_SIZE=4G\nDATA_SIZE=10G" > /etc/sysconfig/docker-storage-setup']
"""

# Extra cmdline args for the qemu invocation.
# Customize as needed :)

CMD_LINE_ARGS = ['-redir',
                 'tcp:2222::22',
                 '-redir',
                 'tcp:8888::80',
                 '-smp',
                 '2'
                 ]
