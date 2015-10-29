#!/bin/sh

# Grab command-line arguments
cmdlnargs="$@"

: ${OO_INSTALL_KEEP_ASSETS:="false"}
: ${OO_INSTALL_CONTEXT:="INSTALLCONTEXT"}
: ${TMPDIR:=/tmp}
: ${OO_INSTALL_LOG:=${TMPDIR}/INSTALLPKGNAME.log}
[[ $TMPDIR != */ ]] && TMPDIR="${TMPDIR}/"

if [ $OO_INSTALL_CONTEXT != 'origin_vm' ]
then
  clear
  echo "Checking for necessary tools..."
fi
if [ -e /etc/redhat-release  ]
then
  for i in python python-virtualenv openssh-clients gcc
  do
    rpm -q $i  >/dev/null 2>&1 || { echo >&2 "Missing installation dependency detected.  Please run \"yum install ${i}\"."; exit 1; }
  done
fi
for i in python virtualenv ssh gcc
do
  command -v $i >/dev/null 2>&1 || { echo >&2 "OpenShift installation requires $i on the PATH but it does not appear to be available. Correct this and rerun the installer."; exit 1; }
done

# All instances of INSTALLPKGNAME are replaced during packaging with the actual package name.
if [[ -e ./INSTALLPKGNAME.tgz ]]
then
  if [ $OO_INSTALL_CONTEXT != 'origin_vm' ]
  then
    echo "Using bundled assets."
  fi
  cp INSTALLPKGNAME.tgz ${TMPDIR}/INSTALLPKGNAME.tgz
elif [[ $OO_INSTALL_KEEP_ASSETS == 'true' && -e ${TMPDIR}/INSTALLPKGNAME.tgz ]]
then
  if [ $OO_INSTALL_CONTEXT != 'origin_vm' ]
  then
    echo "Using existing installer assets."
  fi
else
  echo "Downloading oo-install package to ${TMPDIR}INSTALLPKGNAME.tgz..."
  curl -s -o ${TMPDIR}INSTALLPKGNAME.tgz https://install.openshift.com/INSTALLVERPATHINSTALLPKGNAME.tgz
fi

if [ $OO_INSTALL_CONTEXT != 'origin_vm' ]
then
  echo "Extracting oo-install to ${TMPDIR}INSTALLPKGNAME..."
fi
tar xzf ${TMPDIR}INSTALLPKGNAME.tgz -C ${TMPDIR} 2>&1 >> $OO_INSTALL_LOG

echo "Preparing to install.  This can take a minute or two..."
virtualenv ${TMPDIR}/INSTALLPKGNAME 2>&1 >> $OO_INSTALL_LOG
cd ${TMPDIR}/INSTALLPKGNAME 2>&1 >> $OO_INSTALL_LOG
source ./bin/activate 2>&1 >> $OO_INSTALL_LOG
pip install --no-index -f file:///$(readlink -f deps) ansible 2>&1 >> $OO_INSTALL_LOG

# TODO: these deps should technically be handled as part of installing ooinstall
pip install --no-index -f file:///$(readlink -f deps) click 2>&1 >> $OO_INSTALL_LOG
pip install --no-index ./src/ 2>&1 >> $OO_INSTALL_LOG
echo "Installation preperation done!" 2>&1 >> $OO_INSTALL_LOG

echo "Using `ansible --version`" 2>&1 >> $OO_INSTALL_LOG

if [ $OO_INSTALL_CONTEXT != 'origin_vm' ]
then
  echo "Starting oo-install..." 2>&1 >> $OO_INSTALL_LOG
else
  clear
fi
oo-install $cmdlnargs --ansible-playbook-directory ${TMPDIR}/INSTALLPKGNAME/openshift-ansible-*/ --ansible-log-path $OO_INSTALL_LOG

if [ $OO_INSTALL_KEEP_ASSETS == 'true' ]
then
  echo "Keeping temporary assets in ${TMPDIR}"
else
  echo "Removing temporary assets."
  rm -rf ${TMPDIR}INSTALLPKGNAME
  rm -rf ${TMPDIR}INSTALLPKGNAME.tgz
fi

echo "Please see $OO_INSTALL_LOG for full output."

exit
