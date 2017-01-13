CA=${1:-/etc/openshift/logging/ca.crt}
KEY=${2:-/etc/openshift/logging/system.admin.key}
CERT=${3:-/etc/openshift/logging/system.admin.crt}
openshift_logging_es_host=${4:-logging-es}
openshift_logging_es_port=${5:-9200}
namespace=${6:-logging}

# for each index in _cat/indices
# skip indices that begin with . - .kibana, .operations, etc.
# skip indices that contain a uuid
# get a list of unique project
# daterx - the date regex that matches the .%Y.%m.%d at the end of the indices
# we are interested in - the awk will strip that part off
function get_list_of_indices() {
    curl -s --cacert $CA --key $KEY --cert $CERT https://$openshift_logging_es_host:$openshift_logging_es_port/_cat/indices | \
        awk -v daterx='[.]20[0-9]{2}[.][0-1]?[0-9][.][0-9]{1,2}$' \
        '$3 !~ "^[.]" && $3 !~ "^[^.]+[.][^.]+"daterx && $3 !~ "^project." && $3 ~ daterx {print gensub(daterx, "", "", $3)}' | \
    sort -u
}

# for each index in _cat/indices
# skip indices that begin with . - .kibana, .operations, etc.
# get a list of unique project.uuid
# daterx - the date regex that matches the .%Y.%m.%d at the end of the indices
# we are interested in - the awk will strip that part off
function get_list_of_proj_uuid_indices() {
    curl -s --cacert $CA --key $KEY --cert $CERT https://$openshift_logging_es_host:$openshift_logging_es_port/_cat/indices | \
        awk -v daterx='[.]20[0-9]{2}[.][0-1]?[0-9][.][0-9]{1,2}$' \
            '$3 !~ "^[.]" && $3 ~ "^[^.]+[.][^.]+"daterx && $3 !~ "^project." && $3 ~ daterx {print gensub(daterx, "", "", $3)}' | \
        sort -u
}

if [[ -z "$(oc get pods -l component=es -o jsonpath='{.items[?(@.status.phase == "Running")].metadata.name}')" ]]; then
  echo "No Elasticsearch pods found running.  Cannot update common data model."
  exit 1
fi

count=$(get_list_of_indices | wc -l)
if [ $count -eq 0 ]; then
  echo No matching indices found - skipping update_for_uuid
else
  echo Creating aliases for $count index patterns . . .
  {
    echo '{"actions":['
    get_list_of_indices | \
      while IFS=. read proj ; do
        # e.g. make test.uuid.* an alias of test.* so we can search for
        # /test.uuid.*/_search and get both the test.uuid.* and
        # the test.* indices
        uid=$(oc get project "$proj" -o jsonpath='{.metadata.uid}' 2>/dev/null)
        [ -n "$uid" ] && echo "{\"add\":{\"index\":\"$proj.*\",\"alias\":\"$proj.$uuid.*\"}}"
      done
    echo ']}'
  } | curl -s --cacert $CA --key $KEY --cert $CERT -XPOST -d @- "https://$openshift_logging_es_host:$openshift_logging_es_port/_aliases"
fi

count=$(get_list_of_proj_uuid_indices | wc -l)
if [ $count -eq 0 ] ; then
    echo No matching indexes found - skipping update_for_common_data_model
    exit 0
fi

echo Creating aliases for $count index patterns . . .
# for each index in _cat/indices
# skip indices that begin with . - .kibana, .operations, etc.
# get a list of unique project.uuid
# daterx - the date regex that matches the .%Y.%m.%d at the end of the indices
# we are interested in - the awk will strip that part off
{
  echo '{"actions":['
  get_list_of_proj_uuid_indices | \
    while IFS=. read proj uuid ; do
      # e.g. make project.test.uuid.* and alias of test.uuid.* so we can search for
      # /project.test.uuid.*/_search and get both the test.uuid.* and
      # the project.test.uuid.* indices
      echo "{\"add\":{\"index\":\"$proj.$uuid.*\",\"alias\":\"${PROJ_PREFIX}$proj.$uuid.*\"}}"
    done
  echo ']}'
} | curl -s --cacert $CA --key $KEY --cert $CERT -XPOST -d @- "https://$openshift_logging_es_host:$openshift_logging_es_port/_aliases"
