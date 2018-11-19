#!/bin/bash
for c in $(runc list -q); do
        output=$(runc state $c | grep io.kubernetes.cri-o.ContainerType)
        if [[ "$output" =~ "container" ]]; then
                runc delete -f $c
        fi
        for m in $(mount | grep $c | awk '{print $3}'); do
                umount -R $m
        done
done
for c in $(runc list -q); do
        output=$(runc state $c | grep io.kubernetes.cri-o.ContainerType)
        if [[ "$output" =~ "sandbox" ]]; then
                runc delete -f $c
        fi
        for m in $(mount | grep $c | awk '{print $3}'); do
                umount -R $m
        done
done
mount | grep overlay | awk '{print $3}' | xargs umount | true
mount | grep '/var/lib/containers/storage/' | awk '{print $3}' | xargs umount | true
rm -rf /var/run/containers/storage/*
rm -rf /var/lib/containers/storage/*
