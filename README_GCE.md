
GCE Setup Instructions
======================

Get a gce service key
---------------------
1. ask your GCE project administrator for a GCE service key

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

1. vi ~/.gce/gce.ini
1. make the contents look like this:
```
[gce]
gce_service_account_email_address = long...@developer.gserviceaccount.com
gce_service_account_pem_file_path = /full/path/to/project_id-gce_key_hash.pem
gce_project_id = project_id
```
1. Setup a sym link so that gce.py will pick it up (link must be in same dir as gce.py)
```
  cd openshift-ansible/inventory/gce
  ln -s ~/.gce/gce.ini gce.ini
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
2. Try to list all instances:
```
  ./cloud.rb gce list
```

3. Try to create an instance:
```
  ./cloud.rb gce launch -n ${USER}-node1 -e int --type os3-node
```
