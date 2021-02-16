#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the Omicron Laser project
#
# Copyright (c) 2021 Alberto López Sánchez
# Distributed under the GNU General Public License v3. See LICENSE for more info.

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    "connio",
    
]

extra_requirements = {
    "tango": ["pytango"],
    "simulator": ["sinstruments>=1"],
}
if extra_requirements:
    extra_requirements["all"] = list(set.union(*(set(i) for i in extra_requirements.values())))

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Alberto López Sánchez",
    author_email='controls@cells.es',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Omicron Laser with optional tango server and simulator",
    entry_points={
        'console_scripts': [
            'Omicron_laser=omicron_laser.tango.server:main [tango]',
        ],
    },
    install_requires=requirements,
    extras_require=extra_requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='omicron_laser',
    name='omicron_laser',
    packages=find_packages(include=['omicron_laser', 'omicron_laser.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/catunlock/omicron_laser',
    version='0.1.0',
    zip_safe=False,
)
