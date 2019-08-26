#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

# the name of the project
name = 'jupyter_client'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2, 7) or (v[0] >= 3 and v[:2] < (3, 5)):
    error = "ERROR: %s requires Python version 2.7 or 3.5 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os

from setuptools import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

version_ns = {}
with open(pjoin(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)

from setuptools.command.bdist_egg import bdist_egg

class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install from performing setuptools' default easy_install,
    which it should never ever do.
    """
    def run(self):
        sys.exit("Aborting implicit building of eggs. Use `pip install .` to install from source.")


setup_args = dict(
    name            = name,
    version         = version_ns['__version__'],
    packages        = packages,
    description     = 'Jupyter protocol implementation and client libraries',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author          = 'Jupyter Development Team',
    author_email    = 'jupyter@googlegroups.com',
    url             = 'https://jupyter.org',
    license         = 'BSD',
    platforms       = "Linux, Mac OS X, Windows",
    keywords        = ['Interactive', 'Interpreter', 'Shell', 'Web'],
    project_urls    = {
        'Documentation': 'https://jupyter-client.readthedocs.io',
        'Source': 'https://github.com/jupyter/jupyter_client/',
        'Tracker': 'https://github.com/jupyter/jupyter_client/issues',
    },
    classifiers     = [
        'Framework :: Jupyter',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    install_requires = [
        'traitlets',
        'jupyter_core',
        'pyzmq>=13',
        'python-dateutil>=2.1',
        'tornado>=4.1',
        "pywin32 >=1.0 ; sys_platform == 'win32'"
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    extras_require   = {
        'test': ['ipykernel', 'ipython', 'mock', 'pytest'],
    },
    cmdclass         = {
        'bdist_egg': bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled,
    },
    entry_points     = {
        'console_scripts': [
            'jupyter-kernelspec = jupyter_client.kernelspecapp:KernelSpecApp.launch_instance',
            'jupyter-run = jupyter_client.runapp:RunApp.launch_instance',
            'jupyter-kernel = jupyter_client.kernelapp:main',
        ],
    },
)


if __name__ == '__main__':
    setup(**setup_args)
