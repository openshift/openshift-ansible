require 'thor'

require_relative 'aws_helper'
require_relative 'launch_helper'

module OpenShift
  module Ops
    class AwsCommand < Thor
      # WARNING: we do not currently support environments with hyphens in the name
      SUPPORTED_ENVS = %w(prod stg int tint kint test jint amint tdint lint)

      option :type, :required => true, :enum => LaunchHelper.get_aws_host_types,
             :desc => 'The host type of the new instances.'
      option :env, :required => true, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment of the new instances.'
      option :count, :default => 1, :aliases => '-c', :type => :numeric,
             :desc => 'The number of instances to create'
      option :tag, :type => :array,
             :desc => 'The tag(s) to add to the new instances. Allowed characters are letters, numbers, and hyphens.'
      desc "launch", "Launches instances."
      def launch()
        aws_helper = AwsHelper.new(:launch, options)

        ah = AnsibleHelper.for_aws()
        ah.extra_vars = aws_helper.extra_vars

        puts
        puts "Creating #{options[:count]} #{options[:type]} instance(s) in AWS..."
        ah.ignore_bug_6407

        # Make sure we're completely up to date before launching
        aws_helper.clear_inventory_cache
        ah.run_playbook("playbooks/aws/#{options[:type]}/launch.yml")
      ensure
        # This is so that if we a config right after a launch, the newly launched instances will be
        # in the list.
        aws_helper.clear_inventory_cache
      end

      desc "clear-cache", 'Clear the inventory cache'
      def clear_cache()
        print "Clearing inventory cache... "
        AwsHelper.new.clear_inventory_cache
        puts "Done."
      end

      option :name, :required => false, :type => :string,
             :desc => 'The name of the instance to configure.'
      option :env, :required => false, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment of the new instances.'
      option :type, :required => false, :enum => LaunchHelper.get_aws_host_types,
             :desc => 'The type of the instances to configure.'
      desc "config", 'Configures instances.'
      def config()
        config_task = nil
        if options[:name]
          abort 'Error you can\'t specify --type or --env when you specify --name' if options[:type] || options[:env]
          config_task = :config_host
        elsif options[:type] && options[:env]
          abort 'Error you can\'t specify --name when you specify --type and --env' if options[:name]
          config_task = :config_type_env
        else
          abort 'Error: you need to specify either --name or (--type and --env)'
        end

        aws_helper = AwsHelper.new(config_task, options)
        ah = AnsibleHelper.for_aws()

        host_type = options[:name].nil? ? options[:type] : aws_helper.get_host_type(options[:name])

        puts
        puts "Configuring #{options[:type]} instance(s) in AWS..."
        ah.ignore_bug_6407

        ah.run_playbook("playbooks/aws/#{host_type}/config.yml")
      end

      option :env, :required => false, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment to list.'
      desc "list", "Lists instances."
      def list()
        hosts = AwsHelper.new(:list, options).get_hosts

        fmt_str = "%34s %5s %8s %17s %7s"

        puts
        puts fmt_str % ['Name','Env', 'State', 'IP Address', 'Created By']
        puts fmt_str % ['----','---', '-----', '----------', '----------']
        hosts.each { |h| puts fmt_str % [h.name, h.env, h.state, h.public_ip, h.created_by ] }
        puts
      end

      desc "ssh", "Ssh to an instance"
      def ssh(*ssh_ops, host)
        if host =~ /^([\w\d_.-]+)@([\w\d-_.]+)/
          user = $1
          host = $2
        end

        details = AwsHelper.new(:ssh, options).get_host_details(host)
        abort "\nError: Instance [#{host}] is not RUNNING\n\n" unless details['ec2_state'] == 'running'

        cmd = "ssh #{ssh_ops.join(' ')}"

        if user.nil?
          cmd += " "
        else
          cmd += " #{user}@"
        end

        cmd += "#{details['ec2_ip_address']}"

        exec(cmd)
      end

      desc 'types', 'Displays instance types'
      def types()
        puts
        puts "Available Host Types"
        puts "--------------------"
        LaunchHelper.get_aws_host_types.each { |t| puts "  #{t}" }
        puts
      end
    end
  end
end
