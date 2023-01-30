# Changes in Jupyter Client {#changelog}

<!-- <START NEW CHANGELOG ENTRY> -->

## 8.0.2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.1...717d36edcd9ce595f727d8b5a27e270c2a6e2c46))

### Bugs fixed

- Add papermill downstream check and fix kernel client replies [#925](https://github.com/jupyter/jupyter_client/pull/925) ([@blink1073](https://github.com/blink1073))

### Maintenance and upkeep improvements

- Adopt more ruff rules [#924](https://github.com/jupyter/jupyter_client/pull/924) ([@blink1073](https://github.com/blink1073))
- Prefer print in kernelspecapp [#923](https://github.com/jupyter/jupyter_client/pull/923) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2023-01-26&to=2023-01-30&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2023-01-26..2023-01-30&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 8.0.1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0...dc6113c360e05122430b8e130374e9f4e4b701d7))

### Bugs fixed

- Fix json_output in kernelspec app [#921](https://github.com/jupyter/jupyter_client/pull/921) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2023-01-26&to=2023-01-26&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2023-01-26..2023-01-26&type=Issues)

## 8.0.0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.5...760a7835d8b20a9daea3737759b1751d5e55dad8))

This release is primarily focused on improving `asyncio` support, while aiming to have minimal API changes.

### Enhancements made

- Remove nest-asyncio dependency [#835](https://github.com/jupyter/jupyter_client/pull/835) ([@blink1073](https://github.com/blink1073))

### Bugs fixed

- Allow interrupt during restart of pending kernels [#898](https://github.com/jupyter/jupyter_client/pull/898) ([@blink1073](https://github.com/blink1073))
- Fix connection reconciliation to handle restarts [#882](https://github.com/jupyter/jupyter_client/pull/882) ([@kevin-bates](https://github.com/kevin-bates))
- Reconcile connection information [#879](https://github.com/jupyter/jupyter_client/pull/879) ([@kevin-bates](https://github.com/kevin-bates))
- Workaround for launch bug [#861](https://github.com/jupyter/jupyter_client/pull/861) ([@blink1073](https://github.com/blink1073))
- Defer creation of ready future [#858](https://github.com/jupyter/jupyter_client/pull/858) ([@blink1073](https://github.com/blink1073))
- Fix handling of initial ready promise [#854](https://github.com/jupyter/jupyter_client/pull/854) ([@blink1073](https://github.com/blink1073))
- Revert "Fix pending kernels again" [#853](https://github.com/jupyter/jupyter_client/pull/853) ([@blink1073](https://github.com/blink1073))
- Fix pending kernels again [#845](https://github.com/jupyter/jupyter_client/pull/845) ([@blink1073](https://github.com/blink1073))
- Use pytest_asyncio fixture [#826](https://github.com/jupyter/jupyter_client/pull/826) ([@davidbrochart](https://github.com/davidbrochart))

### Maintenance and upkeep improvements

- MAINT: Don't format log in log call. [#919](https://github.com/jupyter/jupyter_client/pull/919) ([@Carreau](https://github.com/Carreau))
- Remove deprecated zmq imports [#915](https://github.com/jupyter/jupyter_client/pull/915) ([@blink1073](https://github.com/blink1073))
- MAINT: consistently use relative imports. [#912](https://github.com/jupyter/jupyter_client/pull/912) ([@Carreau](https://github.com/Carreau))
- Sync lint deps [#911](https://github.com/jupyter/jupyter_client/pull/911) ([@blink1073](https://github.com/blink1073))
- MAINT: Proper typing and cast [#906](https://github.com/jupyter/jupyter_client/pull/906) ([@Carreau](https://github.com/Carreau))
- MAINT: \[_async_\]start_kernel should only take kwarg only. [#905](https://github.com/jupyter/jupyter_client/pull/905) ([@Carreau](https://github.com/Carreau))
- Add more ci checks [#903](https://github.com/jupyter/jupyter_client/pull/903) ([@blink1073](https://github.com/blink1073))
- Allow releasing from repo [#899](https://github.com/jupyter/jupyter_client/pull/899) ([@blink1073](https://github.com/blink1073))
- Fix jupyter_core pinning [#896](https://github.com/jupyter/jupyter_client/pull/896) ([@ophie200](https://github.com/ophie200))
- Adopt ruff and reduce pre-commit usage [#895](https://github.com/jupyter/jupyter_client/pull/895) ([@blink1073](https://github.com/blink1073))
- Use pytest-jupyter [#891](https://github.com/jupyter/jupyter_client/pull/891) ([@blink1073](https://github.com/blink1073))
- Import ensure_async and run_sync from jupyter_core [#889](https://github.com/jupyter/jupyter_client/pull/889) ([@davidbrochart](https://github.com/davidbrochart))
- Use base setup dependency type [#888](https://github.com/jupyter/jupyter_client/pull/888) ([@blink1073](https://github.com/blink1073))
- More CI Cleanup [#886](https://github.com/jupyter/jupyter_client/pull/886) ([@blink1073](https://github.com/blink1073))
- More coverage [#885](https://github.com/jupyter/jupyter_client/pull/885) ([@blink1073](https://github.com/blink1073))
- Clean up workflow and pyproject [#884](https://github.com/jupyter/jupyter_client/pull/884) ([@blink1073](https://github.com/blink1073))
- Add more coverage [#877](https://github.com/jupyter/jupyter_client/pull/877) ([@blink1073](https://github.com/blink1073))
- Add coverage config [#876](https://github.com/jupyter/jupyter_client/pull/876) ([@blink1073](https://github.com/blink1073))
- Bump actions/setup-python from 2 to 4 [#874](https://github.com/jupyter/jupyter_client/pull/874) ([@dependabot](https://github.com/dependabot))
- Bump actions/checkout from 2 to 3 [#873](https://github.com/jupyter/jupyter_client/pull/873) ([@dependabot](https://github.com/dependabot))
- Use platform dirs in tests [#872](https://github.com/jupyter/jupyter_client/pull/872) ([@blink1073](https://github.com/blink1073))
- Clean up types and remove use of entrypoints [#871](https://github.com/jupyter/jupyter_client/pull/871) ([@blink1073](https://github.com/blink1073))
- Add dependabot [#870](https://github.com/jupyter/jupyter_client/pull/870) ([@blink1073](https://github.com/blink1073))
- Support Python 3.8-3.11 [#866](https://github.com/jupyter/jupyter_client/pull/866) ([@blink1073](https://github.com/blink1073))
- Fix assertion in `TestSession.test_serialize` [#860](https://github.com/jupyter/jupyter_client/pull/860) ([@samrat](https://github.com/samrat))
- Maintenance cleanup [#856](https://github.com/jupyter/jupyter_client/pull/856) ([@blink1073](https://github.com/blink1073))
- Ignore warnings in prereleases test [#844](https://github.com/jupyter/jupyter_client/pull/844) ([@blink1073](https://github.com/blink1073))
- Use hatch for version [#837](https://github.com/jupyter/jupyter_client/pull/837) ([@blink1073](https://github.com/blink1073))
- Move tests to top level [#834](https://github.com/jupyter/jupyter_client/pull/834) ([@blink1073](https://github.com/blink1073))
- Fix nbconvert downstream test [#827](https://github.com/jupyter/jupyter_client/pull/827) ([@blink1073](https://github.com/blink1073))

### Documentation improvements

- Reflect current protocol version in documentation [#918](https://github.com/jupyter/jupyter_client/pull/918) ([@SylvainCorlay](https://github.com/SylvainCorlay))
- Add full api docs [#908](https://github.com/jupyter/jupyter_client/pull/908) ([@blink1073](https://github.com/blink1073))
- Add more ci checks [#903](https://github.com/jupyter/jupyter_client/pull/903) ([@blink1073](https://github.com/blink1073))
- Switch to pydata sphinx theme [#840](https://github.com/jupyter/jupyter_client/pull/840) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-08-25&to=2023-01-26&type=c))

[@arogozhnikov](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aarogozhnikov+updated%3A2022-08-25..2023-01-26&type=Issues) | [@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-08-25..2023-01-26&type=Issues) | [@Carreau](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3ACarreau+updated%3A2022-08-25..2023-01-26&type=Issues) | [@ccordoba12](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Accordoba12+updated%3A2022-08-25..2023-01-26&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-08-25..2023-01-26&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adependabot+updated%3A2022-08-25..2023-01-26&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2022-08-25..2023-01-26&type=Issues) | [@meeseeksdev](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ameeseeksdev+updated%3A2022-08-25..2023-01-26&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2022-08-25..2023-01-26&type=Issues) | [@ophie200](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aophie200+updated%3A2022-08-25..2023-01-26&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-08-25..2023-01-26&type=Issues) | [@samrat](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Asamrat+updated%3A2022-08-25..2023-01-26&type=Issues) | [@SylvainCorlay](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3ASylvainCorlay+updated%3A2022-08-25..2023-01-26&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AZsailer+updated%3A2022-08-25..2023-01-26&type=Issues)

## 8.0.0rc0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0b3...bf637ed9543198d6dca96d748b0307ed01b16c94))

### Maintenance and upkeep improvements

- Allow releasing from repo [#899](https://github.com/jupyter/jupyter_client/pull/899) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-12-13&to=2022-12-19&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-12-13..2022-12-19&type=Issues)

## 8.0.0b3

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0b2...b51a3b5d1a0d1a8ad390c1121506217909da1c4f))

### Bugs fixed

- Allow interrupt during restart of pending kernels [#898](https://github.com/jupyter/jupyter_client/pull/898) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-12-08&to=2022-12-13&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-12-08..2022-12-13&type=Issues)

## 8.0.0b2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0b1...ff33adf784f2bd25814d7ed6ae7c6651cee8376e))

### Maintenance and upkeep improvements

- Fix jupyter_core pinning [#896](https://github.com/jupyter/jupyter_client/pull/896) ([@ophie200](https://github.com/ophie200))
- Adopt ruff and reduce pre-commit usage [#895](https://github.com/jupyter/jupyter_client/pull/895) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-12-05&to=2022-12-08&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-12-05..2022-12-08&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-12-05..2022-12-08&type=Issues) | [@ophie200](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aophie200+updated%3A2022-12-05..2022-12-08&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-12-05..2022-12-08&type=Issues)

## 8.0.0b1

No merged PRs

## 8.0.0b0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0a4...e419ff4a651b6ac7cd533023c2dd3bd391de6eb6))

### Maintenance and upkeep improvements

- Use pytest-jupyter [#891](https://github.com/jupyter/jupyter_client/pull/891) ([@blink1073](https://github.com/blink1073))
- Import ensure_async and run_sync from jupyter_core [#889](https://github.com/jupyter/jupyter_client/pull/889) ([@davidbrochart](https://github.com/davidbrochart))
- Use base setup dependency type [#888](https://github.com/jupyter/jupyter_client/pull/888) ([@blink1073](https://github.com/blink1073))
- More CI Cleanup [#886](https://github.com/jupyter/jupyter_client/pull/886) ([@blink1073](https://github.com/blink1073))
- More coverage [#885](https://github.com/jupyter/jupyter_client/pull/885) ([@blink1073](https://github.com/blink1073))
- Clean up workflow and pyproject [#884](https://github.com/jupyter/jupyter_client/pull/884) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-11-16&to=2022-11-29&type=c))

[@arogozhnikov](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aarogozhnikov+updated%3A2022-11-16..2022-11-29&type=Issues) | [@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-11-16..2022-11-29&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-11-16..2022-11-29&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2022-11-16..2022-11-29&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-11-16..2022-11-29&type=Issues)

## 8.0.0a4

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0a3...107ccdd06c9b67fc081204ae7c0e7123a17cb0c4))

### Bugs fixed

- Fix connection reconciliation to handle restarts [#882](https://github.com/jupyter/jupyter_client/pull/882) ([@kevin-bates](https://github.com/kevin-bates))

### Maintenance and upkeep improvements

- Add more coverage [#877](https://github.com/jupyter/jupyter_client/pull/877) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-11-15&to=2022-11-16&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-11-15..2022-11-16&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2022-11-15..2022-11-16&type=Issues)

## 8.0.0a3

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0a2...10f69c9b5ac55b92b651f1f55fa2814f81f3ce51))

### Bugs fixed

- Reconcile connection information [#879](https://github.com/jupyter/jupyter_client/pull/879) ([@kevin-bates](https://github.com/kevin-bates))

### Maintenance and upkeep improvements

- Add coverage config [#876](https://github.com/jupyter/jupyter_client/pull/876) ([@blink1073](https://github.com/blink1073))
- Bump actions/setup-python from 2 to 4 [#874](https://github.com/jupyter/jupyter_client/pull/874) ([@dependabot](https://github.com/dependabot))
- Bump actions/checkout from 2 to 3 [#873](https://github.com/jupyter/jupyter_client/pull/873) ([@dependabot](https://github.com/dependabot))
- Clean up types and remove use of entrypoints [#871](https://github.com/jupyter/jupyter_client/pull/871) ([@blink1073](https://github.com/blink1073))
- Add dependabot [#870](https://github.com/jupyter/jupyter_client/pull/870) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-11-09&to=2022-11-15&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-11-09..2022-11-15&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adependabot+updated%3A2022-11-09..2022-11-15&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2022-11-09..2022-11-15&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-11-09..2022-11-15&type=Issues)

## 8.0.0a2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0a1...268a3c5c892e3e42e76c5ec120a74de10fb04218))

### Maintenance and upkeep improvements

- Use platform dirs in tests [#872](https://github.com/jupyter/jupyter_client/pull/872) ([@blink1073](https://github.com/blink1073))
- Support Python 3.8-3.11 [#866](https://github.com/jupyter/jupyter_client/pull/866) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-10-25&to=2022-11-09&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-10-25..2022-11-09&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-10-25..2022-11-09&type=Issues)

## 8.0.0a1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v8.0.0a0...35b66d8a738b6c9629ffead308c9f981bee1148f))

### Bugs fixed

- Workaround for launch bug [#861](https://github.com/jupyter/jupyter_client/pull/861) ([@blink1073](https://github.com/blink1073))
- Defer creation of ready future [#858](https://github.com/jupyter/jupyter_client/pull/858) ([@blink1073](https://github.com/blink1073))

### Maintenance and upkeep improvements

- Fix assertion in `TestSession.test_serialize` [#860](https://github.com/jupyter/jupyter_client/pull/860) ([@samrat](https://github.com/samrat))
- Maintenance cleanup [#856](https://github.com/jupyter/jupyter_client/pull/856) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-10-12&to=2022-10-25&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-10-12..2022-10-25&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-10-12..2022-10-25&type=Issues) | [@samrat](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Asamrat+updated%3A2022-10-12..2022-10-25&type=Issues)

## 8.0.0a0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.5...06e9cb3fb29a895a3a14e6e39ab524a13bec85ec))

### Enhancements made

- Remove nest-asyncio dependency [#835](https://github.com/jupyter/jupyter_client/pull/835) ([@blink1073](https://github.com/blink1073))

### Bugs fixed

- Fix handling of initial ready promise [#854](https://github.com/jupyter/jupyter_client/pull/854) ([@blink1073](https://github.com/blink1073))
- Use pytest_asyncio fixture [#826](https://github.com/jupyter/jupyter_client/pull/826) ([@davidbrochart](https://github.com/davidbrochart))

### Maintenance and upkeep improvements

- Ignore warnings in prereleases test [#844](https://github.com/jupyter/jupyter_client/pull/844) ([@blink1073](https://github.com/blink1073))
- Use hatch for version [#837](https://github.com/jupyter/jupyter_client/pull/837) ([@blink1073](https://github.com/blink1073))
- Move tests to top level [#834](https://github.com/jupyter/jupyter_client/pull/834) ([@blink1073](https://github.com/blink1073))
- Fix nbconvert downstream test [#827](https://github.com/jupyter/jupyter_client/pull/827) ([@blink1073](https://github.com/blink1073))

### Documentation improvements

- Switch to pydata sphinx theme [#840](https://github.com/jupyter/jupyter_client/pull/840) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-08-25&to=2022-10-12&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-08-25..2022-10-12&type=Issues) | [@ccordoba12](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Accordoba12+updated%3A2022-08-25..2022-10-12&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-08-25..2022-10-12&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2022-08-25..2022-10-12&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-08-25..2022-10-12&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AZsailer+updated%3A2022-08-25..2022-10-12&type=Issues)

## 7.3.5

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.4...bc5ded5439ca55bd6740885eb3a44ca6bc3e2243))

### Enhancements made

- add `AsyncKernelClient` to `doc/api/client.rst` [#819](https://github.com/jupyter/jupyter_client/pull/819) ([@helioz11](https://github.com/helioz11))

### Bugs fixed

- Use tornado 6.2's PeriodicCallback in restarter [#822](https://github.com/jupyter/jupyter_client/pull/822) ([@vidartf](https://github.com/vidartf))
- Make \_stdin_hook_default async [#814](https://github.com/jupyter/jupyter_client/pull/814) ([@davidbrochart](https://github.com/davidbrochart))

### Maintenance and upkeep improvements

- \[pre-commit.ci\] pre-commit autoupdate [#824](https://github.com/jupyter/jupyter_client/pull/824) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#821](https://github.com/jupyter/jupyter_client/pull/821) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#820](https://github.com/jupyter/jupyter_client/pull/820) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#818](https://github.com/jupyter/jupyter_client/pull/818) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#816](https://github.com/jupyter/jupyter_client/pull/816) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#815](https://github.com/jupyter/jupyter_client/pull/815) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#812](https://github.com/jupyter/jupyter_client/pull/812) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#810](https://github.com/jupyter/jupyter_client/pull/810) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#809](https://github.com/jupyter/jupyter_client/pull/809) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#807](https://github.com/jupyter/jupyter_client/pull/807) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-06-08&to=2022-08-25&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-06-08..2022-08-25&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-06-08..2022-08-25&type=Issues) | [@helioz11](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ahelioz11+updated%3A2022-06-08..2022-08-25&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-06-08..2022-08-25&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Avidartf+updated%3A2022-06-08..2022-08-25&type=Issues)

## 7.3.4

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.3...ca4cb2d6a4b95a6925de85a47b323d2235032c74))

### Bugs fixed

- Revert latest changes to `ThreadedZMQSocketChannel` because they break Qtconsole [#803](https://github.com/jupyter/jupyter_client/pull/803) ([@ccordoba12](https://github.com/ccordoba12))

### Maintenance and upkeep improvements

- Fix sphinx 5.0 support [#804](https://github.com/jupyter/jupyter_client/pull/804) ([@blink1073](https://github.com/blink1073))
- \[pre-commit.ci\] pre-commit autoupdate [#799](https://github.com/jupyter/jupyter_client/pull/799) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-06-07&to=2022-06-08&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-06-07..2022-06-08&type=Issues) | [@ccordoba12](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Accordoba12+updated%3A2022-06-07..2022-06-08&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-06-07..2022-06-08&type=Issues)

## 7.3.3

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.2...37ca37d865db260e7da6fa85339be450d6fd3c3c))

### Bugs fixed

- Add local-provisioner entry point to pyproject.toml Fixes #800 [#801](https://github.com/jupyter/jupyter_client/pull/801) ([@utkonos](https://github.com/utkonos))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-06-06&to=2022-06-07&type=c))

[@utkonos](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Autkonos+updated%3A2022-06-06..2022-06-07&type=Issues)

## 7.3.2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.1...c81771416d9e09e0e92be799f3e8549d0db57e43))

### Enhancements made

- Correct `Any` type annotations. [#791](https://github.com/jupyter/jupyter_client/pull/791) ([@joouha](https://github.com/joouha))

### Maintenance and upkeep improvements

- \[pre-commit.ci\] pre-commit autoupdate [#792](https://github.com/jupyter/jupyter_client/pull/792) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Use hatch backend [#789](https://github.com/jupyter/jupyter_client/pull/789) ([@blink1073](https://github.com/blink1073))
- \[pre-commit.ci\] pre-commit autoupdate [#788](https://github.com/jupyter/jupyter_client/pull/788) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Use flit build backend [#781](https://github.com/jupyter/jupyter_client/pull/781) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-05-08&to=2022-06-06&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-05-08..2022-06-06&type=Issues) | [@joouha](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ajoouha+updated%3A2022-05-08..2022-06-06&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-05-08..2022-06-06&type=Issues)

## 7.3.1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.3.0...4df8a48071649d3488a880e61293efd26b7aff1d))

### Bugs fixed

- Check that channels exist before asking if they are alive [#785](https://github.com/jupyter/jupyter_client/pull/785) ([@ccordoba12](https://github.com/ccordoba12))
- Unicode error correction using Error Handler [#779](https://github.com/jupyter/jupyter_client/pull/779) ([@hxawax](https://github.com/hxawax))

### Maintenance and upkeep improvements

- Allow bot PRs to be automatically labeled [#784](https://github.com/jupyter/jupyter_client/pull/784) ([@blink1073](https://github.com/blink1073))
- \[pre-commit.ci\] pre-commit autoupdate [#783](https://github.com/jupyter/jupyter_client/pull/783) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-04-25&to=2022-05-08&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-04-25..2022-05-08&type=Issues) | [@ccordoba12](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Accordoba12+updated%3A2022-04-25..2022-05-08&type=Issues) | [@hxawax](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ahxawax+updated%3A2022-04-25..2022-05-08&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-04-25..2022-05-08&type=Issues)

## 7.3.0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.2.2...fa597d9cdcdc277abda2c3cab4aeee1593d3a9e2))

### Bugs fixed

- Fix shutdown and cleanup behavior [#772](https://github.com/jupyter/jupyter_client/pull/772) ([@blink1073](https://github.com/blink1073))

### Maintenance and upkeep improvements

- \[pre-commit.ci\] pre-commit autoupdate [#773](https://github.com/jupyter/jupyter_client/pull/773) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [#770](https://github.com/jupyter/jupyter_client/pull/770) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Improve mypy config [#769](https://github.com/jupyter/jupyter_client/pull/769) ([@blink1073](https://github.com/blink1073))
- Clean up pre-commit [#768](https://github.com/jupyter/jupyter_client/pull/768) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-04-07&to=2022-04-25&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-04-07..2022-04-25&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-04-07..2022-04-25&type=Issues)

## 7.2.2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.2.1...01b2095d96c81c56edf8f5df44e12e476b2bcd87))

### Maintenance and upkeep improvements

- Include py.typed file [#766](https://github.com/jupyter/jupyter_client/pull/766) ([@blink1073](https://github.com/blink1073))
- \[pre-commit.ci\] pre-commit autoupdate [#765](https://github.com/jupyter/jupyter_client/pull/765) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- More Cleanup [#764](https://github.com/jupyter/jupyter_client/pull/764) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-03-30&to=2022-04-07&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-03-30..2022-04-07&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-03-30..2022-04-07&type=Issues) | [@echarles](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aecharles+updated%3A2022-03-30..2022-04-07&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Apre-commit-ci+updated%3A2022-03-30..2022-04-07&type=Issues)

## 7.2.1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.2.0...683e8dd96ecd52da48a85f67e4ae31d85f1c6616))

### Maintenance and upkeep improvements

- Handle Warnings [#760](https://github.com/jupyter/jupyter_client/pull/760) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-03-29&to=2022-03-30&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-03-29..2022-03-30&type=Issues)

## 7.2.0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.1.2...098de3e51bd4ee1b1a3aded889e8f109ac5eff89))

### Enhancements made

- Update consoleapp.py [#733](https://github.com/jupyter/jupyter_client/pull/733) ([@you-n-g](https://github.com/you-n-g))

### Bugs fixed

- Json packer: handle TypeError and fallback to old json_clean [#752](https://github.com/jupyter/jupyter_client/pull/752) ([@martinRenou](https://github.com/martinRenou))
- Prefer sending signals to kernel process group [#743](https://github.com/jupyter/jupyter_client/pull/743) ([@kevin-bates](https://github.com/kevin-bates))

### Maintenance and upkeep improvements

- Mock is not needed [#758](https://github.com/jupyter/jupyter_client/pull/758) ([@hroncok](https://github.com/hroncok))
- Add pytest opts and clean up workflows [#757](https://github.com/jupyter/jupyter_client/pull/757) ([@blink1073](https://github.com/blink1073))
- Clean up dependency handling [#750](https://github.com/jupyter/jupyter_client/pull/750) ([@blink1073](https://github.com/blink1073))
- Use built in run cancellation [#742](https://github.com/jupyter/jupyter_client/pull/742) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-01-21&to=2022-03-28&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2022-01-21..2022-03-28&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2022-01-21..2022-03-28&type=Issues) | [@echarles](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aecharles+updated%3A2022-01-21..2022-03-28&type=Issues) | [@hroncok](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ahroncok+updated%3A2022-01-21..2022-03-28&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2022-01-21..2022-03-28&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AmartinRenou+updated%3A2022-01-21..2022-03-28&type=Issues) | [@you-n-g](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ayou-n-g+updated%3A2022-01-21..2022-03-28&type=Issues)

## 7.1.2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.1.1...2c9fbf499f63d4287851021b8f8efc9d3c0e336e))

### Bugs fixed

- Await `kernel.ready` in `_async_shutdown_kernel` [#740](https://github.com/jupyter/jupyter_client/pull/740) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2022-01-14&to=2022-01-21&type=c))

[@jtpio](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ajtpio+updated%3A2022-01-14..2022-01-21&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AZsailer+updated%3A2022-01-14..2022-01-21&type=Issues)

## 7.1.1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.1.0...4428715b65741ddccac9305d318d4ace08fa711a))

### Enhancements made

- Further improvements to pending kernels managment [#732](https://github.com/jupyter/jupyter_client/pull/732) ([@Zsailer](https://github.com/Zsailer))

### Maintenance and upkeep improvements

- Test against all kernels in jupyter kernel test and clean up CI [#731](https://github.com/jupyter/jupyter_client/pull/731) ([@blink1073](https://github.com/blink1073))
- Replace master with main [#729](https://github.com/jupyter/jupyter_client/pull/729) ([@davidbrochart](https://github.com/davidbrochart))

### Documentation improvements

- \[DOC\] improve kernel provisioner doc [#730](https://github.com/jupyter/jupyter_client/pull/730) ([@abzymeinsjtu](https://github.com/abzymeinsjtu))
- add changelog for message spec [#525](https://github.com/jupyter/jupyter_client/pull/525) ([@minrk](https://github.com/minrk))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-11-22&to=2022-01-14&type=c))

[@abzymeinsjtu](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aabzymeinsjtu+updated%3A2021-11-22..2022-01-14&type=Issues) | [@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2021-11-22..2022-01-14&type=Issues) | [@BoPeng](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3ABoPeng+updated%3A2021-11-22..2022-01-14&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2021-11-22..2022-01-14&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2021-11-22..2022-01-14&type=Issues) | [@rgbkrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Argbkrk+updated%3A2021-11-22..2022-01-14&type=Issues) | [@willingc](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Awillingc+updated%3A2021-11-22..2022-01-14&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AZsailer+updated%3A2021-11-22..2022-01-14&type=Issues)

## 7.1.0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.6...6b76603578fd3a76fd577d3319393c9933f53ab0))

### Enhancements made

- Add support for pending kernels [#712](https://github.com/jupyter/jupyter_client/pull/712) ([@blink1073](https://github.com/blink1073))

### Bugs fixed

- Improve restarter logic [#717](https://github.com/jupyter/jupyter_client/pull/717) ([@vidartf](https://github.com/vidartf))
- Set sticky bit only on the directory [#711](https://github.com/jupyter/jupyter_client/pull/711) ([@ci4ic4](https://github.com/ci4ic4))

### Maintenance and upkeep improvements

- Enforce labels on PRs [#720](https://github.com/jupyter/jupyter_client/pull/720) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-10-01&to=2021-11-22&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2021-10-01..2021-11-22&type=Issues) | [@ci4ic4](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aci4ic4+updated%3A2021-10-01..2021-11-22&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2021-10-01..2021-11-22&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-10-01..2021-11-22&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Avidartf+updated%3A2021-10-01..2021-11-22&type=Issues)

## 7.0.6

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.5...58b11df0ecb729effacc59ce28e9f431fa9c6a4d))

### Bugs fixed

- Fallback to the old ipykernel "json_clean" if we are not able to serialize a JSON message [#708](https://github.com/jupyter/jupyter_client/pull/708) ([@martinRenou](https://github.com/martinRenou))

### Other merged PRs

- Add test for serializing bytes [#707](https://github.com/jupyter/jupyter_client/pull/707) ([@martinRenou](https://github.com/martinRenou))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-09-29&to=2021-10-01&type=c))

[@martinRenou](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AmartinRenou+updated%3A2021-09-29..2021-10-01&type=Issues)

## 7.0.5

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.4...e379bf91fea63526b9c4cc6679e7953a325b540c))

### Bugs fixed

- avoid use of deprecated zmq.utils.jsonapi [#703](https://github.com/jupyter/jupyter_client/pull/703) ([@minrk](https://github.com/minrk))

### Maintenance and upkeep improvements

- Use logger.warning instead of deprecated warn method [#700](https://github.com/jupyter/jupyter_client/pull/700) ([@kevin-bates](https://github.com/kevin-bates))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-09-28&to=2021-09-29&type=c))

[@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-09-28..2021-09-29&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2021-09-28..2021-09-29&type=Issues)

## 7.0.4

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.3...5b570152c0d88dd5e0ff1711c75fc9987ef76256))

### Bugs fixed

- Fix json_default so that it's closer to what ipykernel had before [#698](https://github.com/jupyter/jupyter_client/pull/698) ([@martinRenou](https://github.com/martinRenou))
- Clean up the pending task [#697](https://github.com/jupyter/jupyter_client/pull/697) ([@shingo78](https://github.com/shingo78))
- fix kernel can only restart once issue [#695](https://github.com/jupyter/jupyter_client/pull/695) ([@mofanke](https://github.com/mofanke))
- Prevent failure if kernel is not found when shutting it down [#694](https://github.com/jupyter/jupyter_client/pull/694) ([@martinRenou](https://github.com/martinRenou))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-09-16&to=2021-09-28&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2021-09-16..2021-09-28&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AmartinRenou+updated%3A2021-09-16..2021-09-28&type=Issues) | [@mofanke](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Amofanke+updated%3A2021-09-16..2021-09-28&type=Issues) | [@shingo78](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ashingo78+updated%3A2021-09-16..2021-09-28&type=Issues)

## 7.0.3

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.2...e2e854c445d697ae1c188171ea0731532b6ac0d9))

### Bugs fixed

- Address missing `local-provisioner` scenario [#692](https://github.com/jupyter/jupyter_client/pull/692) ([@kevin-bates](https://github.com/kevin-bates))
- use `load_connection_info(info)` when constructing a blocking client [#688](https://github.com/jupyter/jupyter_client/pull/688) ([@minrk](https://github.com/minrk))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-08-30&to=2021-09-16&type=c))

[@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-08-30..2021-09-16&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2021-08-30..2021-09-16&type=Issues)

## 7.0.2

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.1...b2a23d8f8b4f24a2bc908b6d95047242f4da87cd))

### Bugs fixed

- Don't set event loop policy on Windows at import time [#686](https://github.com/jupyter/jupyter_client/pull/686) ([@minrk](https://github.com/minrk))

### Documentation improvements

- Improve migration guide [#685](https://github.com/jupyter/jupyter_client/pull/685) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-08-20&to=2021-08-30&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2021-08-20..2021-08-30&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2021-08-20..2021-08-30&type=Issues) | [@dhirschfeld](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adhirschfeld+updated%3A2021-08-20..2021-08-30&type=Issues) | [@jankatins](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ajankatins+updated%3A2021-08-20..2021-08-30&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-08-20..2021-08-30&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2021-08-20..2021-08-30&type=Issues) | [@takluyver](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Atakluyver+updated%3A2021-08-20..2021-08-30&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ayuvipanda+updated%3A2021-08-20..2021-08-30&type=Issues)

## 7.0.1

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/v7.0.0...0ce9f293ea574d61cae438469df5e53298713b63))

### Merged PRs

- Use formal method names when called internally [#683](https://github.com/jupyter/jupyter_client/pull/683) ([@kevin-bates](https://github.com/kevin-bates))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-08-19&to=2021-08-20&type=c))

[@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-08-19..2021-08-20&type=Issues)

## 7.0.0

([Full Changelog](https://github.com/jupyter/jupyter_client/compare/26a16c0c91e245f7403aa27a812fee5e905d2964...31750bc87baf88377bcc6967e227b650b38fa872))

### Summary

The 7.0 release brings a major feature in [Kernel Provisioners](https://github.com/jupyter/jupyter_client/blob/master/docs/provisioning.rst), which enable the ability for third parties to manage the lifecycle of a kernel's runtime environment.

Being a major release, there are some backward incompatible changes. Please see the [migration guide](https://jupyter-client.readthedocs.io/en/latest/migration.html) for further details.

### Enhancements made

- Kernel Provisioning - initial implementation [#612](https://github.com/jupyter/jupyter_client/pull/612) ([@kevin-bates](https://github.com/kevin-bates))

### Bugs fixed

- Fix up some async method aliases in KernelManager [#670](https://github.com/jupyter/jupyter_client/pull/670) ([@kevin-bates](https://github.com/kevin-bates))
- Support `answer_yes` when removing kernel specs [#659](https://github.com/jupyter/jupyter_client/pull/659) ([@davidbrochart](https://github.com/davidbrochart))
- Include process ID in message ID [#655](https://github.com/jupyter/jupyter_client/pull/655) ([@takluyver](https://github.com/takluyver))
- Fix qtconsole issues [#638](https://github.com/jupyter/jupyter_client/pull/638) ([@davidbrochart](https://github.com/davidbrochart))

### Maintenance and upkeep improvements

- Added debugger key in `kernel_info_reply` [#486](https://github.com/jupyter/jupyter_client/pull/486) ([@JohanMabille](https://github.com/JohanMabille))
- Prepare for use with Jupyter Releaser [#676](https://github.com/jupyter/jupyter_client/pull/676) ([@afshin](https://github.com/afshin))
- Force install `jupyter_client` master [#675](https://github.com/jupyter/jupyter_client/pull/675) ([@davidbrochart](https://github.com/davidbrochart))
- Fix project name [#674](https://github.com/jupyter/jupyter_client/pull/674) ([@vidartf](https://github.com/vidartf))
- Rename trait to `allowed_kernelspecs` [#672](https://github.com/jupyter/jupyter_client/pull/672) ([@blink1073](https://github.com/blink1073))
- Remove block parameter from `get_msg()` [#671](https://github.com/jupyter/jupyter_client/pull/671) ([@davidbrochart](https://github.com/davidbrochart))
- Only import `nest_asyncio` locally [#665](https://github.com/jupyter/jupyter_client/pull/665) ([@SylvainCorlay](https://github.com/SylvainCorlay))
- Use a default serializer that is not only for date types [#664](https://github.com/jupyter/jupyter_client/pull/664) ([@martinRenou](https://github.com/martinRenou))
- Updated `debug_info_response` [#657](https://github.com/jupyter/jupyter_client/pull/657) ([@JohanMabille](https://github.com/JohanMabille))
- Do not block on exit [#651](https://github.com/jupyter/jupyter_client/pull/651) ([@impact27](https://github.com/impact27))
- Update test kernel with native coroutine, remove `async_generator` dependency [#646](https://github.com/jupyter/jupyter_client/pull/646) ([@kevin-bates](https://github.com/kevin-bates))
- `setup.py` and CI improvements [#645](https://github.com/jupyter/jupyter_client/pull/645) ([@dolfinus](https://github.com/dolfinus))
- Test downstream projects [#644](https://github.com/jupyter/jupyter_client/pull/644) ([@davidbrochart](https://github.com/davidbrochart))
- Remove deprecations in kernel manager [#643](https://github.com/jupyter/jupyter_client/pull/643) ([@kevin-bates](https://github.com/kevin-bates))
- Add `block=True` back to `get_msg()` [#641](https://github.com/jupyter/jupyter_client/pull/641) ([@davidbrochart](https://github.com/davidbrochart))
- Pin `python>=3.6.1` [#636](https://github.com/jupyter/jupyter_client/pull/636) ([@davidbrochart](https://github.com/davidbrochart))
- Use `pre-commit` [#631](https://github.com/jupyter/jupyter_client/pull/631) ([@davidbrochart](https://github.com/davidbrochart))
- Attempt CI with `ipykernel` 6.0 prerelease [#629](https://github.com/jupyter/jupyter_client/pull/629) ([@SylvainCorlay](https://github.com/SylvainCorlay))
- Make `KernelManager` subclass tests DRY [#628](https://github.com/jupyter/jupyter_client/pull/628) ([@davidbrochart](https://github.com/davidbrochart))
- Add tests to ensure MultiKernelManager subclass methods are called [#627](https://github.com/jupyter/jupyter_client/pull/627) ([@kevin-bates](https://github.com/kevin-bates))
- Add type annotations, refactor sync/async [#623](https://github.com/jupyter/jupyter_client/pull/623) ([@davidbrochart](https://github.com/davidbrochart))

### Documentation improvements

- Create migration guide [#681](https://github.com/jupyter/jupyter_client/pull/681) ([@blink1073](https://github.com/blink1073))
- Update changelog for 7.0.0rc0 [#673](https://github.com/jupyter/jupyter_client/pull/673) ([@blink1073](https://github.com/blink1073))
- Added documentation for `richInspectVariables` request [#654](https://github.com/jupyter/jupyter_client/pull/654) ([@JohanMabille](https://github.com/JohanMabille))
- Change to `edit_magic` payload [#652](https://github.com/jupyter/jupyter_client/pull/652) ([@yitzchak](https://github.com/yitzchak))
- Added missing documentation for the inspectVariables request and resp… [#649](https://github.com/jupyter/jupyter_client/pull/649) ([@JohanMabille](https://github.com/JohanMabille))
- Add status field to other replies in documentation [#648](https://github.com/jupyter/jupyter_client/pull/648) ([@yitzchak](https://github.com/yitzchak))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/jupyter_client/graphs/contributors?from=2021-03-14&to=2021-08-16&type=c))

[@afshin](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aafshin+updated%3A2021-03-14..2021-08-16&type=Issues) | [@blink1073](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ablink1073+updated%3A2021-03-14..2021-08-16&type=Issues) | [@Carreau](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3ACarreau+updated%3A2021-03-14..2021-08-16&type=Issues) | [@ccordoba12](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Accordoba12+updated%3A2021-03-14..2021-08-16&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adavidbrochart+updated%3A2021-03-14..2021-08-16&type=Issues) | [@dhirschfeld](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adhirschfeld+updated%3A2021-03-14..2021-08-16&type=Issues) | [@dolfinus](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Adolfinus+updated%3A2021-03-14..2021-08-16&type=Issues) | [@echarles](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aecharles+updated%3A2021-03-14..2021-08-16&type=Issues) | [@impact27](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aimpact27+updated%3A2021-03-14..2021-08-16&type=Issues) | [@JohanMabille](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AJohanMabille+updated%3A2021-03-14..2021-08-16&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Akevin-bates+updated%3A2021-03-14..2021-08-16&type=Issues) | [@martinRenou](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AmartinRenou+updated%3A2021-03-14..2021-08-16&type=Issues) | [@mattip](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Amattip+updated%3A2021-03-14..2021-08-16&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Aminrk+updated%3A2021-03-14..2021-08-16&type=Issues) | [@MSeal](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3AMSeal+updated%3A2021-03-14..2021-08-16&type=Issues) | [@SylvainCorlay](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3ASylvainCorlay+updated%3A2021-03-14..2021-08-16&type=Issues) | [@takluyver](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Atakluyver+updated%3A2021-03-14..2021-08-16&type=Issues) | [@vidartf](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Avidartf+updated%3A2021-03-14..2021-08-16&type=Issues) | [@yitzchak](https://github.com/search?q=repo%3Ajupyter%2Fjupyter_client+involves%3Ayitzchak+updated%3A2021-03-14..2021-08-16&type=Issues)

## 6.2.0

- Yanked (PyPI) and marked as broken (conda)

## 6.1.13

- Yanked (PyPI) and marked as broken (conda)

## 6.1.12

- Shutdown request sequence has been modified to be more graceful, it
  now is preceded by interrupt, and will also send a `SIGTERM` before
  forcibly killing the kernel. [#620](https://github.com/jupyter/jupyter_client/pull/620)
- Removal of `ipython_genutils` as a dependency. It was implicit
  before; but required by at least traitlets thus avoiding issues. We
  are working on completely removing it from all jupyter dependencies;
  as it might lead to issues packaging for Python 3.10, and was mostly
  used for compatibility with python 2. ([#620](https://github.com/jupyter/jupyter_client/pull/620), [#605](https://github.com/jupyter/jupyter_client/pull/605))
- Address a race condition between `shutdown_kernel` and restarter.
  ([#607](https://github.com/jupyter/jupyter_client/pull/607).)

See the [full list of
pull-requests](https://github.com/jupyter/jupyter_client/milestone/27?closed=1)

## 6.1.11

- Move jedi pinning to test requirements [#599](https://github.com/jupyter/jupyter_client/pull/599)

## 6.1.10

- Add change parameter needed for observer method of
  kernel_spec_manager trait [#598](https://github.com/jupyter/jupyter_client/pull/598)

## 6.1.9

- Pin jedi\<=0.17.2 [#596](https://github.com/jupyter/jupyter_client/pull/596)

## 6.1.8

- Doc updates ([#563](https://github.com/jupyter/jupyter_client/pull/563),
  [#564](https://github.com/jupyter/jupyter_client/pull/564), [#587](https://github.com/jupyter/jupyter_client/pull/587))
- Fix path to the connection file [#568](https://github.com/jupyter/jupyter_client/pull/568)
- Code cleanup ([#574](https://github.com/jupyter/jupyter_client/pull/574),
  [#579](https://github.com/jupyter/jupyter_client/pull/579))
- Silence kill_kernel when no process is present
  [#576](https://github.com/jupyter/jupyter_client/pull/576)
- Remove extra_env and corresponding test [#581](https://github.com/jupyter/jupyter_client/pull/581)
- Add documentation dependencies to setup.py [#582](https://github.com/jupyter/jupyter_client/pull/582)
- Fix for Windows localhost IP addresses [#584](https://github.com/jupyter/jupyter_client/pull/584)
- Drop Travis CI, add GitHub Actions [#586](https://github.com/jupyter/jupyter_client/pull/586)
- Adapt KernelManager.\_kernel_spec_manager_changed to observe
  [#588](https://github.com/jupyter/jupyter_client/pull/588)
- Allow use ~/ in the kernel's command or its arguments
  [#589](https://github.com/jupyter/jupyter_client/pull/589)
- Change wait_for_ready logic [#592](https://github.com/jupyter/jupyter_client/pull/592)
- Fix test_session with msgpack v1 [#594](https://github.com/jupyter/jupyter_client/pull/594)

## 6.1.6

- Removed warnings in more cases for KernelManagers that use new
  cleanup method [#560](https://github.com/jupyter/jupyter_client/pull/560)
- Some improved tests with a conversion to pytest pattern
  [#561](https://github.com/jupyter/jupyter_client/pull/561)

## 6.1.5

- Gracefully Close ZMQ Context upon kernel shutdown to fix memory leak
  [#548](https://github.com/jupyter/jupyter_client/pull/548)
- Fix for chained exceptions to preserve stacks
  ([#552](https://github.com/jupyter/jupyter_client/pull/552), [#554](https://github.com/jupyter/jupyter_client/pull/554))
- Fix start_kernel error when passing kernel_id
  [#547](https://github.com/jupyter/jupyter_client/pull/547)
- Update to releasing docs [#543](https://github.com/jupyter/jupyter_client/pull/543)

## 6.1.4

(Deleted release with incorrect local files)

## 6.1.3

- Add AsyncKernelClient client_class to AsyncKernelManager
  [#542](https://github.com/jupyter/jupyter_client/pull/542)
- Doc fix for xeus hyperlinks [#540](https://github.com/jupyter/jupyter_client/pull/540)
- Doc typo fix [#539](https://github.com/jupyter/jupyter_client/pull/539)

## 6.1.2

- Fixed a bug causing clients to sometimes hang after a stop call was
  made [#536](https://github.com/jupyter/jupyter_client/pull/536)

## 6.1.1

- Subprocess kill action fix for async execution
  [#535](https://github.com/jupyter/jupyter_client/pull/535)
- Doc fix for xeus kernel list [#534](https://github.com/jupyter/jupyter_client/pull/534)

## 6.1.0

This release includes support for asyncio patterns! Downstream tools
should soon have releases to additionally support async patterns.

- AsyncKernelManager and AsyncMultiKernelManager are now available for
  async jupyter_client interactions ([#528](https://github.com/jupyter/jupyter_client/pull/528), [#529](https://github.com/jupyter/jupyter_client/pull/529))
- Removed unused sphinx dependency ([#518](https://github.com/jupyter/jupyter_client/pull/518), [#518](https://github.com/jupyter/jupyter_client/pull/518)).
- Added install instructions for pip to documentation
  [#521](https://github.com/jupyter/jupyter_client/pull/521)
- Improved docs around version protocol and messaging
  ([#522](https://github.com/jupyter/jupyter_client/pull/522), [#526](https://github.com/jupyter/jupyter_client/pull/526))

## 6.0.0

The git history had to be reworked heavily in merging 5.x and master, so
a link to all the changes at once in github had been left out as it's
just confusing.

An exciting change in this release is some async support (huge thanks to
@davidbrochart for doing most of the work)! See linked PR below for
more details, we're working on integrating this into nbclient as well
in the near future.

New Features:

- Added async API [#506](https://github.com/jupyter/jupyter_client/pull/506)

Changes:

- Python 3.8 testing and support added [#509](https://github.com/jupyter/jupyter_client/pull/509)
- Session.msg_id optimization [#493](https://github.com/jupyter/jupyter_client/pull/493)
- Only cache ports if the cache_ports flag is set to True
  [#492](https://github.com/jupyter/jupyter_client/pull/492)
- Removed direct dependency on pywin32 as this is now in jupyter core
  [#489](https://github.com/jupyter/jupyter_client/pull/489)

Fixes:

- Prevent two kernels to have the same ports [#490](https://github.com/jupyter/jupyter_client/pull/490)

Docs:

- Document the handling of error in do_execute
  [#500](https://github.com/jupyter/jupyter_client/pull/500)

Breaking changes:

- Dropped support for Python 2.7!

## 5.3.5

- Backported memory leak fix [#548](https://github.com/jupyter/jupyter_client/pull/548)
  [#555](https://github.com/jupyter/jupyter_client/pull/555).

## 5.3.4

- Changed secure_write to be imported from jupyter_core with fix for
  extended usernames in Windows [#483](https://github.com/jupyter/jupyter_client/pull/483).

## 5.3.3

- Fixed issue with non-english windows permissions
  [#478](https://github.com/jupyter/jupyter_client/pull/478). Potential issue still open
  in use with jupyerlab.

## 5.3.2

- Important files creation now checks umask permissions
  [#469](https://github.com/jupyter/jupyter_client/pull/469).

## 5.3.1

- Fix bug with control channel socket introduced in 5.3.0
  [#456](https://github.com/jupyter/jupyter_client/pull/456).

## 5.3.0

[5.3.0 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.3.0)

New Features:

- Multiprocessing and Threading support [#437](https://github.com/jupyter/jupyter_client/pull/437) and [#450](https://github.com/jupyter/jupyter_client/pull/450)
- Setup package long_description [#411](https://github.com/jupyter/jupyter_client/pull/411)

Changes:

- Control channel now in the public API [#447](https://github.com/jupyter/jupyter_client/pull/447)
- Closing Jupyter Client is now faster [#420](https://github.com/jupyter/jupyter_client/pull/420)
- Pip support improvements [#421](https://github.com/jupyter/jupyter_client/pull/421)

Breaking changes:

- Dropped support for Python 3.3 and 3.4 (upstream packages dropped
  support already)

## 5.2.4

[5.2.4 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.2.4)

- Prevent creating new console windows on Windows
  [#346](https://github.com/jupyter/jupyter_client/pull/346)
- Fix interrupts on Python 3.7 on Windows [#408](https://github.com/jupyter/jupyter_client/pull/408)

## 5.2.3

[5.2.3 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.2.3)

- Fix hang on close in `.ThreadedKernelClient` (used in QtConsole) when using tornado with asyncio
  (default behavior of tornado 5, see [#352](https://github.com/jupyter/jupyter_client/pull/352)).
- Fix errors when using deprecated
  `.KernelManager.kernel_cmd`
  ([#343](https://github.com/jupyter/jupyter_client/pull/343), [#344](https://github.com/jupyter/jupyter_client/pull/344)).

## 5.2.2

[5.2.2 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.2.2)

- Fix `.KernelSpecManager.get_all_specs` method in subclasses that only override
  `.KernelSpecManager.find_kernel_specs` and
  `.KernelSpecManager.get_kernel_spec`.
  See [#338](https://github.com/jupyter/jupyter_client/issues/338) and
  [#339](https://github.com/jupyter/jupyter_client/pull/339).
- Eliminate occasional error messages during process exit
  [#336](https://github.com/jupyter/jupyter_client/pull/336).
- Improve error message when attempting to bind on invalid address
  [#330](https://github.com/jupyter/jupyter_client/pull/330).
- Add missing direct dependency on tornado [#323](https://github.com/jupyter/jupyter_client/pull/323).

## 5.2.1

[5.2.1 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.2.1)

- Add parenthesis to conditional pytest requirement to work around a
  bug in the `wheel` package, that generate a `.whl` which otherwise
  always depends on `pytest` see [#324](https://github.com/jupyter/jupyter_client/issues/324)and [#325](https://github.com/jupyter/jupyter_client/pull/325).

## 5.2

[5.2 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.2)

- Define Jupyter protocol version 5.3:
  - Kernels can now opt to be interrupted by a message sent on the
    control channel instead of a system signal. See
    `kernelspecs` and
    `msging_interrupt`
    [#294](https://github.com/jupyter/jupyter_client/pull/294).
- New `jupyter kernel` command to launch an installed kernel by name
  [#240](https://github.com/jupyter/jupyter_client/pull/240).
- Kernelspecs where the command starts with e.g. `python3` or
  `python3.6`---matching the version `jupyter_client` is running
  on---are now launched with the same Python executable as the
  launching process [#306](https://github.com/jupyter/jupyter_client/pull/306). This
  extends the special handling of `python` added in 5.0.
- Command line arguments specified by a kernelspec can now include
  `{resource_dir}`, which will be substituted with the kernelspec
  resource directory path when the kernel is launched
  [#289](https://github.com/jupyter/jupyter_client/pull/289).
- Kernelspecs now have an optional `metadata` field to hold arbitrary
  metadata about kernels---see `kernelspecs` [#274](https://github.com/jupyter/jupyter_client/pull/274).
- Make the `KernelRestarter` class used by a `KernelManager`
  configurable [#290](https://github.com/jupyter/jupyter_client/pull/290).
- When killing a kernel on Unix, kill its process group
  [#314](https://github.com/jupyter/jupyter_client/pull/314).
- If a kernel dies soon after starting, reassign random ports before
  restarting it, in case one of the previously chosen ports has been
  bound by another process [#279](https://github.com/jupyter/jupyter_client/pull/279).
- Avoid unnecessary filesystem operations when finding a kernelspec
  with `.KernelSpecManager.get_kernel_spec` [#311](https://github.com/jupyter/jupyter_client/pull/311).
- `.KernelSpecManager.get_all_specs`
  will no longer raise an exception on encountering an invalid
  `kernel.json` file. It will raise a warning and continue
  [#310](https://github.com/jupyter/jupyter_client/pull/310).
- Check for non-contiguous buffers before trying to send them through
  ZMQ [#258](https://github.com/jupyter/jupyter_client/pull/258).
- Compatibility with upcoming Tornado version 5.0
  [#304](https://github.com/jupyter/jupyter_client/pull/304).
- Simplify setup code by always using setuptools
  [#284](https://github.com/jupyter/jupyter_client/pull/284).
- Soften warnings when setting the sticky bit on runtime files fails
  [#286](https://github.com/jupyter/jupyter_client/pull/286).
- Various corrections and improvements to documentation.

## 5.1

[5.1 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.1)

- Define Jupyter protocol version 5.2, resolving ambiguity of
  `cursor_pos` field in the presence of unicode surrogate pairs.

  ::: {.seealso}
  `cursor_pos_unicode_note`
  :::

- Add `Session.clone` for making a copy
  of a Session object without sharing the digest history. Reusing a
  single Session object to connect multiple sockets to the same IOPub
  peer can cause digest collisions.

- Avoid global references preventing garbage collection of background
  threads.

## 5.0

### 5.0.1

[5.0.1 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.0.1)

- Update internal protocol version number to 5.1, which should have
  been done in 5.0.0.

### 5.0.0

[5.0.0 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/5.0)

New features:

- Implement Jupyter protocol version 5.1.

- Introduce `jupyter run` command
  for running scripts with a kernel, for instance:

  ```
  jupyter run --kernel python3 myscript.py
  ```

- New method
  `.BlockingKernelClient.execute_interactive` for running code and capturing or redisplaying its
  output.

- New `KernelManager.shutdown_wait_time` configurable for adjusting
  the time for a kernel manager to wait after politely requesting
  shutdown before it resorts to forceful termination.

Fixes:

- Set sticky bit on connection-file directory to avoid getting cleaned
  up.
- `jupyter_client.launcher.launch_kernel` passes through additional options to the underlying
  Popen, matching `KernelManager.start_kernel`.
- Check types of `buffers` argument in
  `.Session.send`, so that TypeErrors
  are raised immediately, rather than in the eventloop.

Changes:

- In kernelspecs, if the executable is the string `python` (as opposed
  to an absolute path), `sys.executable` will be used rather than
  resolving `python` on PATH. This should enable Python-based kernels
  to install kernelspecs as part of wheels.
- kernelspec names are now validated. They should only include ascii
  letters and numbers, plus period, hyphen, and underscore.

Backward-incompatible changes:

- :py`.datetime` objects returned in
  parsed messages are now always timezone-aware. Timestamps in
  messages without timezone info are interpreted as the local
  timezone, as this was the behavior in earlier versions.

## 4.4

### 4.4.0

[4.4 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.4)

- Add `.KernelClient.load_connection_info` on KernelClient, etc. for loading connection info
  directly from a dict, not just from files.
- Include parent headers when adapting messages from older protocol
  implementations (treats parent headers the same as headers).
- Compatibility fixes in tests for recent changes in ipykernel.

## 4.3

### 4.3.0

[4.3 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.3)

- Adds `--sys-prefix` argument to
  `jupyter kernelspec install`, for
  better symmetry with `jupyter nbextension install`, etc.

## 4.2

### 4.2.2

[4.2.2 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.2.2)

- Another fix for the `start_new_kernel` issue in 4.2.1 affecting slow-starting kernels.

### 4.2.1

[4.2.1 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.2.1)

- Fix regression in 4.2 causing `start_new_kernel` to fail while waiting for kernels to become available.

### 4.2.0

[4.2.0 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.2)

- added `jupyter kernelspec remove`
  for removing kernelspecs
- allow specifying the environment for kernel processes via the `env`
  argument
- added `name` field to connection files identifying the kernelspec
  name, so that consumers of connection files (alternate frontends)
  can identify the kernelspec in use
- added `KernelSpecManager.get_all_specs` for getting all kernelspecs more efficiently
- various improvements to error messages and documentation

## 4.1

### 4.1.0

[4.1.0 on
GitHub](https://github.com/jupyter/jupyter_client/milestones/4.1)

Highlights:

- Setuptools fixes for `jupyter kernelspec`
- `jupyter kernelspec list` includes paths
- add `KernelManager.blocking_client`
- provisional implementation of `comm_info` requests from upcoming 5.1
  release of the protocol

## 4.0

The first release of Jupyter Client as its own package.
