tsuru-bluegreen
===============

A blue-green deployment plugin for tsuru client

Installation
------------

tsuru plugin-install bluegreen https://raw.githubusercontent.com/emerleite/tsuru-bluegreen/master/src/bluegreen.py


Configuration
-------------

Tsuru bluegreen uses convention over configuration. It assumes your application backend is named using blue and green sufix, as explained bellow:

Create a **tsuru-bluegreen.ini** in your application root with the following configuration:

```
[Application]
name: <your_app>
units: <number_of_production_units>
```

You must have to have two tsuru applications and git remotes named: your_app**-blue** and your_app**-green**.

#### Tsuru example:

```
$ tsuru app-list

+---------------+-------------------------+---------------------------------------------------+--------+
| Application   | Units State Summary     | Address                                           | Ready? |
+---------------+-------------------------+---------------------------------------------------+--------+
| sample-blue   | 4 of 4 units in-service | sample.example.com, sample-blue.cloud.example.com | Yes    |
| sample-green  | 4 of 4 units in-service | sample-green.cloud.globoi.com                     | Yes    |
+---------------+-------------------------+---------------------------------------------------+--------+
```

#### Git example:

```
$ git remote

sample-blue
sample-green

```

Usage
-----
```
tsuru bluegreen --help

usage: tsuru bluegreen action [options]

Tsuru blue-green deployment (pre and live).

positional arguments:
  action                pre or swap

optional arguments:
  -h, --help            show this help message and exit
  -t [TAG], --tag [TAG] Tag to be deployed (default: master)
```
