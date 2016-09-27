# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

# TODO:
# - Add a second disk to the devices
# - Add router dns
# - Test guest -> guest connectivity
# - Test host -> guest connnectivity
# - Test pod -> guest connectivity
# - Test router/registry deployment
# - Test app deployment
# - Test all-in-one env
# - Test single master, single node env
# - Test single master, single etcd, single node env
# - Test single master, single etcd, single node, single infra env
# - Test single master, ha etcd, single node, single infra env
# - Test ha master, ha etcd, single node, single infra env
# - Test using atomic hosts (utility host should be created and use non-atomic box)
# - Test containerized install
# - Test origin/fedora atomic/non-atomic
# - Test rhel atomic/non-atomic
# - Test libvirt on fedora 22
# - Test virtualbox on mac

unless Vagrant.has_plugin?("landrush")
  raise 'landrush is not installed!'
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.landrush.enabled = true
  config.landrush.tld = "example.com"
  deployment_type = ENV['OPENSHIFT_DEPLOYMENT_TYPE'] || 'origin'
  num_masters = (ENV['OPENSHIFT_NUM_MASTERS'] || 1).to_i
  num_etcd = (ENV['OPENSHIFT_NUM_ETCD'] || 0).to_i
  num_nodes = (ENV['OPENSHIFT_NUM_NODES'] || 0).to_i
  num_infra = (ENV['OPENSHIFT_NUM_INFRA'] || 0).to_i
  use_atomic = ENV.has_key?('OPENSHIFT_USE_ATOMIC')
  is_containerized = ENV.has_key?('OPENSHIFT_CONTAINERIZED')
  use_fedora = ENV.has_key?('OPENSHIFT_ORIGIN_USE_FEDORA')

  hosts = {masters: [], etcd: [], nodes: [], infra: [], lb: [], nfs: []}
  num_masters.times do |n|
    hosts[:masters] << "master#{n+1}"
  end
  num_etcd.times do |n|
    hosts[:etcd] << "etcd#{n+1}"
  end
  num_nodes.times do |n|
    hosts[:nodes] << "node#{n+1}"
  end
  num_infra.times do |n|
    hosts[:infra] << "infra#{n+1}"
  end

  if use_atomic or is_containerized
    hosts[:nfs] << 'utility'
    hosts[:lb] << 'utility'
  else
    hosts[:nfs] << hosts[:masters][0]
    hosts[:lb] << hosts[:masters][0]
  end
  host_names = hosts.values.flatten.uniq

  config.ssh.insert_key = false

  non_atomic_box = ''

  case deployment_type
  when 'openshift-enterprise', 'atomic-enterprise'
    if use_atomic
      box_type = 'rhel-7-atomic'
      non_atomic_box = 'rhel-7'
    else
      box_type = 'rhel-7'
    end
  when 'origin'
    if use_atomic
      if use_fedora
        box_type = 'fedora/23-atomic-host'
        non_atomic_box = 'fedora/23-cloud-base'
      else
        box_type = 'centos/atomic-host'
        non_atomic_box = 'centos/7'
      end
    else
      if use_fedora
        box_type = 'fedora/23-cloud-base'
      else
        box_type = 'centos/7'
      end
    end
  end

  config.vm.box_check_update
  config.vm.box = box_type
  config.vm.synced_folder '.', '/home/vagrant/sync', disabled: true

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
      if use_atomic and machine == 'utility'
        machine.vm.box = non_atomic_box
      end

      machine.vm.hostname = "openshift-#{hostname}.example.com"
      machine.vm.network :private_network, ip: "192.168.100.#{100 + i}"

      if (num_masters == 1 and machine == 'master1') or (num_masters > 1 and machine == 'utility')
        machine.landrush.host 'openshift.example.com', "192.168.100.#{100 +i}"
#        machine.vm.network :forwarded_port, guest: 8443, host: 8443
      end

      if i == host_names.length - 1
        machine.vm.provision :ansible do |ansible|
          ansible.limit = 'all'
          ansible.sudo = true
          ansible.groups = {
            'OSEv3'            => host_names,
            'masters'          => hosts[:masters],
            'etcd'             => hosts[:etcd].length > 0 ? hosts[:etcd] : hosts[:masters],
            'etcd:vars'        => {'etcd_interface' => 'eth1'},
            'nodes'            => hosts[:masters] + hosts[:nodes] + hosts[:infra],
            'nfs'              => hosts[:nfs],
            'lb'               => hosts[:lb],
            'infra_nodes'      => hosts[:infra],
            'infra_nodes:vars' => {'openshift_node_labels' => "{'region': 'infra'}"},
            'app_nodes'        => hosts[:nodes],
            'app_nodes:vars'   => {'openshift_node_labels' => "{'region': 'app'}"},
          }

          master_vars = {}
          if num_nodes == 0
            master_vars['openshift_schedulable'] = true
          end

          if num_infra == 0
            master_vars['openshift_node_labels'] = "{'region': 'infra'}"
          end

          ansible.groups['masters:vars'] = master_vars

          ansible.host_vars = {}

          ansible.extra_vars = {
            deployment_type: deployment_type,
            openshift_override_hostname_check: true,
          }
          if num_masters > 1
            ansible.extra_vars['openshift_master_cluster_method'] = 'native'
            ansible.extra_vars['openshift_master_cluster_hostname'] = 'openshift.example.com'
            ansible.extra_vars['openshift_master_cluster_public_hostname'] = 'openshift.example.com'
          end
          if is_containerized
            ansible.extra_vars['containerized'] = true
            ansible.host_vars['utility'] = {'containerized' => false}
          end

          ansible.playbook = 'playbooks/byo/vagrant.yml'
        end
      end
    end
  end
end
