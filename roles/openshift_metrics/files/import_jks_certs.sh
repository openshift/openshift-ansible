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
  hawkular_metrics_truststore_password=$(echo $METRICS_TRUSTSTORE_PASSWD | base64 -d)
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

  cert_alias_names=(ca metricca)

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
}

import_certs
