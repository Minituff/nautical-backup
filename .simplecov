# test/test_helper.rb
require 'simplecov'

# frozen_string_literal: true


# .simplecov
SimpleCov.start 'rails' do
  # any custom configs like groups and filters can be here at a central place
  command_name 'Unit Tests'
  enable_coverage_for_eval
  add_filter %r{^/.git/}
  add_filter %r{^/snippets/}
  add_filter %r{^/tests/}
  add_filter "pkg/test.sh"
  # add_filter "/pkg/test.sh"
  add_group "Pkg scripts", "/pkg"
end