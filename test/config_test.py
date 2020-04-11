import os
import unittest
from mock import MagicMock
from mock import Mock
from bluegreen import BlueGreen, Config

class TestConfig(unittest.TestCase):

  def setUp(self):
    self.config = Config.load('test/tsuru-bluegreen.ini')

  def test_load_app_name(self):
    self.assertEqual('app-test', self.config['name'])

  def test_load_defined_hooks(self):
    self.assertEqual('before_pre.sh', self.config['hooks']['before_pre'])
    self.assertEqual('live.sh', self.config['hooks']['after_swap'])

  def test_load_undefined_hooks(self):
    self.assertEqual(None, self.config['hooks']['after_pre'])
    self.assertEqual(None, self.config['hooks']['before_swap'])

  def test_load_newrelic_config(self):
    self.assertEqual('some-api-key', self.config['newrelic']['api_key'])
    self.assertEqual('123', self.config['newrelic']['app_id'])

  def test_load_newrelic_with_environment_variables(self):
    os.environ['NEW_RELIC_API_KEY'] = 'api-key-from-environment'
    os.environ['NEW_RELIC_APP_ID'] = 'app-id-from-environment'
    self.config = Config.load('test/new-relic-with-blank-values.ini')

    self.assertEqual('api-key-from-environment', self.config['newrelic']['api_key'])
    self.assertEqual('app-id-from-environment', self.config['newrelic']['app_id'])

    del os.environ['NEW_RELIC_API_KEY']
    del os.environ['NEW_RELIC_APP_ID']

  def test_load_grafana_config(self):
    self.assertEqual('http://tcp.logstash.example.com', self.config['grafana']['endpoint'])
    self.assertEqual('test-index', self.config['grafana']['index'])

  def test_load_webhook_config(self):
    self.assertEqual('http://example.com', self.config['webhook']['endpoint'])
    self.assertEqual('key1=value1&key2=value2', self.config['webhook']['payload_extras'])

  def test_load_app_deploy_config(self):
    self.assertEqual("'.'", self.config['deploy_dir'])
