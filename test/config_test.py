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
