#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import platform
import re

from setuptools import setup
from distutils.command import install as distutils_install
from distutils.command.sdist import sdist as distutils_sdist


class install(distutils_install.install):
    """
    Custom install command
    """
    sub_commands = [
        ('install_lib', lambda self:False),
        ('install_headers', lambda self:False),
        ('install_scripts', lambda self:True),
        ('install_data', lambda self:True),
        ('install_egg_info', lambda self:False),
    ]


setup(
    name = "containerinfo-rpm",
    version = '0.1.0',
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
    cmdclass = {
        'install':  install,
        'sdist':    distutils_sdist
    },
    scripts = ['kiwi_post_run'],
    data_files={'containerinfoRPM/spec.template'}
)
