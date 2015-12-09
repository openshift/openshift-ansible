Yum Repos
=========

This role allows easy deployment of yum repository config files.

Requirements
------------

Yum or dnf

Role Variables
--------------

| Name              | Default value |                                            |
|-------------------|---------------|--------------------------------------------|
| repo_files        | None          |                                            |
| repo_enabled      | 1             | Should repos be enabled by default         |
| repo_gpgcheck     | 1             | Should repo gpgcheck be enabled by default |

Dependencies
------------

Example Playbook
----------------

A single repo file containing a single repo:
  - hosts: servers
    roles:
    - role: yum_repos
      repo_files:
      - id: my_repo
        repos:
        - id: my_repo
          name: My Awesome Repo
          baseurl: https://my.awesome.repo/is/available/here
          skip_if_unavailable: yes
	  gpgkey: https://my.awesome.repo/pubkey.gpg
        
A single repo file containing a single repo, disabling gpgcheck
  - hosts: servers
    roles:
    - role: yum_repos
      repo_files:
      - id: my_other_repo
        repos:
        - id: my_other_repo
          name: My Other Awesome Repo
          baseurl: https://my.other.awesome.repo/is/available/here
          gpgcheck: no

A single repo file containing a single disabled repo
  - hosts: servers
    roles:
    - role: yum_repos
      repo_files:
      - id: my_other_repo
        repos:
        - id: my_other_repo
          name: My Other Awesome Repo
          baseurl: https://my.other.awesome.repo/is/available/here
          enabled: no

A single repo file containing multiple repos
  - hosts: servers
    roles:
    - role: yum_repos
      repo_files:
        id: my_repos
        repos:
        - id: my_repo
          name: My Awesome Repo
          baseurl: https://my.awesome.repo/is/available/here
	  gpgkey: https://my.awesome.repo/pubkey.gpg
        - id: my_other_repo
          name: My Other Awesome Repo
          baseurl: https://my.other.awesome.repo/is/available/here
          gpgkey: https://my.other.awesome.repo/pubkey.gpg

Multiple repo files containing multiple repos
  - hosts: servers
    roles:
    - role: yum_repos
      repo_files:
      - id: my_repos
        repos:
          - id: my_repo
            name: My Awesome Repo
            baseurl: https://my.awesome.repo/is/available/here
	    gpgkey: https://my.awesome.repo/pubkey.gpg
          - id: my_other_repo
            name: My Other Awesome Repo
            baseurl: https://my.other.awesome.repo/is/available/here
	    gpgkey: https://my.other.awesome.repo/pubkey.gpg
      - id: joes_repos
        repos:
          - id: joes_repo
            name: Joe's Less Awesome Repo
            baseurl: https://joes.repo/is/here
	    gpgkey: https://joes.repo/pubkey.gpg
          - id: joes_otherrepo
            name: Joe's Other Less Awesome Repo
            baseurl: https://joes.repo/is/there
	    gpgkey: https://joes.repo/pubkey.gpg
 
License
-------

ASL 2.0

Author Information
------------------

openshift online operations
