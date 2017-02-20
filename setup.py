from setuptools import setup
import codecs
import re
import os

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(name='testcloud',
      version=find_version('testcloud', '__init__.py'),
      description="small helper script to download and "
      "boot cloud images locally",
      author="Mike Ruckman",
      author_email="roshi@fedoraproject.org",
      license="GPLv2+",
      url="https://github.com/Rorosha/testcloud",
      packages=["testcloud"],
      package_dir={"testcloud": "testcloud"},
      include_package_data=True,
      entry_points=dict(console_scripts=["testcloud=testcloud.cli:main"]),
      )
