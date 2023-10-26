# test/test_helper.rb
require 'simplecov'
require "simplecov_json_formatter"

# frozen_string_literal: true



# .simplecov
SimpleCov.start 'rails' do
  # any custom configs like groups and filters can be here at a central place
  command_name 'Unit Tests'
  enable_coverage :branch
  primary_coverage :branch
  enable_coverage_for_eval # Doesnt work, but breaks if disabled
  add_filter %r{^/.git/}
  add_filter %r{^/snippets/}
  add_filter %r{^/tests/}
  add_filter "pkg/test.sh"
  # add_filter "/pkg/test.sh"
  add_group "Pkg scripts", "/pkg"
  
# Converts the `.resultset.json` to `coverage.json`
  formatter = SimpleCov::Formatter::JSONFormatter
end