#
# spec file for package containerinfo-rpm
#
# Copyright (c) 2019 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           containerinfo-rpm
Version:        __VERSION__
Release:        0
Summary:        OBS KIWI post run hook to package container metadata
License:        GPL-3.0-or-later
Group:          Development/Tools/Building
#Url:           TODO
Source0:        %{name}-%{version}.tar.gz
%if 0%{?suse_version} > 1315
BuildRequires:  python3-setuptools
Requires:       python3-setuptools
Requires:       python3-jina2
%else
BuildRequires:  python-setuptools
Requires:       python-setuptools
Requires:       python-jinja2
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
NEED TO REPLACE THIS

%prep
%setup -q -n %{name}-%{version}

%build
%if 0%{?suse_version} > 1315
# Build Python 3 version
python3 setup.py build
%else
# Build Python 2 version
python2 setup.py build
%endif

%install
%if 0%{?suse_version} > 1315
# Install Python 3 version
python3 setup.py install --root %{buildroot} \
    --install-script %{_prefix}/lib/build \
    --install-data %{_datadir}/%{name}
%else
# Install Python 2 version
python2 setup.py install --root %{buildroot} \
    --install-script %{_prefix}/lib/build \
    --install-data %{_datadir}/%{name}
%endif

%files
%defattr(-,root,root)
%dir %{_prefix}/lib/build
%dir %{_datadir}/%{name}
%{_prefix}/lib/build
%{_datadir}/%{name}

%if 0%{?suse_version} < 1500
%doc LICENSE
%else
%license LICENSE
%endif

%changelog
