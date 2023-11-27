require 'simplecov'
require 'simplecov-cobertura'
require "simplecov-html"

# frozen_string_literal: true

# SimpleCov.formatter = SimpleCov::Formatter::CoberturaFormatter  # Converts the `.resultset.json` to `coverage.xml`

# SimpleCov::Formatter::JSONFormatter, # This formatter breaks the build

# Use multiple formatters
SimpleCov.formatters = SimpleCov::Formatter::MultiFormatter.new([
  SimpleCov::Formatter::SimpleFormatter,
  SimpleCov::Formatter::CoberturaFormatter,
  SimpleCov::Formatter::HTMLFormatter,
])


# .simplecov
SimpleCov.profiles.define 'bashcov' do
  filters.clear # This will remove the :root_filter and :bundler_filter that come via simplecov's defaults
  load_profile 'rails'
  command_name 'Unit Tests'
  enable_coverage :branch
  primary_coverage :branch

  # Remove any .sh files that start with "_"
  add_filter %r{^/_.*.sh}

  # These are not run from the unit test suite
  add_filter %r{^/.*utils.sh}

  # simplecov 0.22.0+
  enable_coverage_for_eval if respond_to? :enable_coverage_for_eval
end

# Conditional loading of profiles
if ENV.key? 'SKIP_PROFILE'
  puts "Skipping bashcov profile..."
else
  puts "--- Loading bashcov configurations ---"
  SimpleCov.load_profile 'bashcov'
end