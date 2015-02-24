#!/bin/bash -eu

NODES=2
MASTERS=1

# If the environment variable OO_PROVDER is defined, it used for the provider
PROVIDER=${OO_PROVIDER:-''}
# Otherwise, default is gce (Google Compute Engine)
if [ "x$PROVIDER" == "x" ];then
   PROVIDER=gce
fi

UPPER_CASE_PROVIDER=$(echo $PROVIDER | tr '[:lower:]' '[:upper:]')


# Use OO_MASTER_PLAYBOOK/OO_NODE_PLAYBOOK environment variables for playbooks if defined,
# otherwise use openshift default values.
MASTER_PLAYBOOK=${OO_MASTER_PLAYBOOK:-'openshift-master'}
NODE_PLAYBOOK=${OO_NODE_PLAYBOOK:-'openshift-node'}


# @formatter:off
function usage {
    cat 1>&2 <<-EOT
        ${0} : [create|terminate|update|list] { ${UPPER_CASE_PROVIDER} environment tag}

        Supported environment tags:
        $(grep --no-messages 'SUPPORTED_ENVS.*=' ./lib/${PROVIDER}_command.rb)
        $([ $? -ne 0 ] && echo "No supported environment tags found for ${PROVIDER}")

        Optional arguments for create:
        [-p|--provider, -m|--masters, -n|--nodes, --master-playbook, --node-playbook]

        Optional arguments for terminate|update:
        [-p|--provider, --master-playbook, --node-playbook]
EOT
}
# @formatter:on

function create_cluster {
    ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$MASTER_PLAYBOOK -c $MASTERS

    ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$NODE_PLAYBOOK -c $NODES

    update_cluster

    echo -e "\nCreated ${MASTERS}/${MASTER_PLAYBOOK} masters and ${NODES}/${NODE_PLAYBOOK} nodes using ${PROVIDER} provider\n"
}

function update_cluster {
    ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$MASTER_PLAYBOOK
    ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$NODE_PLAYBOOK
}

function terminate_cluster {
    ./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=$MASTER_PLAYBOOK
    ./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=$NODE_PLAYBOOK
}

[ -f ./cloud.rb ] || (echo 1>&2 'Cannot find ./cloud.rb' && exit 1)

function check_argval {
    if [[ $1 == -* ]]; then
        echo "Invalid value: '$1'"
        usage
        exit 1
    fi
}

# Using GNU getopt to support both small and long formats
OPTIONS=`getopt -o p:m:n:h --long provider:,masters:,nodes:,master-playbook:,node-playbook:,help \
	        -n "$0" -- "$@"`
eval set -- "$OPTIONS"

while true; do
    case "$1" in
        -h|--help) (usage; exit 1) ; shift ;;
        -p|--provider) PROVIDER="$2" ; check_argval $2 ; shift 2 ;;
        -m|--masters) MASTERS="$2" ; check_argval $2 ; shift 2 ;;
        -n|--nodes) NODES="$2" ; check_argval $2 ; shift 2 ;;
        --master-playbook) MASTER_PLAYBOOK="$2" ; check_argval $2 ; shift 2 ;;
        --node-playbook) NODE_PLAYBOOK="$2" ; check_argval $2 ; shift 2 ;;
        --) shift ; break ;;
        *) break ;;
    esac
done

shift $((OPTIND-1))

[ -z "${1:-}" ] && (usage; exit 1)

case "${1}" in
    'create')
        [ -z "${2:-}" ] && (usage; exit 1)
        ENV="${2}"
        create_cluster ;;
    'update')
        [ -z "${2:-}" ] && (usage; exit 1)
        ENV="${2}"
        update_cluster ;;
    'terminate')
        [ -z "${2:-}" ] && (usage; exit 1)
        ENV="${2}"
        terminate_cluster ;;
    'list')   ./cloud.rb "${PROVIDER}" list ;;
    'help')   usage; exit 0 ;;
    *)
        echo -n 1>&2 "${1} is not a supported operation";
        usage;
        exit 1 ;;
esac

exit 0
