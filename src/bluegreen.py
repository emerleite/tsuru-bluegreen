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

def get_cname(app):
  headers = {"Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("GET", "/apps/" + app, "", headers)
  response = conn.getresponse()
  data = json.loads(response.read())
  if len(data.get("cname")) == 0:
    return None
  return data.get("cname")

def remove_cname(app, cname):
  headers = {"Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("DELETE", "/apps/" + app + '/cname', '{"cname": ' + json.dumps(cname) + '}', headers)
  response = conn.getresponse()
  if response.status != 200:
    return False
  return True

def set_cname(app, cname):
  headers = {"Content-Type" : "application/json", "Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("POST", "/apps/" + app + '/cname', '{"cname": ' + json.dumps(cname) + '}', headers)
  response = conn.getresponse()
  if response.status != 200:
    return False
  return True

def deploy_pre(app, tag):
  print """
Pre deploying tag:%s to %s ...
  """ % (tag, app)

  process = subprocess.Popen(['git', 'push', app, "%s:master" % tag], stdout=subprocess.PIPE)
  for line in iter(process.stdout.readline, ''):
    sys.stdout.write(line)

def deploy_swap(apps, cname):
  print """
Changing live application to %s ...""" % apps[1]

  if not add_units(apps[1], production_instances):
    sys.exit()

  if not remove_cname(apps[0], cname):
    print "Error removing cname of %s. Aborting..." % apps[0]
    remove_units(apps[1])
    sys.exit()

  if set_cname(apps[1], cname):
    remove_units(apps[0])

    print """
Application %s is live at %s ...
    """ % (apps[1], ','.join(cname))

  else:
    print "Error adding cname of %s. Aborting..." % apps[1]
    set_cname(apps[0], cname)
    remove_units(apps[1])

def add_units(app, current_units):
  units = str(int(current_units) - total_units(app))
  print """
Adding %s units to %s ...""" % (units, app)

  headers = {"Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("PUT", "/apps/" + app + '/units', units, headers)
  response = conn.getresponse()
  if response.status != 200:
    print "Error adding units to %s. Aborting..." % app
    return False
  return True

def remove_units(app):
  units = str(total_units(app)-1)
  print """
Removing %s units from %s ...""" % (units, app)

  headers = {"Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("DELETE", "/apps/" + app + '/units', units, headers)
  response = conn.getresponse()
  if response.status != 200:
    print "Error removing units from %s. You'll need to remove manually." % app
    return False

  while (total_units(app) > 1):
    print "Waiting for %s units to go down..." % app
    time.sleep(1)
  return True

def total_units(app):
  headers = {"Authorization" : "bearer " + token}
  conn = httplib.HTTPConnection(target)
  conn.request("GET", "/apps/" + app, "", headers)
  response = conn.getresponse()
  data = json.loads(response.read())
  return len(data.get('units'))

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

  #Load configuration
  config = ConfigParser.ConfigParser()
  config.read('tsuru-bluegreen.ini')

  app_name = config.get('Application', 'name')
  production_instances = config.get('Application', 'units')

  blue = "%s-blue" % app_name
  green = "%s-green" % app_name

  apps = [blue, green]
  cnames = [get_cname(green), get_cname(blue)]

  #reverse if first is not None
  if cnames[0] is not None:
    cnames.reverse()
    apps.reverse()

  cname = cnames[1]
  pre = apps[1]

  if args.action == 'pre':
    deploy_pre(pre, args.tag)
  elif args.action == 'swap':
    deploy_swap(apps, cname)
