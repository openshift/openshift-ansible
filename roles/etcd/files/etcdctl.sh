#!/bin/bash
# Sets up handy aliases for etcd, need etcdctl2 and etcdctl3 because
# command flags are different between the two. Should work on stand
# alone etcd hosts and master + etcd hosts too because we use the peer keys.
etcdctl2() {
 /usr/bin/etcdctl --cert-file /etc/etcd/peer.crt --key-file /etc/etcd/peer.key --ca-file /etc/etcd/ca.crt -C https://`hostname`:2379 ${@}
}

etcdctl3() {
 ETCDCTL_API=3 /usr/bin/etcdctl --cert /etc/etcd/peer.crt --key /etc/etcd/peer.key --cacert /etc/etcd/ca.crt --endpoints https://`hostname`:2379 ${@}
}
