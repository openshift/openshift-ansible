oc annotate namespace $1 opflex.cisco.com/endpoint-group='{"policy-space":"'$2'", "name": "kubernetes|kube-system"}' --overwrite=True
