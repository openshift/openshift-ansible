#!/usr/bin/env ruby

require 'thor'
require_relative 'lib/gce_command'
require_relative 'lib/aws_command'

# Don't buffer output to the client
STDOUT.sync = true
STDERR.sync = true

module OpenShift
  module Ops
    class CloudCommand < Thor
      desc 'gce', 'Manages Google Compute Engine assets'
      subcommand "gce", GceCommand

      desc 'aws', 'Manages Amazon Web Services assets'
      subcommand "aws", AwsCommand
    end
  end
end

if __FILE__ == $0
  SCRIPT_DIR = File.expand_path(File.dirname(__FILE__))
  Dir.chdir(SCRIPT_DIR) do
    # Kick off thor
    OpenShift::Ops::CloudCommand.start(ARGV)
  end
end
