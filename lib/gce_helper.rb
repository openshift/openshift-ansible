require 'ostruct'

module OpenShift
  module Ops
    class GceHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

      def self.get_list()
        cmd = "#{MYDIR}/../inventory/gce/gce.py --list"
        hosts = %x[#{cmd} 2>&1]

        raise "Error: failed to list hosts\n#{hosts}" unless $?.exitstatus == 0
        return JSON.parse(hosts)
      end

      def self.get_gce_tag_val(gce_tags, tag_name)
        tag_prefix = "#{tag_name}-"
        matched_tag = gce_tags.find { |tag| tag =~/\A#{tag_prefix}/ }
        if matched_tag
          return matched_tag.sub(tag_prefix,'')
        end
        return nil
      end

      def self.get_hosts()
        hosts = get_list()

        retval = []
        hosts['_meta']['hostvars'].each do |host, info|
          retval << OpenStruct.new({
            :name        => info['gce_name'] || '-',
            :env         => get_gce_tag_val(info['gce_tags'], 'env') || '-',
            :type        => get_gce_tag_val(info['gce_tags'], 'host-type') || '-',
            :public_ip   => info['gce_public_ip'] || '-',
            :state       => info['gce_status'] || '-',
            :created_by  => get_gce_tag_val(info['gce_tags'], 'created-by') || '-'
          })
        end

        retval.sort_by! { |h| [h.env, h.state, h.name] }

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
