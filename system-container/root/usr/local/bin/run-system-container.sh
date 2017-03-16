#!/bin/sh

exec ansible-playbook -i /etc/ansible/hosts ${OPTS} ${PLAYBOOK_FILE}
