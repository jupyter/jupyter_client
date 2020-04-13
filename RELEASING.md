# Releasing

## Prerequisites

- First check that the changelog.rst is up to date for the next release version

## Bump version

- Load `jupyter_client/_version.py` and remove the 'dev' tag
- Change from patch to minor or major for appropriate version updates.
- `git commit -am "Bumped version for release"`
- `git tag {new version here}`

## Push to PyPI

```bash
rm -rf dist/*
rm -rf build/*
python setup.py sdist bdist_wheel
# You should probably also test downstream libraries against each of the artifacts produced as this isn't tested in the project atm
twine upload dist/*
```

## Dev version

- Load `jupyter_client/_version.py` and bump the patch version and add the 'dev' tag back to the end of the version tuple.


## Push to GitHub

```bash

git commit -am "Added dev back to version"
git push upstream  && git push upstream --tags
```
