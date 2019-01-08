#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import platform
import re

from setuptools import setup


setup(
    name = "containerinfo-rpm",
    version = '0.1.1',
    author = "David Cassany",
    author_email = "dcassany@suse.com",
    description = "OBS KIWI post run hook to package container metadata",
    license = "GPL",
    keywords = "open build service",
    url = "https://github.com/kubic-project/containerinfo-rpm",
    packages=['containerinfoRPM'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Topic :: Development :: Tools :: Building',
    ],
    data_files={'containerinfoRPM/spec.template'},
    entry_points = {
        'console_scripts': [
            'kiwi_post_run = containerinfoRPM.kiwi_post_run:main'
        ]
    }
)
