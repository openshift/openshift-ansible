#! /bin/sh
set -ex

function importPKCS() {
  dir=${SCRATCH_DIR:-_output}
  NODE_NAME=$1
  ks_pass=${KS_PASS:-kspass}
  ts_pass=${TS_PASS:-tspass}
  rm -rf $NODE_NAME

  keytool \
    -importkeystore \
    -srckeystore $NODE_NAME.pkcs12 \
    -srcstoretype PKCS12 \
    -srcstorepass pass \
    -deststorepass $ks_pass \
    -destkeypass $ks_pass \
    -destkeystore $dir/keystore.jks \
    -alias 1 \
    -destalias $NODE_NAME

  echo "Import back to keystore (including CA chain)"

  keytool  \
    -import \
    -file $dir/ca.crt  \
    -keystore $dir/keystore.jks   \
    -storepass $ks_pass  \
    -noprompt -alias sig-ca

  echo All done for $NODE_NAME
}

function createTruststore() {

  echo "Import CA to truststore for validating client certs"

  keytool  \
    -import \
    -file $dir/ca.crt  \
    -keystore $dir/truststore.jks   \
    -storepass $ts_pass  \
    -noprompt -alias sig-ca
}

dir="/opt/deploy/"
SCRATCH_DIR=$dir

admin_user='system.admin'

if [[ ! -f $dir/system.admin.jks || -z "$(keytool -list -keystore $dir/system.admin.jks -storepass kspass | grep sig-ca)" ]]; then
  importPKCS "system.admin"
  mv $dir/keystore.jks $dir/system.admin.jks
fi

if [[ ! -f $dir/searchguard_node_key || -z "$(keytool -list -keystore $dir/searchguard_node_key -storepass kspass | grep sig-ca)" ]]; then
  importPKCS "elasticsearch"
  mv $dir/keystore.jks $dir/searchguard_node_key
fi


if [[ ! -f $dir/system.admin.jks || -z "$(keytool -list -keystore $dir/system.admin.jks -storepass kspass | grep sig-ca)" ]]; then
  importPKCS "logging-es"
fi

[ ! -f $dir/truststore.jks ] && createTruststore

[ ! -f $dir/searchguard_node_truststore ] && cp $dir/truststore.jks $dir/searchguard_node_truststore

# necessary so that the job knows it completed successfully
exit 0
