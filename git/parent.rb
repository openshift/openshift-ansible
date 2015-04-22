#!/usr/bin/env ruby
#
#
#

if __FILE__ == $0
  # If we aren't on master we don't need to parent check
  branch = 'prod'
  exit(0) if ARGV[0] !~ /#{branch}/
  commit_id = ARGV[1]
  %x[/usr/bin/git checkout #{branch}]
  %x[/usr/bin/git merge #{commit_id}]

  count = 0
  #lines = %x[/usr/bin/git rev-list --left-right stg...master].split("\n")
  lines = %x[/usr/bin/git rev-list --left-right remotes/origin/stg...#{branch}].split("\n")
  lines.each do |commit|
    # next if they are in stage
    next if commit =~ /^</
    # remove the first char '>'
    commit = commit[1..-1]
    # check if any remote branches contain $commit
    results = %x[/usr/bin/git branch -q -r --contains #{commit} 2>/dev/null ]
    # if this comes back empty, nothing contains it, we can skip it as
    # we have probably created the merge commit here locally
    next if results.empty?

    # The results generally contain origin/pr/246/merge and origin/pr/246/head
    # this is the pull request which would contain the commit in question.
    #
    # If the results do not contain origin/stg then stage does not contain
    # the commit in question.  Therefore we need to alert!
    unless results =~ /origin\/stg/
      puts "\nFAILED: (These commits are not in stage.)\n"
      puts "\t#{commit}"
      count += 1
    end
  end

  # Exit with count of commits in #{branch} but not stg
  exit(count)
end

__END__

