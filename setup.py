#!/usr/bin/env python
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os

from setuptools import find_packages
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), 'r') as f:
    long_description = f.read()

with open(os.path.join(here, 'requirements.txt'), 'r') as f:
    requirements = f.read().splitlines()

with open(os.path.join(here, 'requirements-test.txt'), 'r') as f:
    requirements_test = f.read().splitlines()

with open(os.path.join(here, 'requirements-doc.txt'), 'r') as f:
    requirements_doc = f.read().splitlines()

setup(
    name='jupyter_client',
    packages=find_packages(exclude=["docs", "docs.*", "tests", "tests.*"]),
    description='Jupyter protocol implementation and client libraries',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    url='https://jupyter.org',
    license='BSD',
    license_file='COPYING.md',
    platforms="Linux, Mac OS X, Windows",
    keywords=['Interactive', 'Interpreter', 'Shell', 'Web'],
    project_urls={
        'Documentation': 'https://jupyter-client.readthedocs.io',
        'Source': 'https://github.com/jupyter/jupyter_client/',
        'Tracker': 'https://github.com/jupyter/jupyter_client/issues',
    },
    classifiers=[
        'Framework :: Jupyter',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.6.1',
    install_requires=requirements,
    extras_require={
        'test': requirements_test,
        'doc': requirements_doc,
    },
    entry_points={
        'console_scripts': [
            'jupyter-kernelspec = jupyter_client.kernelspecapp:KernelSpecApp.launch_instance',
            'jupyter-run = jupyter_client.runapp:RunApp.launch_instance',
            'jupyter-kernel = jupyter_client.kernelapp:main',
        ],
        'jupyter_client.kernel_provisioners': [
            'local-provisioner = jupyter_client.provisioning:LocalProvisioner',
        ],
    },
)
