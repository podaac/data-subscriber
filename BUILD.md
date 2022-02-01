# Manually building

## Make sure we have all the build Dependencies
```
python3 -m pip install --upgrade build
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade twine
```

## Clean, build, and upload
```
rm -r dist
python3 -m build
# pypi test upload
# python3 -m twine upload --repository testpypi dist/*

#pypi upload
python3 -m twine upload dist/*
```

## Install a specific version
```
pip install podaac-data-subscriber==1.7.0
podaac-data-subscriber -c xxx -d ddd  --version
```
