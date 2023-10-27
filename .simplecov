require 'simplecov'
require 'simplecov-cobertura'
require "simplecov-html"

# frozen_string_literal: true

# SimpleCov.formatter = SimpleCov::Formatter::CoberturaFormatter  # Converts the `.resultset.json` to `coverage.xml`

# Use multiple formatters
SimpleCov.formatters = SimpleCov::Formatter::MultiFormatter.new([
  SimpleCov::Formatter::SimpleFormatter,
  SimpleCov::Formatter::CoberturaFormatter,
  SimpleCov::Formatter::HTMLFormatter,
])


# .simplecov
SimpleCov.start 'rails' do
  command_name 'Unit Tests'
  enable_coverage :branch
  primary_coverage :branch
  add_filter %r{^/snippets/}
  add_filter %r{^/.git/}
  add_filter %r{^/tests/}
  add_filter "pkg/test.sh"
  add_group "Pkg scripts", "/pkg"

  enable_coverage_for_eval # Must be at the bottom and Must be here, even though it throws a 'command not found' error
end