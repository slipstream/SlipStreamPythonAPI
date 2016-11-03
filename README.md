# SlipStreamPythonAPI

Python wrapper of the SlipStream API

## Installation
  $ pip install slipstream-api

## Usage
  `$ python`
  ```python
  from slipstream.api import Api
  help(Api)
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


