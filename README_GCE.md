
GCE Setup Instructions
======================

Get a gce service key
---------------------
1. Ask your GCE project administrator for a GCE service key

Note: If your GCE project does not show a Service Account under <Project>/APIs & auth/Credentials, you will need to use "Create new Client ID" to create a Service Account before your administrator can create the service key for you.


Convert a GCE service key into a pem (for ansible)
--------------------------------------------------
1. mkdir -p ~/.gce
1. The gce service key looks something like this: projectname-ef83bd90f261.p12
.. The ef83bd90f261 part is the public hash (GCE_KEY_HASH), The projectname part, is the project name (PROJECT_NAME).
1. Be in the same directory as the p12 key file.
1. The commands below should be copy / paste-able
1. Run these commands:
```
   # Temporarily set hash variable and project name
   export GCE_KEY_HASH=ef83bd90f261
   export PROJECT_NAME=Project Name
   export PROJECT_ID=Project ID

   # Convert the service key (note: 'notasecret' is literally what we want here)
   openssl pkcs12 -in "${PROJECT_NAME}-${GCE_KEY_HASH}.p12" -passin pass:notasecret -nodes -nocerts | openssl rsa -out ${PROJECT_ID}-${GCE_KEY_HASH}.pem

   # Move the converted service key to the .gce dir
   mv ${PROJECT_ID}-${GCE_KEY_HASH}.pem ~/.gce
```

1. Once this is done, put the original service key file (projectname-ef83bd90f261.p12) somewhere safe, or delete it (your call, I don not know what else we will use it for, and we can always regen it if needed).


Create a gce.ini file for GCE
--------------------------------
* gce_service_account_email_address - Found in "APIs & auth" -> Credentials -> "Service Account" -> "Email Address"
* gce_service_account_pem_file_path - Full path from previous steps
* gce_project_id - Found in "Projects", it list all the gce projects you are associated with.  The page lists their "Project Name" and "Project ID".  You want the "Project ID"

Mandatory customization variables (check the values according to your tenant):
* zone = europe-west1-d
* network = default
* gce_machine_type = n1-standard-2
* gce_machine_master_type = n1-standard-1
* gce_machine_node_type = n1-standard-2
* gce_machine_image = preinstalled-slave-50g-v5
* gce_machine_master_image = preinstalled-slave-50g-v5
* gce_machine_node_image = preinstalled-slave-50g-v5


1. vi ~/.gce/gce.ini
1. make the contents look like this:
```
[gce]
gce_service_account_email_address = long...@developer.gserviceaccount.com
gce_service_account_pem_file_path = /full/path/to/project_id-gce_key_hash.pem
gce_project_id = project_id
zone = europe-west1-d
network = default
gce_machine_type = n1-standard-2
gce_machine_master_type = n1-standard-1
gce_machine_node_type = n1-standard-2
gce_machine_image = preinstalled-slave-50g-v5
gce_machine_master_image = preinstalled-slave-50g-v5
gce_machine_node_image = preinstalled-slave-50g-v5

```
1. Define the environment variable GCE_INI_PATH so gce.py can pick it up and bin/cluster can also read it
```
export GCE_INI_PATH=~/.gce/gce.ini
```


Install Dependencies
--------------------
1. Ansible requires libcloud for gce operations:
```
  yum install -y ansible python-libcloud
```


Test The Setup
--------------
1. cd openshift-ansible/
1. Try to list all instances (Passing an empty string as the cluster_id
argument will result in all gce instances being listed)
```
  bin/cluster list gce ''
```

Creating a cluster
------------------
1. To create a cluster with one master and two nodes
```
  bin/cluster create gce <cluster-id>
```

Updating a cluster
---------------------
1. To update the cluster
```
  bin/cluster update gce <cluster-id>
```

Terminating a cluster
---------------------
1. To terminate the cluster
```
  bin/cluster terminate gce <cluster-id>
```
