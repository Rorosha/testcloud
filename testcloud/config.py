import os
import imp

import testcloud


DEFAULT_CONF_DIR = os.path.abspath(os.path.dirname(testcloud.__file__)) + '/../conf'

CONF_DIRS = [DEFAULT_CONF_DIR,
             '{}/.config/testcloud'.format(os.environ['HOME']),
             '/etc/testcloud'
             ]

CONF_FILE = 'settings.py'

_config = None


def get_config():
    '''Retrieve a config instance. If a config instance has already been parsed,
    reuse that parsed instance.

    :return: :class:`.ConfigData` containing configuration values
    '''

    global _config
    if not _config:
        _config = _parse_config()
    return _config


def _parse_config():
    '''Parse config file in a supported location and merge with default values.

    :return: loaded config data merged with defaults from :class:`.ConfigData`
    '''

    config = ConfigData()
    config_filename = _find_config_file()

    if config_filename is not None:
        loaded_config = _load_config(config_filename)
        config.merge_object(loaded_config)

    return config


def _find_config_file():
    '''Look in supported config dirs for a configuration file.

    :return: filename of first discovered file, None if no files are found
    '''

    for conf_dir in CONF_DIRS:
        conf_file = '{}/{}'.format(conf_dir, CONF_FILE)
        if os.path.exists(conf_file):
            return conf_file
    return None


def _load_config(conf_filename):
    '''Load configuration data from a python file. Only loads attrs which are
    named using all caps.

    :param conf_filename: full path to config file to load
    :type conf_filename: str
    :return: object containing configuration values
    '''

    new_conf = imp.new_module('config')
    new_conf.__file__ = conf_filename
    try:
        with open(conf_filename, 'r') as conf_file:
            exec(compile(conf_file.read(), conf_filename, 'exec'),
                 new_conf.__dict__)
    except IOError as e:
        e.strerror = 'Unable to load config file {}'.format(e.strerror)
        raise
    return new_conf


class ConfigData(object):
    '''Holds configuration data for TestCloud. Is initialized with default
    values which can be overridden.
    '''

    DOWNLOAD_PROGRESS = True
    LOG_FILE = None

    # Directories testcloud cares about

    DATA_DIR = "/var/lib/testcloud"
    STORE_DIR = "/var/lib/testcloud/backingstores"

    # libvirt domain XML Template
    # This lives either in the DEFAULT_CONF_DIR or DATA_DIR
    XML_TEMPLATE = "domain-template.jinja"

    # Data for cloud-init

    PASSWORD = 'passw0rd'
    HOSTNAME = 'testcloud'

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

    CMD_LINE_ARGS = []

    # timeout, in seconds for instance boot process
    BOOT_TIMEOUT = 30

    # ram size, in MiB
    RAM = 512

    # Desired size, in GiB of instance disks. 0 leaves disk capacity
    # identical to source image
    DISK_SIZE = 0

    def merge_object(self, obj):
        '''Overwrites default values with values from a python object which have
        names containing all upper case letters.

        :param obj: python object containing configuration values
        :type obj: python object
        '''

        for key in dir(obj):
            if key.isupper():
                setattr(self, key, getattr(obj, key))
