# Releasing

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://jupyter-releaser.readthedocs.io/en/latest/get_started/making_release_from_repo.html).

## Manual Release

### Prerequisites

- First check that the CHANGELOG.md is up to date for the next release version
- Install packaging requirements: `pip install pipx`

### Bump version

- `export version=<NEW_VERSION>`
- `pipx run hatch version ${version}`
- `git tag -a ${version} -m {version}`

### Push to PyPI

```bash
rm -rf dist/*
rm -rf build/*
pipx run build .
pipx run twine check dist/*
pipx run twine upload dist/*
```

### Dev version

- Bump the patch version and add the 'dev' tag back to the end of the version tuple using `pipx run hatch version <DEV_VERSION>`

### Push to GitHub

```bash
git push upstream  && git push upstream --tags
```
