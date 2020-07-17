# tsuru-bluegreen [![Build Status](https://travis-ci.org/emerleite/tsuru-bluegreen.svg?branch=master)](https://travis-ci.org/emerleite/tsuru-bluegreen)

A blue-green deployment plugin for tsuru client

## Dependencies

Python 2.7

## Installation

```
tsuru plugin-install bluegreen https://raw.githubusercontent.com/emerleite/tsuru-bluegreen/1.4.3/src/bluegreen.py
```

## Deployment methods

By default, the plugin deploys using `git push`. But if you define a `deploy_dir` key, inside the `Application` section of the configuration file, it uses `tsuru app-deploy` command instead.

## Configuration

Tsuru bluegreen uses convention over configuration. It assumes your application backend is named using blue and green sufixes, as explained bellow:

Create a **tsuru-bluegreen.ini** in your application root with the following configuration:

```
[Application]
name: <your_app>
deploy_dir: <./build> <./build2>

[NewRelic]
api_key: <newrelic_api_key>
app_id: <newrelic_app_id>

[Grafana]
endpoint: <logstash_endpoint>
index: <logstash_index>

[WebHook]
endpoint: http://example.com
payload_extras: key1=value1&key2=value2

[Hooks]
before_pre: <command to run before 'pre' action>
after_pre: <command to run after a successful 'pre' action>
before_swap: <command to run before 'swap' action>
after_swap: <command to run after a successful 'swap' action>
```

**Note:** if a NewRelic key's value is left blank, the plugin will try to get it from an environment variable (`NEW_RELIC_API_KEY` or `NEW_RELIC_APP_ID`).

### 'Application' section

Based on the `name` configuration value, you must have to have two tsuru applications and git remotes named: your_app**-blue** and your_app**-green**.

The `deploy_dir` configuration value is used with the `--app-deploy` flag. The default value is `.`.

### 'NewRelic' section

Notify New Relic about your deployment after swap. See [NewRelic docs](https://docs.newrelic.com/docs/apm/new-relic-apm/maintenance/deployment-notifications).

### 'Grafana' section

Notify Grafana about your deployment after swap. See [Grafana docs](http://docs.grafana.org/reference/annotations/).

### 'WebHook' section

POST to a **WebHook** after deployment swap. The payload is the defined payload_extras plus **tag=<tag_value>**.

### 'Hooks' section

Hooks are optional. They are ran before or after the corresponding actions, and everything sent to stdout and stderr is ignored. **If a before hook fails (return value isn't zero), the action (pre/swap) is cancelled.** If you want to run the pre/swap action independently of the before hook execution, you need to make sure it always returns `0`.

Hooks must run inside a shell. If you want to run a `curl` command, for instance, you should do it inside a shell script:

```
$ cat script.sh
#! /bin/sh
curl http://example.com

$ cat tsuru-bluegreen.ini
[Application]
name: test

[Hooks]
before_pre: ./script.sh

$ tsuru bluegreen pre -t some-tag
```

In this case, if `curl` command fails, the `pre` action will be cancelled.

## Example

```
$ tsuru app-list

+---------------+-------------------------+---------------------------------------------------+--------+
| Application   | Units State Summary     | Address                                           | Ready? |
+---------------+-------------------------+---------------------------------------------------+--------+
| sample-blue   | 4 of 4 units in-service | sample.example.com, sample-blue.cloud.example.com | Yes    |
| sample-green  | 0 of 0 units in-service | sample-green.cloud.globoi.com                     | Yes    |
+---------------+-------------------------+---------------------------------------------------+--------+
```

```
$ git remote

sample-blue
sample-green

```

## Usage

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

## Tests

```
$ make testdeps
$ make test
```
