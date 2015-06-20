from setuptools import setup

import testcloud


setup(name='testcloud',
      version=testcloud.__version__,
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
