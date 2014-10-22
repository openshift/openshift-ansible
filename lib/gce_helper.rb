require 'ostruct'

module OpenShift
  module Ops
    class GceHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

      def self.get_hosts()
        cmd = "#{MYDIR}/../inventory/gce/gce.py --list"
        hosts = %x[#{cmd} 2>&1]

        raise "Error: failed to list hosts\n#{hosts}" unless $?.exitstatus == 0

        # invert the hash so that it's key is the host, and values is an array of metadata
        data = {}
        JSON.parse(hosts).each do |key,value|
          value.each { |h| (data[h] ||= []) << key }
        end

        # For now, we only care about the name. In the future, we may want the other metadata included.
        retval = []
        data.keys.sort.each { |k| retval << OpenStruct.new({ :name => k }) }

        return retval
      end

      def self.get_host_details(host)
        cmd = "#{MYDIR}/../inventory/gce/gce.py --host #{host}"
        details = %x[#{cmd} 2>&1]

        raise "Error: failed to get host details\n#{details}" unless $?.exitstatus == 0

        retval = JSON.parse(details)

        raise "Error: host not found [#{host}]" if retval.empty?

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
  end
end
