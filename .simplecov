# test/test_helper.rb
require 'simplecov'
require "simplecov_json_formatter"

# frozen_string_literal: true


SimpleCov.formatter = SimpleCov::Formatter::JSONFormatter

# .simplecov
SimpleCov.start 'rails' do
  # any custom configs like groups and filters can be here at a central place
  command_name 'Unit Tests'
  add_filter %r{^/.git/}
  add_filter %r{^/snippets/}
  add_filter %r{^/tests/}
  add_filter "pkg/test.sh"
  # add_filter "/pkg/test.sh"
  add_group "Pkg scripts", "/pkg"

  # collate Dir["simplecov-resultset-*/.resultset.json"]
  # track_files 
end