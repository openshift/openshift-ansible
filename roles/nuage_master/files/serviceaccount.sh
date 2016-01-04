#!/bin/bash
# Parse CLI options
for i in "$@"; do
    case $i in
        --master-cert-dir=*)
            MASTER_DIR="${i#*=}"
            CA_CERT=${MASTER_DIR}/ca.crt
            CA_KEY=${MASTER_DIR}/ca.key
            CA_SERIAL=${MASTER_DIR}/ca.serial.txt
            ADMIN_FILE=${MASTER_DIR}/admin.kubeconfig
        ;;
        --server=*)
            SERVER="${i#*=}"
        ;;
        --output-cert-dir=*)
            OUTDIR="${i#*=}"
            CONFIG_FILE=${OUTDIR}/nuage.kubeconfig
        ;;
    esac
done

# If any are missing, print the usage and exit
if [ -z $SERVER ] || [ -z $OUTDIR ] || [ -z $MASTER_DIR ]; then
    echo "Invalid syntax: $@"
    echo "Usage:"
    echo "  $0 --server=<address>:<port> --output-cert-dir=/path/to/output/dir/ --master-cert-dir=/path/to/master/"
    echo "--master-cert-dir:  Directory where the master's configuration is held"
    echo "--server:           Address of Kubernetes API server (default port is 8443)"
    echo "--output-cert-dir:  Directory to put artifacts in"
    echo ""
    echo "All options are required"
    exit 1
fi

# Login as admin so that we can create the service account
oc login -u system:admin --config=$ADMIN_FILE || exit 1
oc project default --config=$ADMIN_FILE

ACCOUNT_CONFIG='
{
  "apiVersion": "v1",
  "kind": "ServiceAccount",
  "metadata": {
    "name": "nuage"
  }
}
'

# Create the account with the included info
echo $ACCOUNT_CONFIG|oc create --config=$ADMIN_FILE -f -

# Add the cluser-reader role, which allows this service account read access to
# everything in the cluster except secrets
oadm policy add-cluster-role-to-user cluster-reader system:serviceaccounts:default:nuage --config=$ADMIN_FILE

# Generate certificates and a kubeconfig for the service account
oadm create-api-client-config --certificate-authority=${CA_CERT} --client-dir=${OUTDIR} --signer-cert=${CA_CERT} --signer-key=${CA_KEY} --signer-serial=${CA_SERIAL} --user=system:serviceaccounts:default:nuage --master=${SERVER} --public-master=${SERVER} --basename='nuage'

# Verify the finalized kubeconfig
if ! [ $(oc whoami --config=$CONFIG_FILE) == 'system:serviceaccounts:default:nuage' ]; then
    echo "Service account creation failed!"
    exit 1
fi
