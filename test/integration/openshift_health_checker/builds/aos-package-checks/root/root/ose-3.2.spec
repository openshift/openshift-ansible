Name:           atomic-openshift
Version:        3.2
Release:        1
Summary:        package the critical aos packages

License:        NA

Source0:	http://example.com/ose.tgz
BuildArch:	noarch

%package master
Summary:        package the critical aos packages
%package node
Summary:        package the critical aos packages

%description
Package for pretending to provide AOS

%description master
Package for pretending to provide AOS

%description node
Package for pretending to provide AOS

%prep
%setup -q


%build


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT


%files
%files master
%files node
%doc



%changelog
