require 'thor'
require 'securerandom'
require 'fileutils'

require_relative 'gce_helper'
require_relative 'launch_helper'
require_relative 'ansible_helper'

module OpenShift
  module Ops
    class GceCommand < Thor
      # WARNING: we do not currently support environments with hyphens in the name
      SUPPORTED_ENVS = %w(prod stg int twiest gshipley kint test jhonce amint tdint lint)

      option :type, :required => true, :enum => LaunchHelper.get_gce_host_types,
             :desc => 'The host type of the new instances.'
      option :env, :required => true, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment of the new instances.'
      option :count, :default => 1, :aliases => '-c', :type => :numeric,
             :desc => 'The number of instances to create'
      option :tag, :type => :array,
             :desc => 'The tag(s) to add to the new instances. Allowed characters are letters, numbers, and hyphens.'
      desc "launch", "Launches instances."
      def launch()
        # Expand all of the instance names so that we have a complete array
        names = []
        options[:count].times { names << "#{options[:env]}-#{options[:type]}-#{SecureRandom.hex(5)}" }

        ah = AnsibleHelper.for_gce()

        # GCE specific configs
        ah.extra_vars['oo_new_inst_names'] = names
        ah.extra_vars['oo_new_inst_tags'] = options[:tag]
        ah.extra_vars['oo_env'] = options[:env]

        # Add a created by tag
        ah.extra_vars['oo_new_inst_tags'] = [] if ah.extra_vars['oo_new_inst_tags'].nil?

        ah.extra_vars['oo_new_inst_tags'] << "created-by-#{ENV['USER']}"
        ah.extra_vars['oo_new_inst_tags'] << GceHelper.generate_env_tag(options[:env])
        ah.extra_vars['oo_new_inst_tags'] << GceHelper.generate_host_type_tag(options[:type])
        ah.extra_vars['oo_new_inst_tags'] << GceHelper.generate_env_host_type_tag(options[:env], options[:type])

        puts
        puts "Creating #{options[:count]} #{options[:type]} instance(s) in GCE..."

        ah.run_playbook("playbooks/gce/#{options[:type]}/launch.yml")
      end


      option :name, :required => false, :type => :string,
             :desc => 'The name of the instance to configure.'
      option :env, :required => false, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment of the new instances.'
      option :type, :required => false, :enum => LaunchHelper.get_gce_host_types,
             :desc => 'The type of the instances to configure.'
      desc "config", 'Configures instances.'
      def config()
        ah = AnsibleHelper.for_gce()

        abort 'Error: you can\'t specify both --name and --type' unless options[:type].nil? || options[:name].nil?

        abort 'Error: you can\'t specify both --name and --env' unless options[:env].nil? || options[:name].nil?

        host_type = nil
        if options[:name]
          details = GceHelper.get_host_details(options[:name])
          ah.extra_vars['oo_host_group_exp'] = options[:name]
          ah.extra_vars['oo_env'] = details['env']
          host_type = details['host-type']
        elsif options[:type] && options[:env]
          oo_env_host_type_tag = GceHelper.generate_env_host_type_tag_name(options[:env], options[:type])
          ah.extra_vars['oo_host_group_exp'] = "groups['#{oo_env_host_type_tag}']"
          ah.extra_vars['oo_env'] = options[:env]
          host_type = options[:type]
        else
          abort 'Error: you need to specify either --name or (--type and --env)'
        end

        puts
        puts "Configuring #{options[:type]} instance(s) in GCE..."

        ah.run_playbook("playbooks/gce/#{host_type}/config.yml")
      end

      option :name, :required => false, :type => :string,
             :desc => 'The name of the instance to terminate.'
      option :env, :required => false, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment of the new instances.'
      option :type, :required => false, :enum => LaunchHelper.get_gce_host_types,
             :desc => 'The type of the instances to configure.'
      option :confirm, :required => false, :type => :boolean,
             :desc => 'Terminate without interactive confirmation'
      desc "terminate", 'Terminate instances'
      def terminate()
        ah = AnsibleHelper.for_gce()

        abort 'Error: you can\'t specify both --name and --type' unless options[:type].nil? || options[:name].nil?

        abort 'Error: you can\'t specify both --name and --env' unless options[:env].nil? || options[:name].nil?

        host_type = nil
        if options[:name]
          details = GceHelper.get_host_details(options[:name])
          ah.extra_vars['oo_host_group_exp'] = options[:name]
          ah.extra_vars['oo_env'] = details['env']
          host_type = details['host-type']
        elsif options[:type] && options[:env]
          oo_env_host_type_tag = GceHelper.generate_env_host_type_tag_name(options[:env], options[:type])
          ah.extra_vars['oo_host_group_exp'] = "groups['#{oo_env_host_type_tag}']"
          ah.extra_vars['oo_env'] = options[:env]
          host_type = options[:type]
        else
          abort 'Error: you need to specify either --name or (--type and --env)'
        end

        puts
        puts "Terminating #{options[:type]} instance(s) in GCE..."

        ah.run_playbook("playbooks/gce/#{host_type}/terminate.yml")
      end

      option :env, :required => false, :aliases => '-e', :enum => SUPPORTED_ENVS,
             :desc => 'The environment to list.'
      desc "list", "Lists instances."
      def list()
        hosts = GceHelper.get_hosts()

        hosts.delete_if { |h| h.env != options[:env] } unless options[:env].nil?

        fmt_str = "%34s %5s %8s %17s %7s"

        puts
        puts fmt_str % ['Name','Env', 'State', 'IP Address', 'Created By']
        puts fmt_str % ['----','---', '-----', '----------', '----------']
        hosts.each { |h| puts fmt_str % [h.name, h.env, h.state, h.public_ip, h.created_by ] }
        puts
      end

      option :file, :required => true, :type => :string,
             :desc => 'The name of the file to copy.'
      option :dest, :required => false, :type => :string,
             :desc => 'A relative path where files are written to.'
      desc "scp_from", "scp files from an instance"
      def scp_from(*ssh_ops, host)
        if host =~ /^([\w\d_.-]+)@([\w\d-_.]+)$/
          user = $1
          host = $2
        end

        path_to_file = options['file']
        dest = options['dest']

        details = GceHelper.get_host_details(host)
        abort "\nError: Instance [#{host}] is not RUNNING\n\n" unless details['gce_status'] == 'RUNNING'

        cmd = "scp #{ssh_ops.join(' ')}"

        if user.nil?
          cmd += " "
        else
          cmd += " #{user}@"
        end

        if dest.nil?
          download = File.join(Dir.pwd, 'download')
          FileUtils.mkdir_p(download) unless File.exists?(download)
          cmd += "#{details['gce_public_ip']}:#{path_to_file} download/"
        else
          cmd += "#{details['gce_public_ip']}:#{path_to_file} #{File.expand_path(dest)}"
        end

        exec(cmd)
      end

      desc "ssh", "Ssh to an instance"
      def ssh(*ssh_ops, host)
        if host =~ /^([\w\d_.-]+)@([\w\d-_.]+)/
          user = $1
          host = $2
        end

        details = GceHelper.get_host_details(host)
        abort "\nError: Instance [#{host}] is not RUNNING\n\n" unless details['gce_status'] == 'RUNNING'

        cmd = "ssh #{ssh_ops.join(' ')}"

        if user.nil?
          cmd += " "
        else
          cmd += " #{user}@"
        end

        cmd += "#{details['gce_public_ip']}"

        exec(cmd)
      end

      option :name, :required => true, :aliases => '-n', :type => :string,
             :desc => 'The name of the instance.'
      desc 'details', 'Displays details about an instance.'
      def details()
        name = options[:name]

        details = GceHelper.get_host_details(name)

        key_size = details.keys.max_by { |k| k.size }.size

        header = "Details for #{name}"
        puts
        puts header
        header.size.times { print '-' }
        puts
        details.each { |k,v| printf("%#{key_size + 2}s: %s\n", k, v) }
        puts
      end

      desc 'types', 'Displays instance types'
      def types()
        puts
        puts "Available Host Types"
        puts "--------------------"
        LaunchHelper.get_gce_host_types.each { |t| puts "  #{t}" }
        puts
      end
    end
  end
end
