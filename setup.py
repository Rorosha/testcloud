from setuptools import setup, Command

import testCloud


setup(name='testCloud',
        version=testCloud.__version__,
        description="small helper script to download and boot cloud images locally",
        author="Mike Ruckman",
        author_email="roshi@fedoraproject.org",
        license="GPLv2+",
        url="https://github.com/Rorosha/testCloud",
        packages=["testCloud"],
        package_dir={"testCloud":"testCloud"},
        include_package_data=True,
        entry_points=dict(console_scripts=["testCloud=testCloud.cli:main"]),
)
