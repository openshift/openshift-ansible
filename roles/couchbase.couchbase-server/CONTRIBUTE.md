## Contribution

Issues and pull requests are welcome for this project. Please read and
abide by the [Couchbase Code of Conduct](http://www.couchbase.com/code-of-conduct).

The preferred repository for issues and pull requests is:

https://github.com/couchbaselabs/ansible-couchbase-server

This role was specifically created for use with the  
[Ansible Galaxy](https://galaxy.ansible.com/) project, but it also functions
as a standalone project.

Check out the [Ansible](http://www.ansible.com) and 
[Ansible Galaxy](https://galaxy.ansible.com/) websites to learn more and
get `ansible`.

Once you're ready to go, you can install this role with:

```
ansible-galaxy install brianshumate.couchbase-server
```

There is more information available on using Ansible roles in the 
[roles documentation](http://docs.ansible.com/playbooks_roles.html#roles).


### Local Role Customization

You can also customize this role with your own changes by naming your local
repository clone or fork the same as Ansible Galaxy:

For example, this repository is named `ansible-couchbase-server` and the
Ansible Galaxy project name is `brianshumate.couchbase-server`.

First, you need to specify a directory where you'd like to store custom
roles, and then add that to `~/.ansible.cfg`:


```
[defaults]
roles_path = /home/ansible/roles
```

Now simply change into that role directory and clone the repository:

```
cd /home/ansible/roles
git clone https://github.com/brianshumate/ansible-couchbase-server.git brianshumate.couchbase-server
```

Now you can make all the changes you like, and execute the `ansible-galaxy`
commands as though you were working against the remote project, but you'll
instead be using your custom version.
