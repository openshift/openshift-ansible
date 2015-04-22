#!/usr/bin/env ruby
#
#
#
require 'yaml'
require 'tmpdir'

class YamlValidate
  def self.yaml_file?(filename)
    return filename.end_with?('.yaml') || filename.end_with?('.yml')
  end

  def self.short_yaml_ext?(filename)
    return filename.end_with?(".yml")
  end

  def self.valid_yaml?(filename)
    YAML::load_file(filename)

    return true
  end
end

class GitCommit
  attr_accessor :oldrev, :newrev, :refname, :tmp
  def initialize(oldrev, newrev, refname)
    @oldrev = oldrev
    @newrev = newrev
    @refname = refname
    @tmp = Dir.mktmpdir(@newrev)
  end

  def get_file_changes()
    files = %x[/usr/bin/git diff --name-only #{@oldrev} #{@newrev} --diff-filter=ACM].split("\n")

    # if files is empty we will get a full checkout.  This happens on
    # a git rm file.  If there are no changes then we need to skip the archive
    return [] if files.empty?

    # We only want to take the files that changed.  Archive will do that when passed
    # the filenames.  It will export these to a tmp dir
    system("/usr/bin/git archive #{@newrev} #{files.join(" ")} | tar x -C #{@tmp}")
    return Dir.glob("#{@tmp}/**/*").delete_if { |file| File.directory?(file) }
  end
end

if __FILE__ == $0
  while data = STDIN.gets
    oldrev, newrev, refname = data.split
    gc = GitCommit.new(oldrev, newrev, refname)

    results = []
    gc.get_file_changes().each do |file|
      begin
        puts "++++++ Received:  #{file}"

        #raise "Yaml file extensions must be .yaml not .yml" if YamlValidate.short_yaml_ext? file

        # skip readme, other files, etc
        next unless YamlValidate.yaml_file?(file)

        results << YamlValidate.valid_yaml?(file)
      rescue Exception => ex
        puts "\n#{ex.message}\n\n"
        results << false
      end
    end

    #puts "RESULTS\n#{results.inspect}\n"
    exit 1 if results.include?(false)
  end
end
