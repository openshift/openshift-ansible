require 'fileutils'
require 'parseconfig'

module OpenShift
  module Ops
    class AwsHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

      attr_reader :config, :extra_vars

      def initialize(command=nil, options={})
        @hosts = nil
        @options = options
        set_config()
        set_vars_for_command(command)
      end

      def get_hosts
        set_hosts

        retval = []
        @hosts['_meta']['hostvars'].each do |host, info|
          retval << OpenStruct.new({
            :name        => info['ec2_tag_Name'],
            :env         => info['ec2_tag_environment'] || 'UNSET',
            :public_ip   => info['ec2_ip_address'],
            :public_dns  => info['ec2_public_dns_name'],
            :state       => info['ec2_state'],
            :created_by  => info['ec2_tag_created-by']
          })
        end

        retval.delete_if { |h| h.env != @options[:env] } unless @options[:env].nil?
        retval.sort_by! { |h| [h.env, h.state, h.name] }
        return retval
      end

      def get_host_type(host)
        host_details = get_host_details(host)
        return host_details['host-type']
      end

      def get_host_details(host)
        set_hosts
        dns_names = @hosts["tag_Name_#{host}"]

        raise "Host not found [#{host}]" if dns_names.nil?
        raise "Multiple entries found for [#{host}]" if dns_names.size > 1

        return @hosts['_meta']['hostvars'][dns_names.first]
      end

      def clear_inventory_cache
        path = "#{ENV['HOME']}/.ansible/tmp"
        cache_files = ["#{path}/ansible-ec2.cache", "#{path}/ansible-ec2.index"]
        FileUtils.rm_f(cache_files)
        @config = nil
      end


      private
      def set_hosts
        if @hosts.nil?
          cmd = "#{MYDIR}/../inventory/aws/ec2.py --list"
          inventory = %x[#{cmd} 2>&1]
          raise "Error: failed to list hosts\n#{inventory}" unless $?.exitstatus == 0
          @hosts = JSON.parse(inventory)
        end
      end


      def set_vars_for_command(command)
        ENV['AWS_ACCESS_KEY_ID'] = config['oo_aws_access_key_id']
        ENV['AWS_SECRET_ACCESS_KEY'] = config['oo_aws_secret_access_key']

        vars = { :oo_env => @options[:env] }
        case command
        when :launch
          vars[:oo_new_inst_names] = count.times do
            names << "#{env}-#{type}-#{SecureRandom.hex(5)}"
          end
          vars[:oo_new_inst_tags] = tags.nil? ? {} : tags
          vars[:oo_new_inst_tags][:created_by] = ENV['USER']
          vars[:oo_new_inst_tags].merge!(generate_tag(:env))
          vars[:oo_new_inst_tags].merge!(generate_tag(:host_type))
          vars[:oo_new_inst_tags].merge!(generate_tag(:env_host_type))
        when :config_host
          vars[:oo_host_group_exp] = options[:name]
        when :config_type_env
          vars[:oo_host_group_exp] = "groups['#{tag_name_from_tag(generate_tag(:env_host_type))}']"
        end
        @extra_vars = vars
      end


      def generate_tag(tag_type)
        case tag_type
        when :env
          raise "Missing option :env" unless @options.has_key?(:env)
          { "environment" => env }
        when :host_type
          raise "Missing option :type" unless @options.has_key?(:type)
          { "host-type" => host_type }
        when :env_host_type
          raise "Missing option :env" unless @options.has_key?(:env)
          raise "Missing option :type" unless @options.has_key?(:type)
          { "env-host-type" => "#{env}-#{host_type}"}
        else
          raise "Unknown tag type"
        end
      end


      def tag_name_from_tag(tag)
        return "tag_#{h.keys.first}_#{h.values.first}"
      end


      def set_config
        # Prefer devenv style creds to aws cli config
        config_opts = get_opts_creds_file
        if config_opts.empty?
          config_opts = get_opts_cli_config
        end

        # Environment variables override config file settings
        config_opts.merge!(get_opts_env)

        # Validate config, we must have oo_aws_access_key_id and
        # oo_aws_secret_access_key set
        unless config_opts.has_key?('oo_aws_access_key_id') && config_opts.has_key?('oo_aws_secret_access_key')
          raise 'Could not locate AWS credentials.'
        end
        @config = config_opts
      end


      def get_opts_env
        config_opts = {}

        # if multiple env variables are set for the same config item, the
        # order of preference is:
        # 1. OO_AWS_* variables
        # 2. devenv style environment variables
        # 4. ansible style environment variables
        # 3. AWS CLI style environment variables (if one exists)
        { 'oo_aws_access_key_id' =>
            ['OO_AWS_ACCESS_KEY_ID', 'AWSAccessKeyId', 'AWS_ACCESS_KEY', 'AWS_ACCESS_KEY_ID'],
          'oo_aws_secret_access_key' =>
            ['OO_AWS_SECRET_ACCESS_KEY', 'AWSSecretyKey', 'AWS_SECRET_KEY', 'AWS_SECRET_ACCESS_KEY'],
          'oo_aws_keypair' =>
            ['OO_AWS_KEYPAIR', 'AWSKeyPairName'],
          'oo_aws_private_key_path' =>
            ['OO_AWS_PRIVATE_KEY_PATH', 'AWSPrivateKeyPath'],
          'oo_aws_region' =>
            ['OO_AWS_REGION', 'AWSDefaultRegion', 'AWS_DEFAULT_REGION'],
          'oo_aws_ami' =>
            ['OO_AWS_AMI', 'AWSDefaultAMI'],
          'oo_aws_instance_type' =>
            ['OO_AWS_INSTANCE_TYPE', 'AWSDefaultInstanceType']
        }.each do |opt, env_vars|
          env_vars.each do |v|
            if ENV[v] && ENV[v] != ''
              config_opts[opt] = ENV[v]
              break
            end
          end
        end
        config_opts
      end


      def get_opts_cli_config
        config_opts = {}
        creds_keys = ['aws_access_key_id', 'aws_secret_access_key']
        creds_key_prefix = 'oo_'
        config_keys = ['region']
        config_key_prefix = 'oo_'
        profile = ENV['AWS_DEFAULT_PROFILE'].nil? || ENV['AWS_DEFAULT_PROFILE'] == '' ? 'default' : ENV['AWS_DEFAULT_PROFILE']

        # load values from the cli config file first, honoring the
        # AWS_CONFIG_FILE env variable
        config_file = ENV['AWS_CONFIG_FILE'].nil? || ENV['AWS_CONFIG_FILE'] == '' ? '~/.aws/config' : ENV['AWS_CONFIG_FILE']
        config = config_from_file(config_file)
        config[profile].each do |param, val|
          case param
          when *creds_keys
            config_opts["#{creds_key_prefix}#{param}"] = val
          when *config_keys
            config_opts["#{config_key_prefix}#{param}"] = val
          end
        end

        # Load the credentials from the default cli credentials file,
        # overriding the values set in the config file if set.
        config = config_from_file('~/.aws/credentials')
        config[profile].each do |param, val|
          case param
          when *creds_keys
            config_opts["#{creds_key_prefix}#{param}"] = val
          end
        end
        config_opts
      end

      def get_opts_creds_file
        config_opts = {}

        # Honor the vagrant-openshift AWS_CREDS env variable if present
        config_file = ENV['AWS_CREDS'].nil? || ENV['AWS_CREDS'] == '' ? '~/.awscred' : ENV['AWS_CREDS']
        config = config_from_file(config_file)
        config.params.each do |param, val|
          case param
          when 'AWSAccessKeyId'
            config_opts['oo_aws_access_key_id'] = val
          when 'AWSSecretKey'
            config_opts['oo_aws_secret_access_key'] = val
          when 'AWSKeyPairName',
            config_opts['oo_aws_keypair'] = val
          when 'AWSPrivateKeyPath'
            config_opts['oo_aws_private_key_path'] = val
          when 'AWSDefaultRegion'
            config_opts['oo_aws_region'] = val
          when 'AWSDefaultInstanceType'
            config_opts['oo_aws_instance_type'] = val
          when 'AWSDefaultAMI'
            config_opts['oo_aws_ami'] = val
          end
        end
        config_opts
      end

      def config_from_file(config_file)
        config = ParseConfig.new()
        full_path = File.expand_path(config_file)
        if File.file?(full_path)
          config = ParseConfig.new(full_path)
        end
        config
      end
    end
  end
end
