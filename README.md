flask-messenger
===============

This is a simple CRUD-type messaging app built with Flask (with Bootstrap for styling and responsiveness). It also features a REST API.

flask-messenger works with Python 3.x, which you really should be using at this point. It may still work with Python 2.x, but caveat emptor.

Installation:
-------------

1. Clone this repository.
2. Install the pre-requisites. Using [a virtualenv](https://docs.python.org/3/library/venv.html) is preferred. To setup a virtualenv and install dependencies via Pip:

```
python3 -m venv ./env
. env/bin/activate
pip install -r requirements.txt
```

Running it:
-----------
```
python messenger.py
```

Running the tests:
------------------
```
python messenger_tester.py
```

Running the tests with Coverage:
------------------
```
coverage run --omit=env/*  messenger_tester.py
coverage html
```

Notes:
--------

For the time being, the REST API doesn't use authentication. Also, the POST views are not yet protected against CSRF attacks.

Licensing:
----------

flask-messenger is licensed under the MIT license, which can be viewed at [flask-messenger/LICENSE](flask-messenger/LICENSE).
