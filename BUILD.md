# openshift-ansible RPM Build instructions
We use tito to make building and tracking revisions easy.

For more information on tito, please see the [Tito home page](https://github.com/dgoodwin/tito "Tito home page").


## Build openshift-ansible-bin
- Change into openshift-ansible/bin
```
cd openshift-ansible/bin
```
- Build a test package (no tagging needed)
```
tito build --test --rpm
```
- Tag a new build (bumps version number and adds log entries)
```
tito tag
```
- Follow the on screen tito instructions to push the tags
- Build a new package based on the latest tag information
```
tito build --rpm
```


## Build openshift-ansible-inventory
- Change into openshift-ansible/inventory
```
cd openshift-ansible/inventory
```
- Build a test package (no tagging needed)
```
tito build --test --rpm
```
- Tag a new build (bumps version number and adds log entries)
```
tito tag
```
- Follow the on screen tito instructions to push the tags
- Build a new package based on the latest tag information
```
tito build --rpm
```
