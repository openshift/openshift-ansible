# Running ansible in a docker container
* Building ansible container:

  ```sh
  git clone https://github.com/openshift/openshift-ansible.git
  cd openshift-ansible
  docker build --rm -t ansible .
  ```
* Create /etc/ansible directory on the host machine and copy inventory file (hosts) into it.
* Copy ssh public key of the host machine to master and nodes machines in the cluster.
* Running the ansible container:

  ```sh
  docker run -it --rm --privileged --net=host -v ~/.ssh:/root/.ssh -v /etc/ansible:/etc/ansible ansible
  ```
