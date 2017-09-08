## Requirements

Install `tox` and `pyenv`

```
pip install pyenv tox tox-pyenv 
```

Install different Python versions with `pyenv` and set them locally.

```
PYVERS="2.7.12 3.3.6 3.4.3 3.5.3 3.6.2"
for v in $PYVERS; do
    pyenv install $v
done 
pyenv local $PYVERS
```

To run the tests

```
tox
```

or for specific version of Python

```
tox -e py35
```

as defined in the `api/tox.ini` under `[tox] envlist`.
