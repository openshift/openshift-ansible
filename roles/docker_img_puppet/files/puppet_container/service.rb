#!/usr/bin/env ruby

require 'fileutils'

if __FILE__ == $0
  abort "\nUsage: #{File.basename($0)} <name> <action>\n\n" unless ARGV.size == 2

  name = ARGV[0]
  action = ARGV[1]

  SERVICE_IPC_DIR = '/var/run/ctr-ipc/service'

  FileUtils.mkdir_p(SERVICE_IPC_DIR)

  File.open("#{SERVICE_IPC_DIR}/#{name}", 'w') do |f|
    f.print action
  end
end
