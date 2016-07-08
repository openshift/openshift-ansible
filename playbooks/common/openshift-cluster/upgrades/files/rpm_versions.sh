#!/bin/bash
if [ `which dnf 2> /dev/null` ]; then
  installed=$(dnf repoquery --installed --latest-limit 1 -d 0 --qf '%{version}-%{release}' "${@}" 2> /dev/null)
  available=$(dnf repoquery --available --latest-limit 1 -d 0 --qf '%{version}-%{release}' "${@}" 2> /dev/null)
else
  installed=$(repoquery --plugins --pkgnarrow=installed --qf '%{version}-%{release}' "${@}" 2> /dev/null)
  available=$(repoquery --plugins --pkgnarrow=available --qf '%{version}-%{release}' "${@}" 2> /dev/null)
fi

echo "---"
echo "curr_version: ${installed}"
echo "avail_version: ${available}"
