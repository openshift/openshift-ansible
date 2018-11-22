* Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` env vars
* Copy `test/aws/vars.yml.sample` to `test/aws/inventory/group_vars/all/vars.yml`
* Adjust it your liking - this would be the host configuration
* Cleanup ec2 cache - `rm -rf ~/.ansible/tmp`
* Provision instances via `ansible-playbook -vv -i test/aws/inventory/ test/aws/launch.yml`
  This would create EC2 instances if necessary and setup cluster there.
  Rerun the playbook to continue setup on existing nodes (identified by `kubernetes.io/cluster/{{ aws_cluster_id }}: true` tag)
* Once the setup is complete run `ansible-playbook -vv -i test/aws/inventory/ test/aws/deprovision.yml`
