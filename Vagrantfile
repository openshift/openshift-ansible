# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

unless Vagrant.has_plugin?("landrush")
  raise 'landrush is not installed!'
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.landrush.enabled = true
  config.landrush.tld = "example.com"
  deployment_type = ENV['OPENSHIFT_DEPLOYMENT_TYPE'] || 'origin'
  num_masters = (ENV['OPENSHIFT_NUM_MASTERS'] || 1).to_i
  num_etcd = (ENV['OPENSHIFT_NUM_ETCD'] || 0).to_i
  num_nodes = (ENV['OPENSHIFT_NUM_NODES'] || 1).to_i
  num_infra = (ENV['OPENSHIFT_NUM_INFRA'] || 1).to_i
  use_atomic = ENV.has_key?('OPENSHIFT_USE_ATOMIC')
  containerized = use_atomic or ENV.has_key?('OPENSHIFT_CONTAINERIZED')
  use_fedora = ENV.has_key?('OPENSHIFT_ORIGIN_USE_FEDORA')

  hosts = {masters: [], etcd: [], nodes: [], infra: [], lb: [], nfs: ['utility']}
  num_masters.times do |n|
    hosts[:masters] << "master#{n+1}"
  num_etcd.times do |n|
    hosts[:etcd] << "etcd#{n+1}"
  num_nodes.times do |n|
    hosts[:nodes] << "node#{n+1}"
  num_infra.times do |n|
    hosts[:infra] << "infra#{n+1}"
  if num_masters > 1:
    hosts[:lb] << ['utility']
  host_names = hosts.values.flatten.uniq

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.include_offline = true
  config.ssh.insert_key = false

  non_atomic_box = ''

  case deployment_type
  when 'openshift-enterprise', 'atomic-enterprise'
    if use_atomic
      vm.box = 'rhel-7-atomic'
      non_atomic_box = 'rhel-7'
    else:
      vm.box = 'rhel-7'
  when 'origin'
    if use_atomic
      if use_fedora
        vm.box = 'fedora/23-atomic-host'
        non_atomic_box = 'fedora/23-cloud-base'
      else
        vm.box = 'centos/atomic-host'
        non_atomic_box = 'centos/7'
      end
    else
      if use_fedora
        vm.box = 'fedora/23-cloud-base'
      else
        vm.box = 'centos/7'
      end
    end
  end

  config.vm.box_check_update

  config.vm.provider 'virtualbox' do |vbox, override|
    vbox.memory = 1024
    vbox.cpus = 1
    vbox.linked_clone = true

    # Enable multiple guest CPUs if available
    vbox.customize ['modifyvm', :id, '--ioapic', 'on']
  end

  config.vm.provider 'libvirt' do |libvirt, override|
    libvirt.cpus = 1
    libvirt.memory = 1024
    libvirt.driver = 'kvm'
  end

  host_names.each_with_index do |hostname, i|
    config.vm.define hostname do |machine|
      machine.vm.hostname = "openshift-#{host}.example.com"
      machine.vm.network :private_network, ip: "192.168.100.#{100 + i}"
      if (num_masters == 1 and machine == 'master1') or (num_masters > 1 and machine == 'utility'
        machine.vm.network :forwarded_port, guest: 8443, host: 8443

      if i == host_names.length
        machine.vm.provision :ansible do |ansible|
          ansible.limit = 'all'
          ansible.sudo = true
          ansible.groups = {
            'masters' => hosts[:masters]
            'etcd'    => hosts[:etcd].length > 0 ? hosts[:etcd] : hosts[:masters]
            'nodes'   => hosts[:masters] + hosts[:nodes] + hosts[:infra]
            'nfs'     => hosts[:nfs]
            'lb'      => hosts[:lb]
          }
          ansible.extra_vars = {
            deployment_type: deployment_type,
          }
          if num_masters > 1:
          ansible.playbook = 'playbooks/byo/vagrant.yml'
      end
    end
  end
end
