# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

unless Vagrant.has_plugin?("vagrant-hostmanager")
  raise 'vagrant-hostmanager plugin is required'
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  deployment_type = ENV['OPENSHIFT_DEPLOYMENT_TYPE'] || 'origin'
  num_nodes = (ENV['OPENSHIFT_NUM_NODES'] || 2).to_i

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.include_offline = true
  config.ssh.insert_key = false

  if deployment_type === 'enterprise'
    unless Vagrant.has_plugin?('vagrant-registration')
      raise 'vagrant-registration-plugin is required for enterprise deployment'
    end
    username = ENV['rhel_subscription_user']
    password = ENV['rhel_subscription_pass']
    unless username and password
      raise 'rhel_subscription_user and rhel_subscription_pass are required'
    end
    config.registration.username = username
    config.registration.password = password
    # FIXME this is temporary until vagrant/ansible registration modules
    # are capable of handling specific subscription pools
    if not ENV['rhel_subscription_pool'].nil?
      config.vm.provision "shell" do |s|
        s.inline = "subscription-manager attach --pool=$1 || true"
        s.args = "#{ENV['rhel_subscription_pool']}"
      end
    end
  end

  config.vm.provider "virtualbox" do |vbox, override|
    override.vm.box = "centos/7"
    vbox.memory = 1024
    vbox.cpus = 2

    # Enable multiple guest CPUs if available
    vbox.customize ["modifyvm", :id, "--ioapic", "on"]
  end

  config.vm.provider "libvirt" do |libvirt, override|
    libvirt.cpus = 2
    libvirt.memory = 1024
    libvirt.driver = 'kvm'
    case deployment_type
    when "enterprise"
      override.vm.box = "rhel-7"
    when "origin"
      override.vm.box = "centos/7"
      override.vm.box_download_checksum = "b2a9f7421e04e73a5acad6fbaf4e9aba78b5aeabf4230eebacc9942e577c1e05"
      override.vm.box_download_checksum_type = "sha256"
    end
  end

  num_nodes.times do |n|
    node_index = n+1
    config.vm.define "node#{node_index}" do |node|
      node.vm.hostname = "ose3-node#{node_index}.example.com"
      node.vm.network :private_network, ip: "192.168.100.#{200 + n}"
      config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service"
    end
  end

  config.vm.define "master" do |master|
    master.vm.hostname = "ose3-master.example.com"
    master.vm.network :private_network, ip: "192.168.100.100"
    master.vm.network :forwarded_port, guest: 8443, host: 8443
    config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service"
    master.vm.provision "ansible" do |ansible|
      ansible.limit = 'all'
      ansible.sudo = true
      ansible.groups = {
        "masters" => ["master"],
        "nodes"   => ["master", "node1", "node2"],
      }
      ansible.extra_vars = {
        deployment_type: deployment_type,
      }
      ansible.playbook = "playbooks/byo/vagrant.yml"
    end
  end
end
