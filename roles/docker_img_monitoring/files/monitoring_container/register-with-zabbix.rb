#!/usr/bin/env oo-ruby

require 'optparse'
require '/usr/local/lib/zabbix_helper'


if __FILE__ == $0
  $stdout.sync = true
  $stderr.sync = true

  opt_name = nil
  opt_hostgroup = []
  opt_template = []

  optparse = OptionParser.new do |opts|
    opts.banner = "\nUsage: #{File.basename $0}\n\n"

    opts.on('--name NAME',          '[REQUIRED] The host name to register') { |value| opt_name = value }
    opts.on('--hostgroup GROUP',   '[REQUIRED] The hostgroup(s) with which to register') { |value| opt_hostgroup << value }
    opts.on('--template TEMPLATE', '[REQUIRED] The template with which to register') { |value| opt_template << value }
  end

  optparse.parse!

  abort optparse.help if opt_name.nil? || opt_hostgroup.empty? || opt_template.empty?

  puts "Adding host [#{opt_name}] to zabbix..."

  zh = ZabbixHelper.new()
  result = zh.create_agentless_host(opt_name, opt_hostgroup, opt_template)
  if result['hostids'].nil?
    raise "failed to add #{opt_name}"
  else
    puts "Successfully registered host with hostid [#{result['hostids'].first}]"
  end
end
