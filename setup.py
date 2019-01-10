#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup


setup(
    name = "containermetadata-rpm",
    version = '0.1.2',
    author = "David Cassany",
    author_email = "dcassany@suse.com",
    description = "OBS KIWI post run hook to package container metadata",
    license = "GPL",
    keywords = "open build service",
    url = "https://github.com/kubic-project/containermetadata-rpm",
    packages=['containermetadataRPM'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Topic :: Development :: Tools :: Building',
    ],
    data_files={'containermetadataRPM/spec.template'},
    entry_points = {
        'console_scripts': [
            'kiwi_post_run = containermetadataRPM.kiwi_post_run:main'
        ]
    }
)
