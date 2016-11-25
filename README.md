# SlipStreamPythonAPI

Python wrapper of the SlipStream API

## Installation
  `$ pip install slipstream-api`

## Usage
  `$ python`
  ```python
  from slipstream.api import Api
  api = Api('https://nuv.la')
  api.login('username', 'password')
  api.list_applications()
  ```

## Contribute
  `$ sh`
  ```sh
  git clone https://github.com/slipstream/SlipStreamPythonAPI.git
  cd SlipStreamPythonAPI/
  pip install --editable .
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
```bash
pydoc slipstream.api.Api
```

Or for a specific function:
_Python shell/code_
```python
from slipstream.api import Api
help(Api.deploy)
```
_Shell_
```bash
pydoc slipstream.api.Api.deploy
```

Or to get only the docstring:
_Python shell/code_
```python
from slipstream.api import Api
print Api.deploy.__doc__
```

Currently there is no HTML version of the documentation, only docstring inside the code but the documentation can be generated by the user. 
To run a local webserver with the documentation you can run:
```shell
pydoc -p 8080 slipstream.api.Api
```
and then [http://localhost/slipstream.api.api.html#Api](http://localhost/slipstream.api.api.html#Api)

### Sphinx documentation
There is a Sphinx documentation available at http://slipstream.github.io/SlipStreamPythonAPI

#### Generate and publish the Sphinx documentation to GitHub Pages
You can use the provided makefile (in the `doc` directory or in the root directory):
```shell
make gh-pages
```
