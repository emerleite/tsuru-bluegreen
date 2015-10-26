#!/usr/bin/env python

import os
import sys
import httplib
import json
import subprocess
import ConfigParser
import argparse
import time
from urlparse import urlparse

class BlueGreen:
  def __init__(self, token, target, config):
    self.token = token
    self.target = target
    self.app_name = config['name']
    try:
      self.hooks = config['hooks']
    except KeyError:
      self.hooks = {}

  def get_cname(self, app):
    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("GET", "/apps/" + app, "", headers)
    response = conn.getresponse()
    data = json.loads(response.read())
    if len(data.get("cname")) == 0:
      return None
    return data.get("cname")

  def remove_cname(self, app, cname):
    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("DELETE", "/apps/" + app + '/cname', '{"cname": ' + json.dumps(cname) + '}', headers)
    response = conn.getresponse()
    return response.status == 200

  def set_cname(self, app, cname):
    headers = {"Content-Type" : "application/json", "Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("POST", "/apps/" + app + '/cname', '{"cname": ' + json.dumps(cname) + '}', headers)
    response = conn.getresponse()
    return response.status == 200

  def env_set(self, app, key, value):
    headers = {"Content-Type" : "application/json", "Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("POST", "/apps/" + app + '/env', '{"' + key + '": "' + value + '"}', headers)
    response = conn.getresponse()
    return response.status == 200

  def env_get(self, app, key):
    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("GET", "/apps/" + app + '/env', '["' + key + '"]', headers)
    response = conn.getresponse()
    data = json.loads(response.read())
    if data is None or len(data) == 0:
      return None
    return data[0].get("value")

  def total_units(self, app):
    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("GET", "/apps/" + app, "", headers)
    response = conn.getresponse()
    data = json.loads(response.read())
    return len(data.get('units'))

  def remove_units(self, app, keep=0):
    units = str(self.total_units(app) - keep)
    print """
  Removing %s units from %s ...""" % (units, app)

    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("DELETE", "/apps/" + app + '/units?units='+units, units, headers)
    response = conn.getresponse()
    if response.status != 200:
      print "Error removing units from %s. You'll need to remove manually." % app
      return False

    while (self.total_units(app) > 1):
      print "Waiting for %s units to go down..." % app
      time.sleep(1)
    return True

  def add_units(self, app, current_units):
    units = str(int(current_units) - self.total_units(app))
    print """
  Adding %s units to %s ...""" % (units, app)

    headers = {"Authorization" : "bearer " + self.token}
    conn = httplib.HTTPConnection(self.target)
    conn.request("PUT", "/apps/" + app + '/units?units='+units, units, headers)
    response = conn.getresponse()
    response.read()
    if response.status != 200:
      print "Error adding units to %s. Aborting..." % app
      return False

    if (self.total_units(app) != int(current_units)):
      print "Error adding units to %s. Aborting..." % app
      return False
    return True

  def run_command(self, command, env_vars=None):
    DEVNULL = open(os.devnull, 'wb')

    try:
      return_value = subprocess.call(command.split(' '), stdout=DEVNULL, stderr=DEVNULL, env=env_vars)
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

  def deploy_pre(self, app, tag):
    print """
  Pre deploying tag:%s to %s ...
    """ % (tag, app)

    self.remove_units(app)

    self.env_set(app, 'TAG', tag)

    if not self.run_hook('before_pre', {"TAG": tag}):
        print """
  Error running 'before' hook. Pre deploy aborted.
        """
        return

    process = subprocess.Popen(['git', 'push', '--force', app, "%s:master" % tag], stdout=subprocess.PIPE)
    for line in iter(process.stdout.readline, ''):
      sys.stdout.write(line)

    if not self.run_hook('after_pre', {"TAG": tag}):
        print """
  Error running 'after' hook. Pre deploy aborted.
        """

  def deploy_swap(self, apps, cname):
    print """
  Changing live application to %s ...""" % apps[1]

    tag = self.env_get(apps[1], 'TAG')

    if not self.run_hook('before_swap', {"TAG": tag}):
        print """
  Error running 'before' hook. Pre deploy aborted.
        """
        return

    if not self.add_units(apps[1], self.total_units(apps[0])):
      sys.exit()

    if not self.remove_cname(apps[0], cname):
      print "Error removing cname of %s. Aborting..." % apps[0]
      self.remove_units(apps[1], 1)
      sys.exit()

    if self.set_cname(apps[1], cname):
      self.remove_units(apps[0])

      print """
  Application %s is live at %s ...
      """ % (apps[1], ','.join(cname))

      if not self.run_hook('after_swap', {"TAG": tag}):
          print """
  Error running 'before' hook. Pre deploy aborted.
          """

    else:
      print "Error adding cname of %s. Aborting..." % apps[1]
      self.set_cname(apps[0], cname)
      self.remove_units(apps[1], 1)


class Config:
  @classmethod
  def load(self, filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)

    app_name = config.get('Application', 'name')

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

    return {'name' : app_name, 'hooks' : hooks}


if __name__ == "__main__":
  #Initialization
  token = os.environ['TSURU_TOKEN']
  target = urlparse(os.environ['TSURU_TARGET']).hostname

  #Parameters
  parser = argparse.ArgumentParser(description='Tsuru blue-green deployment (pre and live).',
                                   usage='tsuru bluegreen action [options]')

  parser.add_argument('action', metavar='action', help='pre or swap', choices=['pre', 'swap'])
  parser.add_argument('-t', '--tag', metavar='TAG', help='Tag to be deployed (default: master)', nargs='?', default="master")

  args = parser.parse_args()

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

  if args.action == 'pre':
    bluegreen.deploy_pre(pre, args.tag)
  elif args.action == 'swap':
    bluegreen.deploy_swap(apps, cname)
