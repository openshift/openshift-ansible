#!/usr/bin/env ruby

require 'thor'
require 'json'
require 'yaml'
require 'securerandom'
require 'fileutils'
require 'parseconfig'
require 'open3'

# Don't buffer output to the client
STDOUT.sync = true
STDERR.sync = true

SCRIPT_DIR = File.expand_path(File.dirname(__FILE__))

module OpenShift
  module Ops
    # WARNING: we do not currently support environments with hyphens in the name
    SUPPORTED_ENVS = %w(prod stg int tint kint test jint)

    class GceHelper
      def self.list_hosts()
        cmd = "#{SCRIPT_DIR}/inventory/gce/gce.py --list"
        hosts = %x[#{cmd} 2>&1]

        raise "Error: failed to list hosts\n#{hosts}" unless $?.exitstatus == 0

        return JSON.parse(hosts)
      end

      def self.get_host_details(host)
        cmd = "#{SCRIPT_DIR}/inventory/gce/gce.py --host #{host}"
        details = %x[#{cmd} 2>&1]

        raise "Error: failed to get host details\n#{details}" unless $?.exitstatus == 0

        retval = JSON.parse(details)

        # Convert OpenShift specific tags to entries
        retval['gce_tags'].each do |tag|
          if tag =~ /\Ahost-type-([\w\d-]+)\z/
            retval['host-type'] = $1
          end

          if tag =~ /\Aenv-([\w\d]+)\z/
            retval['env'] = $1
          end
        end

        return retval
      end

      def self.generate_env_tag(env)
        return "env-#{env}"
      end

      def self.generate_env_tag_name(env)
        return "tag_#{generate_env_tag(env)}"
      end

      def self.generate_host_type_tag(host_type)
        return "host-type-#{host_type}"
      end

      def self.generate_host_type_tag_name(host_type)
        return "tag_#{generate_host_type_tag(host_type)}"
      end

      def self.generate_env_host_type_tag(env, host_type)
        return "env-host-type-#{env}-#{host_type}"
      end

      def self.generate_env_host_type_tag_name(env, host_type)
        return "tag_#{generate_env_host_type_tag(env, host_type)}"
      end
    end

    class LaunchHelper
      def self.expand_name(name)
        return [name] unless name =~ /^([a-zA-Z0-9\-]+)\{(\d+)-(\d+)\}$/

        # Regex matched, so grab the values
        start_num = $2
        end_num = $3

        retval = []
        start_num.upto(end_num) do |i|
          retval << "#{$1}#{i}"
        end

        return retval
      end

      def self.get_gce_host_types()
        return Dir.glob("#{SCRIPT_DIR}/playbooks/gce/*").map { |d| File.basename(d) }
      end
    end

    class AnsibleHelper
      attr_accessor :inventory, :extra_vars, :verbosity, :pipelining

      def initialize(extra_vars={}, inventory=nil)
        @extra_vars = extra_vars
        @verbosity = '-vvvv'
        @pipelining = true
      end

      def all_eof(files)
        files.find { |f| !f.eof }.nil?
      end

      def run_playbook(playbook)
        @inventory = 'inventory/hosts' if @inventory.nil?

        # This is used instead of passing in the json on the cli to avoid quoting problems
        tmpfile    = Tempfile.open('extra_vars') { |f| f.write(@extra_vars.to_json); f}

        cmds = []

        #cmds << 'set -x'
        cmds << %Q[export ANSIBLE_FILTER_PLUGINS="#{Dir.pwd}/filter_plugins"]

        # We need this for launching instances, otherwise conflicting keys and what not kill it
        cmds << %q[export ANSIBLE_TRANSPORT="ssh"]
        cmds << %q[export ANSIBLE_SSH_ARGS="-o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"]

        # We need pipelining off so that we can do sudo to enable the root account
        cmds << %Q[export ANSIBLE_SSH_PIPELINING='#{@pipelining.to_s}']
        cmds << %Q[time -p ansible-playbook -i #{@inventory} #{@verbosity} #{playbook} --extra-vars '@#{tmpfile.path}']

        cmd = cmds.join(' ; ')

        pid = spawn(cmd, :out => $stdout, :err => $stderr, :close_others => true)
        _, state = Process.wait2(pid)

        if 0 != state.exitstatus
          raise %Q[Warning failed with exit code: #{state.exitstatus}

#{cmd}

extra_vars: #{@extra_vars.to_json}
]
        end
      ensure
        tmpfile.unlink if tmpfile
      end

      def merge_extra_vars_file(file)
        vars = YAML.load_file(file)
        @extra_vars.merge!(vars)
      end

      def self.for_gce
        ah      = AnsibleHelper.new

        # GCE specific configs
        gce_ini = "#{SCRIPT_DIR}/inventory/gce/gce.ini"
        config  = ParseConfig.new(gce_ini)

        if config['gce']['gce_project_id'].to_s.empty?
          raise %Q['gce_project_id' not set in #{gce_ini}]
        end
        ah.extra_vars['gce_project_id'] = config['gce']['gce_project_id']

        if config['gce']['gce_service_account_pem_file_path'].to_s.empty?
          raise %Q['gce_service_account_pem_file_path' not set in #{gce_ini}]
        end
        ah.extra_vars['gce_pem_file'] = config['gce']['gce_service_account_pem_file_path']

        if config['gce']['gce_service_account_email_address'].to_s.empty?
          raise %Q['gce_service_account_email_address' not set in #{gce_ini}]
        end
        ah.extra_vars['gce_service_account_email'] = config['gce']['gce_service_account_email_address']

        ah.inventory = 'inventory/gce/gce.py'
        return ah
      end

      def ignore_bug_6407
        puts
        puts %q[ .----  Spurious warning "It is unnecessary to use '{{' in loops" (ansible bug 6407)  ----.]
        puts %q[ V                                                                                        V]
      end

    end

    class GceCommand < Thor

      option :type, :required => true, :enum => LaunchHelper.get_gce_host_types,
             :desc => 'The host type of the new instances.'
      option :env, :required => true, :aliases => '-e', :enum => OpenShift::Ops::SUPPORTED_ENVS,
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
        puts 'Creating instance(s) in GCE...'
        ah.ignore_bug_6407

        ah.run_playbook("playbooks/gce/#{options[:type]}/launch.yml")
      end


      option :name, :required => false, :type => :string,
             :desc => 'The name of the instance to configure.'
      option :env, :required => false, :aliases => '-e', :enum => OpenShift::Ops::SUPPORTED_ENVS,
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
        ah.ignore_bug_6407

        ah.run_playbook("playbooks/gce/#{host_type}/config.yml")
      end

      option :name, :required => false, :type => :string,
             :desc => 'The name of the instance to terminate.'
      option :env, :required => false, :aliases => '-e', :enum => OpenShift::Ops::SUPPORTED_ENVS,
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
        ah.ignore_bug_6407

        ah.run_playbook("playbooks/gce/#{host_type}/terminate.yml")
      end

      desc "list", "Lists instances."
      def list()
        hosts = GceHelper.list_hosts()

        data = {}
        hosts.each do |key,value|
          value.each { |h| (data[h] ||= []) << key }
        end

        puts
        puts "Instances"
        puts "---------"
        data.keys.sort.each { |k| puts "  #{k}" }
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
        puts host
        if host =~ /^([\w\d_.-]+)@([\w\d-_.]+)/
          user = $1
          host = $2
        end
        puts "user=#{user}"
        puts "host=#{host}"

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

    class CloudCommand < Thor
      desc 'gce', 'Manages Google Compute Engine assets'
      subcommand "gce", GceCommand
    end
  end
end

if __FILE__ == $0
  Dir.chdir(SCRIPT_DIR) do
    # Kick off thor
    OpenShift::Ops::CloudCommand.start(ARGV)
  end
end
