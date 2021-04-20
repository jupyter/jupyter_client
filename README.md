# Jupyter Client

[![Build Status](https://github.com/jupyter/jupyter_client/workflows/CI/badge.svg)](https://github.com/jupyter/jupyter_client/actions)
[![Code Health](https://landscape.io/github/jupyter/jupyter_client/master/landscape.svg?style=flat)](https://landscape.io/github/jupyter/jupyter_client/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`jupyter_client` contains the reference implementation of the [Jupyter protocol][].
It also provides client and kernel management APIs for working with kernels.

It also provides the `jupyter kernelspec` entrypoint
for installing kernelspecs for use with Jupyter frontends.

[jupyter protocol]: https://jupyter-client.readthedocs.io/en/latest/messaging.html

# Development Setup

The [Jupyter Contributor Guides](http://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html) provide extensive information on contributing code or documentation to Jupyter projects. The limited instructions below for setting up a development environment are for your convenience.

## Coding

You'll need Python and `pip` on the search path. Clone the Jupyter Client git repository to your computer, for example in `/my/project/jupyter_client`.
Now create an [editable install](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)
and download the dependencies of code and test suite by executing:

    cd /my/projects/jupyter_client/
    pip install -e .[test]
    py.test

The last command runs the test suite to verify the setup. During development, you can pass filenames to `py.test`, and it will execute only those tests.

## Documentation

The documentation of Jupyter Client is generated from the files in `docs/` using Sphinx. Instructions for setting up Sphinx with a selection of optional modules are in the [Documentation Guide](https://jupyter.readthedocs.io/en/latest/contributing/docs-contributions/index.html). You'll also need the `make` command.
For a minimal Sphinx installation to process the Jupyter Client docs, execute:

    pip install ipykernel sphinx sphinx_rtd_theme

The following commands build the documentation in HTML format and check for broken links:

    cd /my/projects/jupyter_client/docs/
    make html linkcheck

Point your browser to the following URL to access the generated documentation:

_file:///my/projects/jupyter_client/docs/\_build/html/index.html_

## Contributing

jupyter-client has adopted automatic code formatting so you shouldn't
need to worry too much about your code style.
As long as your code is valid,
the pre-commit hook should take care of how it should look.
You can invoke the pre-commit hook by hand at any time with:

```bash
pre-commit run
```

which should run any autoformatting on your code
and tell you about any errors it couldn't fix automatically.
You may also install [black integration](https://github.com/psf/black#editor-integration)
into your text editor to format code automatically.

If you have already committed files before setting up the pre-commit
hook with `pre-commit install`, you can fix everything up using
`pre-commit run --all-files`. You need to make the fixing commit
yourself after that.
