If you are interested in contributing to this project, you will need to be able to manually build it.

However, if you just want to download and use this project, please refer back to the [Installation](./README.md#installation) instructions in the README file.

# Manually building (for development)

This project is built with [Poetry](https://python-poetry.org/). 
In order to build it, please follow the [installation instructions](https://python-poetry.org/docs/#installation) for poetry first. 
If you are unfamiliar with poetry as a build tool, it is recommended to review the [Basic Usage](https://python-poetry.org/docs/basic-usage/) documentation before continuing.

## Installing
```
poetry install
```

## Running tests
All tests
```
poetry run pytest
```

Exclude regression tests
```
poetry run pytest -m "not regression"
```

Only regression tests
```
poetry run pytest -m "regression"
```


## Clean, build, and upload
```
rm -r dist
poetry install
poetry build
# pypi test upload
# poetry config repositories.testpypi https://test.pypi.org/legacy/
# poetry publish -r testpypi

#pypi upload
poetry publish
```

## Install a specific version
```
pip install podaac-data-subscriber==1.7.0
podaac-data-subscriber -c xxx -d ddd  --version
```
