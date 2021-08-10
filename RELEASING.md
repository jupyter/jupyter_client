# Releasing

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://github.com/jupyter-server/jupyter_releaser#checklist-for-adoption).

## Manual Release

### Prerequisites

- First check that the CHANGELOG.md is up to date for the next release version
- Install packaging requirements: `pip install tbump build tomlkit==0.7.0`

### Bump version

- `export version=<NEW_VERSION>`
- `tbump ${version} --no-push`

### Push to PyPI

```bash
rm -rf dist/*
rm -rf build/*
python -m build .
twine upload dist/*
```

### Dev version

- Bump the patch version and add the 'dev' tag back to the end of the version tuple using `tbump <DEV_VERSION> --no-push`

### Push to GitHub

```bash
git push upstream  && git push upstream --tags
```
