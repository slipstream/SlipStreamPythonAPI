# SlipStreamPythonAPI

Python client for the SlipStream CIMI API.

## Installation

  `$ pip install slipstream-api`

  or

  `$ yum install slipstream-python-api`

## Usage

```python
  from slipstream.api import Api
  
  api = Api('https://nuv.la')
  
  # Login with username & password
  api.login_internal('username', 'password')
  # or
  # Login with api-key & secret
  api.login_apikey('credential/uuid', 'secret')
  
  # List available applications from the App Store
  api.list_applications()
  
  # Deploy an application and get its deployment ID
  deployment_id = api.deploy('apps/WordPress/wordpress', cloud='exoscale-ch-gva')

  # Terminate the deployment started above
  api.terminate(deployment_id)

  # Logout
  api.logout()
  ```

## Contribute

### Development helper

```sh
git clone https://github.com/slipstream/SlipStreamPythonAPI.git
cd SlipStreamPythonAPI/api/
pip install --editable .
```

### Push version to pypi

Configure `~/.pypirc` with pypi repo credentials. This file should look
like as following:

```
[distutils]
index-servers=pypi

[pypi]
username = <username>
password = <password>
```

From repo root directory, launch following commands:
```sh
git checkout <release-version>
mvn clean install -P release
```

## Documentation
### Simple docstring based documentation
You can get the full documentation by typing:

_Python shell/code_
```python
from slipstream.api import Api
help(Api)
```
_Shell_
```sh
pydoc slipstream.api.Api
```

Or for a specific function:

_Python shell/code_
```python
from slipstream.api import Api
help(Api.deploy)
```
_Shell_
```sh
pydoc slipstream.api.Api.deploy
```

Or to get only the docstring:

_Python shell/code_
```python
from slipstream.api import Api
print Api.deploy.__doc__
```

Currently there is no HTML version of the documentation, only
docstring inside the code but the documentation can be generated by
the user.

To run a local webserver with the documentation you can run:
```shell
pydoc -p 8080 slipstream.api.Api
```
and then
[http://localhost/slipstream.api.api.html#Api](http://localhost/slipstream.api.api.html#Api)

### Sphinx documentation

There is a Sphinx documentation available at
http://slipstream.github.io/SlipStreamPythonAPI

#### Generate and publish the Sphinx documentation to GitHub Pages

You can use the provided makefile (in the `doc` directory or in the
root directory):

```shell
make gh-pages
```

