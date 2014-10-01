#!/bin/bash -eu

MINIONS=1
MASTERS=1
PROVIDER=gce

# FIXME: Add option
#MASTER_PLAYBOOK=os3-master
MASTER_PLAYBOOK=openshift-master
#MINION_PLAYBOOK=os3-minion
MINION_PLAYBOOK=openshift-minion


# @formatter:off
function usage {
    cat 1>&2 <<-EOT
        ${0} : [create|destroy|update|list] {GCE environment tag}

        Supported environment tags:
        $(grep 'SUPPORTED_ENVS.*=' ./cloud.rb)
EOT
}
# @formatter:on

function create_cluser {
    for (( i = 0; i < $MINIONS; i ++ )); do
        ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$MINION_PLAYBOOK
    done

    for (( i = 0; i < $MASTERS; i ++ )); do
        ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=$MASTER_PLAYBOOK
    done
    update_cluster
    echo -e "\nCreated ${MASTERS} ${MASTER_PLAYBOOK} masters and ${MINIONS} ${MINION_PLAYBOOK} minions using ${PROVIDER} provider\n"
}

function update_cluster {
    for (( i = 0; i < $MINIONS; i ++ )); do
        ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$MINION_PLAYBOOK
    done

    for (( i = 0; i < $MASTERS; i ++ )); do
        ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=$MASTER_PLAYBOOK
    done
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
        create_cluser ;;
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
