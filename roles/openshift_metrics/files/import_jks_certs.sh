#!/bin/bash
#
# Copyright 2014-2015 Red Hat, Inc. and/or its affiliates
# and other contributors as indicated by the @author tags.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -ex

function import_certs() {
  dir=$CERT_DIR
  hawkular_metrics_keystore_password=$(echo $METRICS_KEYSTORE_PASSWD | base64 -d)
  hawkular_cassandra_keystore_password=$(echo $CASSANDRA_KEYSTORE_PASSWD | base64 -d)
  hawkular_metrics_truststore_password=$(echo $METRICS_TRUSTSTORE_PASSWD | base64 -d)
  hawkular_cassandra_truststore_password=$(echo $CASSANDRA_TRUSTSTORE_PASSWD | base64 -d)
  hawkular_jgroups_password=$(echo $JGROUPS_PASSWD | base64 -d)
  
  cassandra_alias=`keytool -noprompt -list -keystore $dir/hawkular-cassandra.truststore -storepass ${hawkular_cassandra_truststore_password} | sed -n '7~2s/,.*$//p'`
  hawkular_alias=`keytool -noprompt -list -keystore $dir/hawkular-metrics.truststore -storepass ${hawkular_metrics_truststore_password} | sed -n '7~2s/,.*$//p'`
  
  if [ ! -f $dir/hawkular-metrics.keystore ]; then
    echo "Creating the Hawkular Metrics keystore from the PEM file"
    keytool -importkeystore -v \
      -srckeystore $dir/hawkular-metrics.pkcs12 \
      -destkeystore $dir/hawkular-metrics.keystore \
      -srcstoretype PKCS12 \
      -deststoretype JKS \
      -srcstorepass $hawkular_metrics_keystore_password \
      -deststorepass $hawkular_metrics_keystore_password
  fi

  if [ ! -f $dir/hawkular-cassandra.keystore ]; then
    echo "Creating the Hawkular Cassandra keystore from the PEM file"
    keytool -importkeystore -v \
      -srckeystore $dir/hawkular-cassandra.pkcs12 \
      -destkeystore $dir/hawkular-cassandra.keystore \
      -srcstoretype PKCS12 \
      -deststoretype JKS \
      -srcstorepass $hawkular_cassandra_keystore_password \
      -deststorepass $hawkular_cassandra_keystore_password
  fi
  
  if [[ ! ${cassandra_alias[*]} =~ hawkular-metrics ]]; then
    echo "Importing the Hawkular Certificate into the Cassandra Truststore"
    keytool -noprompt -import -v -trustcacerts -alias hawkular-metrics \
      -file $dir/hawkular-metrics.crt \
      -keystore $dir/hawkular-cassandra.truststore \
      -trustcacerts \
      -storepass $hawkular_cassandra_truststore_password
  fi
  
  if [[ ! ${hawkular_alias[*]} =~ hawkular-cassandra ]]; then
    echo "Importing the Cassandra Certificate into the Hawkular Truststore"
    keytool -noprompt -import -v -trustcacerts -alias hawkular-cassandra \
      -file $dir/hawkular-cassandra.crt \
      -keystore $dir/hawkular-metrics.truststore \
      -trustcacerts \
      -storepass $hawkular_metrics_truststore_password
  fi

  if [[ ! ${cassandra_alias[*]} =~ hawkular-cassandra ]]; then
    echo "Importing the Hawkular Cassandra Certificate into the Cassandra Truststore"
    keytool -noprompt -import -v -trustcacerts -alias hawkular-cassandra \
      -file $dir/hawkular-cassandra.crt \
      -keystore $dir/hawkular-cassandra.truststore \
      -trustcacerts \
      -storepass $hawkular_cassandra_truststore_password
  fi

  cert_alias_names=(ca metricca cassandraca)

  for cert_alias in ${cert_alias_names[*]}; do
    if [[ ! ${cassandra_alias[*]} =~ "$cert_alias" ]]; then
      echo "Importing the CA Certificate with alias $cert_alias into the Cassandra Truststore"
      keytool -noprompt -import -v -trustcacerts -alias $cert_alias \
        -file ${dir}/ca.crt \
        -keystore $dir/hawkular-cassandra.truststore \
        -trustcacerts \
        -storepass $hawkular_cassandra_truststore_password
    fi
  done

  for cert_alias in ${cert_alias_names[*]}; do
    if [[ ! ${hawkular_alias[*]} =~ "$cert_alias" ]]; then
      echo "Importing the CA Certificate with alias $cert_alias into the Hawkular Metrics Truststore"
      keytool -noprompt -import -v -trustcacerts -alias $cert_alias \
        -file ${dir}/ca.crt \
        -keystore $dir/hawkular-metrics.truststore \
        -trustcacerts \
        -storepass $hawkular_metrics_truststore_password
    fi
  done

  if [ ! -f $dir/hawkular-jgroups.keystore ]; then
    echo "Generating the jgroups keystore"
    keytool -genseckey -alias hawkular -keypass ${hawkular_jgroups_password} \
      -storepass ${hawkular_jgroups_password} \
      -keyalg Blowfish \
      -keysize 56 \
      -keystore $dir/hawkular-jgroups.keystore \
      -storetype JCEKS
  fi
}

import_certs

exit 0
