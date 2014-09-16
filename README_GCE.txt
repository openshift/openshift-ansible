
GCE Setup Instructions

Get a gce service key
---------------------
1. ping twiest and ask for a GCE service key


Convert a GCE service key into a pem (for ansible)
--------------------------------------------------
1. The gce service key looks something like this: os302gce-ef83bd90f261.p12
2. the ef83bd90f261 part is the public hash
3. Be in the same directory as the p12 key file.
4. The commands below should be copy / paste-able
5. Run these commands:
   # Temporarily set hash variable
   export GCE_KEY_HASH=ef83bd90f261

   # Convert the service key (note: 'notasecret' is literally what we want here)
   openssl pkcs12 -in os302gce-${GCE_KEY_HASH}.p12 -passin pass:notasecret -nodes -nocerts | openssl rsa -out os302gce-${GCE_KEY_HASH}.pem

   # Move the converted service key to the .ssh dir
   mv os302gce-${GCE_KEY_HASH}.pem ~/.ssh

   # Set a sym link so it's easy to reference
   ln -s ~/.ssh/os302gce-${GCE_KEY_HASH}.pem ~/.ssh/os302gce_priv_key.pem

6. Once this is done, put the original service key file (os302gce-ef83bd90f261.p12) somewhere safe, or delete it (your call, I don't know what else we'll use it for, and we can always regen it if needed)



Install Dependencies (not needed for ctl1)
------------------------------------------
1. Ansible requires libcloud for gce operations:
    yum install -y ansible python-libcloud


Test The Setup
--------------
1. cd li-ops/cloud
2. Try to list all instances:
   ./cloud.rb gce list

3. Try to create an instance:
   ./cloud.rb gce launch -n ${USER}-minion1 -e int --type os3-minion
