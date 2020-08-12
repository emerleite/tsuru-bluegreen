#!/usr/bin/env python

import os
import sys
import httplib
import json
import subprocess
import ConfigParser
import argparse
import time

try:
  from urllib.parse import urlparse
except:
  from urlparse import urlparse

def create_connection(url):
  if url.scheme == 'https':
    return httplib.HTTPSConnection(url.netloc)
  return httplib.HTTPConnection(url.netloc or url.path)

class BlueGreen:
  def __init__(self, token, target, config):
    self.token = token
    self.target = urlparse(target)
    self.app_name = config['name']
    self.deploy_dir = config['deploy_dir']

    try:
      self.hooks = config['hooks']
    except KeyError:
      self.hooks = {}
    try:
      self.newrelic = config['newrelic']
    except KeyError:
      self.newrelic = {}
    try:
      self.grafana = config['grafana']
    except KeyError:
      self.grafana = {}
    try:
      self.webhook = config['webhook']
    except KeyError:
      self.webhook = {}

  def remove_cname(self, app, cname):
    query = ""
    for val in cname:
      query += "cname={}&".format(val)
    query = query[:-1]

    response = self.delete("/apps/{}/cname?{}".format(app, query))
    return response.status == 200

  def set_cname(self, app, cname):
    url = "/apps/{}/cname".format(app)
    body = ""
    for val in cname:
      body += "cname={}&".format(val)
    body = body[:-1]
    return self.post(url, body)

  def get_cname(self, app):
    response = self.get("/apps/{}".format(app))
    data = json.loads(response.read())
    if len(data.get("cname")) == 0:
      return None
    return data.get("cname")

  def post(self, url, body):
    headers = {
      "Authorization": "bearer " + self.token,
      "Content-Type": "application/x-www-form-urlencoded",
     }
    conn = create_connection(self.target)
    conn.request("POST", url, body, headers)
    response = conn.getresponse()
    return response.status == 200

  def get(self, url):
    headers = {
      "Authorization": "bearer " + self.token,
     }
    conn = create_connection(self.target)
    conn.request("GET", url, None, headers)
    return conn.getresponse()

  def delete(self, url):
    headers = {
      "Authorization": "bearer " + self.token,
     }
    conn = create_connection(self.target)
    conn.request("DELETE", url, None, headers)
    return conn.getresponse()

  def swap(self, app1, app2, force=True):
    url = "/swap"
    body = "app1={}&app2={}&force={}&cnameOnly=true".format(app1, app2, str(force).lower())
    return self.post(url, body)

  def env_set(self, app, key, value):
    url = "/apps/{}/env".format(app)
    body =  "noRestart=true&Envs.0.Name={}&Envs.0.Value={}".format(key, value)
    return self.post(url, body)

  def env_get(self, app, key):
    url = "/apps/{}/env?env={}".format(app, key)
    response = self.get(url)
    data = json.loads(response.read())
    if data is None or len(data) == 0:
      return None
    return data[0].get("value")

  def total_units(self, app):
    response = self.get("/apps/{}".format(app))
    data = json.loads(response.read())

    units = {}
    for unit in data.get('units'):
        process_name = unit['ProcessName']
        if units.has_key(process_name):
            units[process_name] += 1
        else:
            units[process_name] = 1

    return units

  def remove_units(self, app, units_to_keep=0):
      total_units = self.total_units(app)
      results = []
      for process_name, units in total_units.iteritems():
          results.append(self.remove_units_per_process_type(app, units - units_to_keep, process_name))

      for result in results:
          if not result:
              return False

      return True

  def remove_units_per_process_type(self, app, units_to_remove, process_name):
    print """
  Removing %s '%s' units from %s ...""" % (units_to_remove, process_name, app)

    headers = {"Authorization" : "bearer " + self.token}
    conn = create_connection(self.target)
    conn.request("DELETE", "/apps/" + app + '/units?units=' + str(units_to_remove) + '&process=' + process_name, '', headers)
    response = conn.getresponse()
    if response.status != 200:
      max_tries = 3
      for i in range(max_tries):
        response.read() # This acts as a flush
        print "Error removing '%s' units from %s. Retrying %d..." % (process_name, app, i)
        time.sleep(30)
        conn.request("DELETE", "/apps/" + app + '/units?units=' + str(units_to_remove) + '&process=' + process_name, '', headers)
        response = conn.getresponse()
        if response.status == 200:
          return True
      return False
    else:
      return True

  def add_units(self, app, total_units_after_add):
    total_units = self.total_units(app)
    results = []
    for process_name, units in total_units_after_add.iteritems():
      if total_units.has_key(process_name):
        units_to_add = units - total_units[process_name]
      else:
        units_to_add = units

      if units_to_add > 0:
        results.append(self.add_units_per_process_type(app, units_to_add, units, process_name))

    for result in results:
      if not result:
        return False

    return True

  def add_units_per_process_type(self, app, units_to_add, total_units_after_add, process_name):
    print """
  Adding %s '%s' units to %s ...""" % (units_to_add, process_name, app)

    headers = {"Authorization" : "bearer " + self.token}
    conn = create_connection(self.target)
    conn.request("PUT", "/apps/" + app + '/units?units=' + str(units_to_add) + '&process=' + process_name, '', headers)
    response = conn.getresponse()
    response.read()
    if response.status != 200:
      print "Error adding '%s' units to %s. Aborting..." % (process_name, app)
      return False

    if (self.total_units(app)[process_name] != total_units_after_add):
      print "Error adding '%s' units to %s. Aborting..." % (process_name, app)
      return False
    return True

  def notify_newrelic(self,  tag):
    api_key = self.newrelic.get('api_key')
    app_id = self.newrelic.get('app_id')
    if api_key and app_id:
      print """
  Notifying New Relic app '%s' ...
      """ % (app_id)
      headers = {"Content-Type" : "application/x-www-form-urlencoded", "X-Api-Key" : api_key}
      url = "/v2/applications/" + app_id + "/deployments.json"
      body = 'deployment[application_id]=' + app_id + '&deployment[revision]=' + tag

      conn = httplib.HTTPConnection("api.newrelic.com")
      conn.request("POST", url, body, headers)
      response = conn.getresponse()
      return response.status == 200
    return False

  def notify_grafana(self, app, tag):
    endpoint = self.grafana.get('endpoint')
    index = self.grafana.get('index')

    if endpoint and index:
      print """
    Notifying deploy to Grafana ...
      """
      endpoint_host = urlparse(endpoint).hostname
      endpoint_path = urlparse(endpoint).path
      headers = {"Content-Type" : "application/json"}
      payload = {
        "title": "Deploy",
        "client": index,
        "annotation_type": "deploy",
        "description": app,
        "label": tag
      }

      conn = httplib.HTTPConnection(endpoint_host)
      conn.request("POST", (endpoint_path or '/'), json.dumps(payload), headers)
      response = conn.getresponse()
      return response.status == 200

  def run_webhook(self, tag):
    endpoint = self.webhook.get('endpoint')
    payload_extras = self.webhook.get('payload_extras')
    if endpoint and payload_extras:
      print """
  POSTING to WebHook '%s' ...
      """ % (endpoint)
      endpoint_host = urlparse(endpoint).hostname
      endpoint_path = urlparse(endpoint).path
      headers = {"Content-Type" : "application/x-www-form-urlencoded"}
      conn = httplib.HTTPConnection(endpoint_host)
      conn.request("POST", (endpoint_path or '/'), payload_extras + '&tag=' + tag, headers)
      response = conn.getresponse()
      return response.status == 200
    return False

  def run_command(self, command, env_vars=None):
    try:
      return_value = subprocess.call(command.split(' '), env=env_vars)
      return return_value == 0
    except:
      return False

  def run_hook(self, hook_name, env_vars=None):
    hook_command = self.hooks.get(hook_name)
    if hook_command:
      print """
  Running '%s' hook ...
      """ % (hook_name)
      return self.run_command(hook_command, env_vars)

    return True

  def deploy_pre(self, app, tag, app_deploy):
    print """
  Pre deploying tag:%s to %s ...
    """ % (tag, app)

    self.remove_units(app)

    self.env_set(app, 'TAG', tag)

    if not self.run_hook('before_pre', {"TAG": tag}):
        print """
  Error running 'before_pre' hook. Pre deploy aborted.
        """
        return 2

    deploy_arguments = ['git', 'push', '--force', app, "%s:master" % tag]

    if app_deploy:
      deploy_arguments = ['tsuru', 'app-deploy', '-a', app] + self.deploy_dir.split()

    process = subprocess.Popen(deploy_arguments, stdout=subprocess.PIPE)
    for line in iter(process.stdout.readline, ''):
      sys.stdout.write(line)

    process.communicate()

    deploy_status = process.returncode

    if not self.run_hook('after_pre', {"TAG": tag}):
        print """
  Error running 'after_pre' hook. Pre deploy aborted.
        """
        return 2

    return deploy_status

  def deploy_swap(self, apps, cname):
    print """
  Changing live application to %s ...""" % apps[1]

    tag = self.env_get(apps[1], 'TAG')

    if not self.run_hook('before_swap', {"TAG": tag}):
        print """
  Error running 'before_swap' hook. Pre deploy aborted.
        """
        return 2

    if not self.add_units(apps[1], self.total_units(apps[0])):
      return 2

    if not self.swap(apps[0], apps[1], False):
      print "\n  Error swaping {} and {}. Aborting...".format(apps[0], apps[1])
      self.remove_units(apps[1], 1)
      return 2

    self.remove_units(apps[0])

    print "\n  Apps {} and {} cnames successfullly swapped!".format(apps[0], apps[1])

    self.notify_newrelic(tag)

    self.notify_grafana(apps[1], tag)

    self.run_webhook(tag)

    if not self.run_hook('after_swap', {"TAG": tag}):
      print """
Error running 'after_swap' hook.
        """
      return 2

    return 0


class Config:
  @classmethod
  def load(self, filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)

    app_name = config.get('Application', 'name')

    try:
      deploy_dir = config.get('Application', 'deploy_dir')
    except ConfigParser.NoOptionError:
      deploy_dir = None

    hooks = {
      'before_pre': None,
      'after_pre': None,
      'before_swap': None,
      'after_swap': None
    }
    for key in hooks:
      try:
        hook_value = config.get('Hooks', key)
        if hook_value:
          hooks[key] = hook_value

      except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        pass

    #NewRelic
    newrelic = {
      'api_key': None,
      'app_id': None
    }

    for key in newrelic:
      try:
        newrelic_value = config.get('NewRelic', key)
        if newrelic_value:
          newrelic[key] = newrelic_value
        else:
          newrelic[key] = os.getenv('NEW_RELIC_' + key.upper())

      except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        pass

    #Grafana
    grafana = {
      'endpoint': None,
      'index': None
    }

    for key in grafana:
      try:
        grafana_value = config.get('Grafana', key)
        if grafana_value:
          grafana[key] = grafana_value

      except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        pass

    #WebHook
    webhook = {
      'endpoint': None,
      'payload_extras': None
    }

    for key in webhook:
      try:
        webhook_value = config.get('WebHook', key)
        if webhook_value:
          webhook[key] = webhook_value

      except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        pass

    return {'name' : app_name, 'deploy_dir' : deploy_dir , 'hooks' : hooks, 'newrelic' : newrelic, 'grafana' : grafana, 'webhook' : webhook}

if __name__ == "__main__":
  #Parameters
  parser = argparse.ArgumentParser(description='Tsuru blue-green deployment (pre and live).',
                                   usage='tsuru bluegreen action [options]')

  parser.add_argument('action', metavar='action', help='pre or swap', choices=['pre', 'swap', 'cname'])
  parser.add_argument('-t', '--tag', metavar='TAG', help='Tag to be deployed (default: master)', nargs='?', default="master")

  args = parser.parse_args()

  #Initialization
  token = os.environ['TSURU_TOKEN']
  target = os.environ['TSURU_TARGET']

  config = Config.load('tsuru-bluegreen.ini')

  app_name = config['name']
  blue = "%s-blue" % app_name
  green = "%s-green" % app_name

  bluegreen = BlueGreen(token, target, config)

  apps = [blue, green]
  cnames = [bluegreen.get_cname(green), bluegreen.get_cname(blue)]

  #reverse if first is not None
  if cnames[0] is not None:
    cnames.reverse()
    apps.reverse()

  cname = cnames[1]
  pre = apps[1]

  app_deploy = config['deploy_dir'] != None

  if args.action == 'pre':
    sys.exit(bluegreen.deploy_pre(pre, args.tag, app_deploy))
  elif args.action == 'cname':
    print bluegreen.get_cname(apps[0])
  elif args.action == 'swap':
    sys.exit(bluegreen.deploy_swap(apps, cname))
