#!/usr/bin/env ruby

require 'fileutils'

module OpenShift
  module Ops
    class Notify
      def self.puts(msg)
        $stdout.puts "#{Time.now}: #{msg}"
      end
    end

    class WatchForIpcs
      IPC_DIR = '/var/run/ctr-ipc'
      POLL_INTERVAL = 10 # second
      HAPROXY_CONF = '/etc/haproxy/haproxy.cfg'
      HAPROXY_PID_FILE = '/var/run/haproxy.pid'

      def self.wait_for_service()
        loop do
          Dir.glob("#{IPC_DIR}/service/*").each do |svc_file|
            svc = File.basename(svc_file)
            action = File.read(svc_file)
            Notify.puts "Found IPC service file: #{svc}"
            Notify.puts "      Action requested: #{action}"

            # Make sure we don't handle this multiple times
            FileUtils.rm(svc_file)

            handle_service_ipc(svc, action)
          end

          sleep POLL_INTERVAL
        end
      end

      def self.handle_service_ipc(svc, action)
        cmd = nil
        case svc
        when 'httpd'
          case action
          when 'restart', 'reload'
            cmd = "/usr/sbin/apachectl -k graceful"
          end
        when 'haproxy'
          case action
          when 'restart'
            cmd = "/usr/sbin/haproxy -f #{HAPROXY_CONF} -p #{HAPROXY_PID_FILE} -sf $(/bin/cat #{HAPROXY_PID_FILE})"
          end
        end

  if cmd.nil?
          Notify.puts "  Warning: Not handling #{svc} #{action}"
          return
        end

        Notify.puts "  Running: #{cmd}"
        output = %x[#{cmd} 2>&1]
        Notify.puts "  Output: #{output}"
      end
    end
  end
end

if __FILE__ == $0
  OpenShift::Ops::WatchForIpcs.wait_for_service()
end
