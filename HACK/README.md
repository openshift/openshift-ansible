This directory contains the inventory and extra vars I have been using
to deploy auto scale group capable clusters on AWS. There are commits
in this tree that need to be submitted as separate PRs but as there
were many moving pieces I have collated them all here for the moment.

My deployment looks like:

    $ git checkout openshift-ansible-3.10.9-1 

	$ ansible-playbook -i provision.ini \
		~/openshift-ansible/playbooks/aws/openshift-cluster/prerequisites.yml \
		-e @vars.yaml 

	$ ansible-playbook -i provision.ini \
		~/openshift-ansible/playbooks/aws/openshift-cluster/provision.yml \
		-e @vars.yaml 

	$ ansible-playbook -i provision.ini \
		~/openshift-ansible/playbooks/aws/openshift-cluster/install.yml \
		-e @vars.yaml 

	$ ansible-playbook -i provision.ini \
		~/openshift-ansible/playbooks/aws/openshift-cluster/provision_nodes.yml \
		-e @vars.yaml 

Once this runs to completion I have a cluster that looks like:

```console
# oc get nodes
NAME                            STATUS    ROLES     AGE       VERSION
ip-172-31-54-212.ec2.internal   Ready     master    1h        v1.10.0+b81c8f8
ip-172-31-55-97.ec2.internal    Ready     infra     1h        v1.10.0+b81c8f8
ip-172-31-59-224.ec2.internal   Ready     compute   1h        v1.10.0+b81c8f8
```

Before autoscaling will work properly you need to attach the
`aos-pod-cluster-autoscaler-minimal` Role to the infra node. Without
this role auto scaling will not work.

Once the cluster is up you'll see that there is the following pod:

```console>
NAME                                  READY     STATUS    RESTARTS   AGE
cluster-autoscaler-5cf8dc5bd7-qsstr   1/1       Running   0          58m
```

You can test that autoscaling is working by running:

    $ oc create -n openshift-autoscaler -f scale-up.yaml
	
The number of replicas required will mean that additional nodes will
be automatically spawned. And vice-versa, when you:

    $ oc delete -n openshift-autoscaler -f scale-up.yaml
	
the new nodes will be destroyed.
