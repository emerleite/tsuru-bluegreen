$:.unshift(File.join(File.dirname(__FILE__), "..", "lib"))

require 'simplecov'
SimpleCov.start

require 'webmock/rspec'
require 'bluegreen'
