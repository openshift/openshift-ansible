# -*- mode: ruby -*-
# vi: set ft=ruby :

# Ansible provisioner for multimachine
ANSIBLE_RAW_SSH_ARGS = []
boxes = [
    {
        :name => "keepalived1",
        :eth1 => "192.168.33.10",
        :image => "ubuntu/trusty64",
    },
    {
        :name => "keepalived2",
        :eth1 => "192.168.33.11",
        :image => "ubuntu/xenial64",
    },
    {
        :name => "keepalived3",
        :eth1 => "192.168.33.12",
        :image => "centos/7",
    }
]

# Gather all the keys for the ssh connections
boxes.each do |boxopts|
  ANSIBLE_RAW_SSH_ARGS << "-o IdentityFile=.vagrant/machines/#{boxopts[:name]}/virtualbox/private_key"
end

Vagrant.configure(2) do |config|

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--memory", 256]
    v.customize ["modifyvm", :id, "--cpus", 1]
  end

  # Optional vagrant cache
  #if Vagrant.has_plugin?("vagrant-cachier")
  #  # http://fgrehm.viewdocs.io/vagrant-cachier/usage/
  #  config.cache.scope = :box
  #  #config.cache.synced_folder_opts = {
  #  #  type: :nfs,
  #  #  mount_options: ['rw', 'vers=3', 'tcp', 'nolock']
  #  #}
  #end

  boxes.each do |boxopts|
    config.vm.define boxopts[:name] do |config|
      config.vm.box = boxopts[:image]
      config.vm.hostname = boxopts[:name]
      config.vm.network :private_network, ip: boxopts[:eth1]
      # Vagrant works serially and provision machines
      # serially. Each of them is unaware of the others.
      # Therefore, we should start provisioning only on last machine
      if boxopts[:name] == "keepalived3"
        config.vm.provision :ansible do |ansible|
          ansible.playbook = "tests/deploy.yml"
          ansible.extra_vars = "tests/keepalived_haproxy_combined_example.yml"
          ansible.limit = 'all'
          #ansible.inventory_path = "tests/inventory"
          ansible.verbose = "-v"
          ansible.raw_ssh_args = ANSIBLE_RAW_SSH_ARGS
        end
      end
    end
  end
end
