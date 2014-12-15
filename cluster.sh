#!/bin/bash -eu

MINIONS=3
MASTERS=1

# If the environment variable OO_PROVDER is defined, it used for the provider
PROVIDER=${OO_PROVIDER:-''}
# Otherwise, default is gce (Google Compute Engine)
if [ "x$PROVIDER" == "x" ];then
   PROVIDER=gce
fi

UPPER_CASE_PROVIDER=$(echo $PROVIDER | tr '[:lower:]' '[:upper:]')


# FIXME: Add options
MASTER_PLAYBOOK=openshift-master
MINION_PLAYBOOK=openshift-minion


# @formatter:off
function usage {
    cat 1>&2 <<-EOT
        ${0} : [create|terminate|update|list] { ${UPPER_CASE_PROVIDER} environment tag}

        Supported environment tags:
        $(grep 'SUPPORTED_ENVS.*=' ./lib/${PROVIDER}_command.rb)
EOT
}
# @formatter:on

function create_cluster {
    ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$MASTER_PLAYBOOK -c $MASTERS

    ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$MINION_PLAYBOOK -c $MINIONS

    update_cluster

    echo -e "\nCreated ${MASTERS}/${MASTER_PLAYBOOK} masters and ${MINIONS}/${MINION_PLAYBOOK} minions using ${PROVIDER} provider\n"
}

function update_cluster {
    ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$MASTER_PLAYBOOK
    ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$MINION_PLAYBOOK
}

function terminate_cluster {
    ./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=$MASTER_PLAYBOOK
    ./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=$MINION_PLAYBOOK
}

[ -f ./cloud.rb ] || (echo 1>&2 'Cannot find ./cloud.rb' && exit 1)

while getopts ':p:m:n:' flag; do
    case "${flag}" in
        p) PROVIDER="${OPTARG}" ;;
        m) MASTERS="${OPTARG}" ;;
        n) MINIONS="${OPTARG}" ;;
        *)  echo -e 2>&1 "unsupported option $OPTARG\n"
            usage
            exit 1 ;;
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
