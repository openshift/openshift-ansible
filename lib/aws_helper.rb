require 'fileutils'

module OpenShift
  module Ops
    class AwsHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

      def self.get_list()
        cmd = "#{MYDIR}/../inventory/aws/ec2.py --list"
        hosts = %x[#{cmd} 2>&1]

        raise "Error: failed to list hosts\n#{hosts}" unless $?.exitstatus == 0
        return JSON.parse(hosts)
      end

      def self.get_hosts()
        hosts = get_list()

        retval = []
        hosts['_meta']['hostvars'].each do |host, info|
          retval << OpenStruct.new({
            :name        => info['ec2_tag_Name'],
            :env         => info['ec2_tag_environment'] || 'UNSET',
            :public_ip   => info['ec2_ip_address'],
            :public_dns  => info['ec2_public_dns_name'],
            :state       => info['ec2_state'],
            :created_by  => info['ec2_tag_created-by']
          })
        end

        retval.sort_by! { |h| [h.env, h.state, h.name] }

        return retval
      end

      def self.get_host_details(host)
        hosts = get_list()
        dns_names = hosts["tag_Name_#{host}"]

        raise "Host not found [#{host}]" if dns_names.nil?
        raise "Multiple entries found for [#{host}]" if dns_names.size > 1

        return hosts['_meta']['hostvars'][dns_names.first]
      end

      def self.check_creds()
        raise "AWS_ACCESS_KEY_ID environment variable must be set" if ENV['AWS_ACCESS_KEY_ID'].nil?
        raise "AWS_SECRET_ACCESS_KEY environment variable must be set" if ENV['AWS_SECRET_ACCESS_KEY'].nil?
      end

      def self.clear_inventory_cache()
        path = "#{ENV['HOME']}/.ansible/tmp"
        cache_files = ["#{path}/ansible-ec2.cache", "#{path}/ansible-ec2.index"]
        FileUtils.rm(cache_files)
      end

      def self.generate_env_tag(env)
        return { "environment" => env }
      end

      def self.generate_env_tag_name(env)
        h = generate_env_tag(env)
        return "tag_#{h.keys.first}_#{h.values.first}"
      end

      def self.generate_host_type_tag(host_type)
        return { "host-type" => host_type }
      end

      def self.generate_host_type_tag_name(host_type)
        h = generate_host_type_tag(host_type)
        return "tag_#{h.keys.first}_#{h.values.first}"
      end

      def self.generate_env_host_type_tag(env, host_type)
        return { "env-host-type" => "#{env}-#{host_type}" }
      end

      def self.generate_env_host_type_tag_name(env, host_type)
        h = generate_env_host_type_tag(env, host_type)
        return "tag_#{h.keys.first}_#{h.values.first}"
      end
    end
  end
end
