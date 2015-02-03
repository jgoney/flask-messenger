flask-messenger
===============

This is a simple CRUD-type messaging app built with Flask (with Bootstrap for styling and responsiveness). It also features a REST API.

Installation:
-------------

1. Clone this repository.
2. Install the pre-requisites. You can install them either globally or in [a virtualenv](https://virtualenv.pypa.io/en/latest/), as you prefer. To install via Pip:

```
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
Notes:
--------

For the time being, the REST API doesn't use authentication. Also, the POST views are not yet protected against CSRF attacks.

Licensing:
----------

flask-messenger is licensed under the MIT license, which can be viewed at [flask-messenger/LICENSE](flask-messenger/LICENSE).
