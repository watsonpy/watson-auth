.. Watson - Auth documentation master file, created by
   sphinx-quickstart on Fri Jan 17 14:49:48 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: python(code)
   :language: python

Watson-Auth
===========

Authorization and authentication library for Watson.

Build Status
------------

+-----------+------------------+---------------------+
| Branch    | Status           | Coverage            |
+===========+==================+=====================+
| Master    | |Build StatusM|  | |Coverage Status|   |
+-----------+------------------+---------------------+
| Develop   | |Build StatusD|  |                     |
+-----------+------------------+---------------------+

|Pypi|

Requirements
------------

-  watson-db
-  py3k-bcrypt

Installation
------

``pip install watson-auth``

Testing
-------

Watson can be tested with py.test. Simply activate your virtualenv and run :python:`python setup.py test`.

Contributing
------------

If you would like to contribute to Watson, please feel free to issue a
pull request via Github with the associated tests for your code. Your
name will be added to the AUTHORS file under contributors.

Table of Contents
-----------------

.. include:: toc.rst.inc

.. |Coverage Status| image:: https://coveralls.io/repos/bespohk/watson-auth/badge.png
   :target: https://coveralls.io/r/bespohk/watson-auth
.. |Build StatusD| image:: https://api.travis-ci.org/bespohk/watson-auth.png?branch=develop
   :target: https://travis-ci.org/bespohk/watson-auth
.. |Build StatusM| image:: https://api.travis-ci.org/bespohk/watson-auth.png?branch=master
   :target: https://travis-ci.org/bespohk/watson-auth
.. |Pypi| image:: https://pypip.in/v/watson-auth/badge.png
   :target: https://crate.io/packages/watson-auth/
