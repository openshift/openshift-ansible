#!/bin/bash -eu

MINIONS=3
MASTERS=1
PROVIDER=gce

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
        ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=os3-minion
    done

    for (( i = 0; i < $MASTERS; i ++ )); do
        ./cloud.rb "${PROVIDER}" launch -e "${ENV}" --type=os3-master
    done
    update_cluster
    echo -e "\nCreated ${MASTERS} masters and ${MINIONS} minions using ${PROVIDER} provider\n"
}

function update_cluster {
    for (( i = 0; i < $MINIONS; i ++ )); do
        ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=os3-minion
    done

    for (( i = 0; i < $MASTERS; i ++ )); do
        ./cloud.rb "${PROVIDER}" config -e "${ENV}" --type=os3-master
    done
}

function terminate_cluster {
    #./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=os3-master
    ./cloud.rb "${PROVIDER}" terminate -e "${ENV}" --type=os3-minion
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
