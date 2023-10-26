require 'simplecov'
require "simplecov_json_formatter"

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
  # formatter = SimpleCov::Formatter::JSONFormatter

  # collate Dir["simplecov-resultset-*/.resultset.json"]
  # track_files 
end