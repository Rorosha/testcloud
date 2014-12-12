LOCAL_DOWNLOAD_DIR = "/tmp/"
DOWNLOAD_PROGRESS = True

# Data for cloud-init

META_DATA =  """instance-id: iid-123456
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
                 '-append', # These two lines are needed for cloud-init
                 'root=/dev/vda1 ro ds=nocloud-net'
]
