module OpenShift
  module Ops
    class LaunchHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

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
        return Dir.glob("#{MYDIR}/../playbooks/gce/*").map { |d| File.basename(d) }
      end

      def self.get_aws_host_types()
        return Dir.glob("#{MYDIR}/../playbooks/aws/*").map { |d| File.basename(d) }
      end
    end
  end
end
