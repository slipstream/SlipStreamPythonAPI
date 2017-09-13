#!/usr/bin/env python
"""
 SlipStream Client
 =====
 Copyright (C) 2014 SixSq Sarl (sixsq.com)
 =====
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from setuptools import setup

with open('requirements.txt') as f:
    install_requires = []
    for line in f.readlines():
        if not line.startswith('mock'):
            install_requires.append(line)

version = '${project.version}'

setup(
    name='slipstream-api',
    version=version.replace('-SNAPSHOT', ''),
    description='SlipStream client API library in Python.',
    long_description='SlipStream client API library to communicate with '
                     'SlipStream server.',
    author='SixSq Sarl, (sixsq.com)',
    author_email='info@sixsq.com',
    license='Apache License, Version 2.0',
    platforms='Any',
    url='http://sixsq.com/slipstream',
    install_requires=install_requires,
    package_dir={'slipstream': 'slipstream'},
    packages=[
        'slipstream',
        'slipstream.api'
    ],
    classifiers=[
        'Development Status :: 4 - Betta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development'
    ],
)
