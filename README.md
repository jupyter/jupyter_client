# Jupyter Client

[![Code Health](https://landscape.io/github/jupyter/jupyter_client/master/landscape.svg?style=flat)](https://landscape.io/github/jupyter/jupyter_client/master)


`jupyter_client` contains the reference implementation of the [Jupyter protocol][].
It also provides client and kernel management APIs for working with kernels.

It also provides the `jupyter kernelspec` entrypoint
for installing kernelspecs for use with Jupyter frontends.

[Jupyter protocol]: https://jupyter-client.readthedocs.io/en/latest/messaging.html


# Development Setup

To develop and contribute code for the Jupyter Client, you should set up
a development environment to run the test suite and build the documentation.
The following steps assume that you have `git`, `python`, `pip`, and `make`
already installed and on the system search path.
You might want to set up the development project in a dedicated
[virtual environment](https://virtualenv.pypa.io/en/stable/) or
[conda environment](https://conda.io/docs/using/envs.html),
depending on what Python distribution you are using.

## Clone the Repository

Fetch the Jupyter Client source code by cloning the GitHub repository itself,
or your [fork](https://help.github.com/articles/fork-a-repo/) of it.
To clone the original repository into a subdirectory `jupyter_client` of
`/my/projects/`:

    cd /my/projects/
    git clone https://github.com/jupyter/jupyter_client.git

If you have configured an SSH key pair for GitHub authentication, use the
[SSH URL](https://help.github.com/articles/which-remote-url-should-i-use/)
for cloning instead. But then you already know how to do that anyway.

## Install the Dependencies

The Jupyter Client code depends on several other Python packages at runtime.
The test suite requires a few more packages on top of that.
An [editable install](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)
with `pip` will download the dependencies, and add your local clone of the
Jupyter Client to the Python environment. To create the editable install and
include the dependencies for the test suite:

    cd /my/projects/jupyter_client/
    pip install -e .[test]

The Jupyter Client documentation is built with
[Sphinx](http://www.sphinx-doc.org/en/stable/).
You can install that with `pip` or,
if you are using an Anaconda distribution, with `conda`.

    # in a virtual environment...
    pip install sphinx sphinx_rtd_theme

    # in a conda environment...
    conda install sphinx sphinx_rtd_theme

## Run the Test Suite

Use `pytest` to run the test suite:

    cd /my/projects/jupyter_client/
    pytest

The full test suite takes a while. During development, you'll probably prefer
to run only the tests relevant to your changes. You can tell `pytest` to
run just the tests from a single file by providing the path to the file.
For example:

    cd /my/projects/jupyter_client
    pytest jupyter_client/tests/test_session.py

## Build the Documentation

Use `make` to build the documentation in HTML:

    cd /my/projects/jupyter_client/docs/
    make html

Point your browser to the following URL to access the generated documentation:

_file:///my/projects/jupyter_client/docs/_build/html/index.html_

