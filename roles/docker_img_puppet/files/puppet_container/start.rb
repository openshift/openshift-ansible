#!/usr/bin/env ruby

require 'fileutils'

CTR_CONFIG_FLAG = '/shared/var/run/ctr-ipc/flag/ctr_configured'


class Start
  def self.setup_shared_dirs()
    puts '_'
    puts 'Setting up dirs in shared volume'
    puts '--------------------------------'
    mtab = File.read('/etc/mtab')

    shared_dirs = mtab.grep(/ \/shared\//).collect { |line| line.split(' ')[1] }

    shared_dirs.each do |sh_dir|
      orig_dir = sh_dir.gsub(/^\/shared/,'')

      next if File.symlink?(orig_dir)

      if File.exist?(orig_dir)
        cmd = "cp -vaf #{orig_dir} #{File.dirname(sh_dir)}"
        puts "Running: #{cmd}"
        system(cmd)

        cmd = "rm -vrf #{orig_dir}"
        puts "Running: #{cmd}"
        system(cmd)
      end

      FileUtils.ln_s(sh_dir, orig_dir, {:verbose => true})
    end
    puts 'Done.'
    puts '_'
  end

  def self.run_puppet_agent()
    puts '_'
    puts 'Running Puppet Agent'
    puts '--------------------'
    exitcode = nil
    1.upto(3) do |ctr|
       unless ctr == 1
         puts '_'
         puts "Previous puppet run failed with exit code [#{exitcode}], running again..."
         puts '_'
       end

       system("bash -c 'time /usr/bin/puppet agent -t'")
       exitcode = $?.exitstatus
       puts "Exit Code [#{exitcode}]"

       break if exitcode == 0 || exitcode == 2
    end

    raise "Puppet run failed, retries exhausted." if exitcode != 0 && exitcode != 2

    puts 'Done.'
    puts '_'

    puts '_'
    puts 'Creating ctr_configured flag'
    FileUtils.mkdir_p(File.dirname(CTR_CONFIG_FLAG))
    FileUtils.touch(CTR_CONFIG_FLAG)
    puts 'Done.'
    puts '_'
  end

  def self.exec_puppetd()
    puts '_'
    puts 'Exec-ing puppet daemon'
    puts '---------------------'
    puts "Starting puppet agent..."
    exec("bash -c '/usr/bin/puppet agent --no-daemonize --detailed-exitcodes --verbose'")
  end
end

if __FILE__ == $0
  $stdout.sync = true
  $stderr.sync = true

  Start.setup_shared_dirs()
  Start.run_puppet_agent()
  Start.exec_puppetd()
end
