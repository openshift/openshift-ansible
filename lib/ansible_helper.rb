require 'json'
require 'parseconfig'

module OpenShift
  module Ops
    class AnsibleHelper
      MYDIR = File.expand_path(File.dirname(__FILE__))

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
        gce_ini = "#{MYDIR}/../inventory/gce/gce.ini"
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
  end
end
