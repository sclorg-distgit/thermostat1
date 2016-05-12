%{!?scl_name_base:%global scl_name_base thermostat}
%{!?scl_name_version:%global scl_name_version 1}

%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Name:       %scl_name
Version:    2.2
# Release should be higher than el7 builds. Use convention
# 60.X where X is an increasing int. 60 for rhel-6. We use
# 70.X for rhel-7. For some reason we cannot rely on the
# dist tag.
Release:    60.4%{?dist}
Summary:    Package that installs %scl

License:    GPLv2+
Source4:    README
Source5:    LICENSE

# This needs to require all packages shipped with the thermostat1
# collection. The leaf package is thermostat1-thermostat-webapp
# which should pull in thermostat1-thermostat plus all deps, such
# as mongo-java-driver and mongodb from the mongodb collection.
# See RHBZ#1033653 for an explanation as to why thermostat-webapp
# and not thermostat without webapp.
BuildRequires:    scl-utils-build
BuildRequires:    help2man
# Collections we depend on
BuildRequires:    rh-mongodb26-scldevel
BuildRequires:    rh-java-common-scldevel
BuildRequires:    maven30-scldevel
# For java macro expansion
BuildRequires:    rh-java-common-javapackages-tools
Requires:         %{name}-thermostat-webapp
Requires:         %{name}-runtime >= %{version}-%{release}

%description
This is the main package for the %scl Software Collection.

%package runtime
Summary:    Package that handles %scl Software Collection.
Requires:   scl-utils >= 20120927-8
# Thermostat depends on the mongodb collection
%{?scl_mongodb:Requires:   %{scl_mongodb}}
# Starting with RHSCL 2.0 thermostat1 depends on the java common SCL
# for shared dependencies
Requires:   %{?scl_prefix_java_common}runtime
# Older meta package had a -common sub package. Obsololete it
# in -runtime since it got merged into that package.
Obsoletes:  %{name}-common < %{version}-%{release}

%description runtime
Package shipping essential scripts to work with the %scl Software Collection.

%package build
Requires:   scl-utils >= 20120927-8
Requires:   %{name}-scldevel = %{version}-%{release}
Summary:    Build support tools for the %scl Software Collection.

%description build
Package shipping essential configuration marcros/files in order to be able
to build %scl Software Collection.

%package scldevel
Summary:    Package shipping development files for %{scl}.
Group:      Applications/File
# This version of javapackages-tools has the fix for
# RHBZ#1098523 and RHBZ#1122947
Requires:   %{?scl_prefix_java_common}javapackages-tools
Requires:   %{name}-runtime = %{version}-%{release}
Requires:   %{?scl_prefix_java_common}scldevel
Requires:   %{?scl_prefix_mongodb}scldevel
Requires:   %{?scl_prefix_maven}scldevel

%description scldevel
Development files for %scl (useful e.g. for hierarchical collection
building with transitive dependencies).

%prep
%setup -c -T
#===================#
# SCL enable script #
#===================#
cat <<EOF >enable
# The thermostat1 collection depends on the mongodb collection
# for the mongo-java-driver and on the rh-java-commmon collection
# for shared dependencies. We need to source the enable script
# in order for xmvn builds to work.
. scl_source enable %{?scl_mongodb} %{?scl_java_common}

# Generic variables
export PATH="%{_bindir}:\${PATH:-/bin:/usr/bin}"
export MANPATH="%{_mandir}:\${MANPATH}"

# Needed by Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"

# Required by XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"

# Not really needed by anything for now, but kept for consistency with
# XDG_CONFIG_DIRS.
export XDG_DATA_DIRS="%{_datadir}:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
EOF

#===========#
# java.conf #
#===========#
cat <<EOF >java.conf
# Java configuration file for %{scl} software collection.
JAVA_LIBDIR=%{_javadir}
JNI_LIBDIR=%{_jnidir}
JVM_ROOT=%{_jvmdir}
EOF

#=============#
# XMvn config #
#=============#
cat <<EOF >configuration.xml
<!-- XMvn configuration file for %{scl} software collection -->
<configuration>
  <resolverSettings>
    <metadataRepositories>
      <repository>/opt/rh/%{scl}/root/usr/share/maven-metadata</repository>
    </metadataRepositories>
    <prefixes>
      <prefix>/opt/rh/%{scl}/root</prefix>
    </prefixes>
  </resolverSettings>
  <installerSettings>
    <metadataDir>opt/rh/%{scl}/root/usr/share/maven-metadata</metadataDir>
  </installerSettings>
  <repositories>
    <repository>
      <id>resolve-%{scl}</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>resolve</id>
      <type>compound</type>
      <configuration>
        <repositories>
        <!-- The %{scl} collection resolves from:
                    1. local repository
                    2. %{scl}
                    3. java-common
                    4. mongodb
                    5. maven
               collections. -->
          <repository>resolve-local</repository>
          <repository>resolve-%{scl}</repository>
          <repository>resolve-java-common</repository>
          <repository>resolve-%{scl_mongodb}</repository>
          <repository>resolve-%{scl_maven}</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-install</repository>
        </repositories>
      </configuration>
    </repository>
  </repositories>
</configuration>
EOF

#=====================#
# Javapackages config #
#=====================#
cat <<EOF >javapackages-config.json
{
    "maven.req": {
	"always_generate": [
	    "%{scl}-runtime"
	],
	"java_requires": {
	    "package_name": "java",
	    "always_generate": true,
	    "skip": false
	},
	"java_devel_requires": {
	    "package_name": "java-devel",
	    "always_generate": false,
	    "skip": false
	}
    },
    "javadoc.req": {
	"always_generate": [
	    "%{scl}-runtime"
	]
    }
}
EOF

#=====================#
# README and man page #
#=====================#
# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE4})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE5} .

# scldevel macros
cat << EOF > macros.%{scl_name_base}-scldevel
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
EOF

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7

# Fix single quotes in man page. See RHBZ#1219531
#
# http://lists.gnu.org/archive/html/groff/2008-06/msg00001.html suggests that
# using "'" for quotes is correct, but the current implementation of man in 6
# mangles it when rendering.
sed -i "s/'/\\\\(aq/g" %{scl_name}.7


%install
# Parentheses are needed here as workaround for rhbz#1017085
(%scl_install)

install -d -m 755 %{buildroot}%{_scl_scripts}
install -p -m 755 enable %{buildroot}%{_scl_scripts}/

install -d -m 755 %{buildroot}%{_sysconfdir}/java
install -p -m 644 java.conf %{buildroot}%{_sysconfdir}/java/
install -p -m 644 javapackages-config.json %{buildroot}%{_sysconfdir}/java/

install -d -m 755 %{buildroot}%{_sysconfdir}/xdg/xmvn
install -p -m 644 configuration.xml %{buildroot}%{_sysconfdir}/xdg/xmvn/

# Create java/maven/icons directories so that they'll get properly owned.
# These are listed in the scl_files macro. See also: RHBZ#1057169
mkdir -p %{buildroot}%{_javadir}
mkdir -p %{buildroot}%{_prefix}/lib/java
mkdir -p %{buildroot}%{_javadocdir}
mkdir -p %{buildroot}%{_mavenpomdir}
mkdir -p %{buildroot}%{_datadir}/maven-effective-poms
mkdir -p %{buildroot}%{_datadir}/maven-metadata
mkdir -p %{buildroot}%{_mavendepmapfragdir}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

# scldevel macro
install -p -m 644 macros.%{scl_name_base}-scldevel %{buildroot}%{_root_sysconfdir}/rpm/

# Empty package (no file content).  The sole purpose of this package
# is collecting its dependencies so that the whole SCL can be
# installed by installing %{name}.
%files

%files runtime
%{scl_files}
%doc LICENSE
%doc README
%dir %{_sysconfdir}/java
%{_mandir}/man7/%{scl_name}.*
%{_sysconfdir}/java/java.conf
%{_sysconfdir}/java/javapackages-config.json
%{_sysconfdir}/xdg/xmvn/configuration.xml
%dir %{_datadir}/maven-metadata

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Wed Mar 30 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.2-60.4
- Own in collection directories.
- Resolves: RHBZ#1317970

* Tue Mar 15 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.2-60.3
- Install javapackages-config.json file.

* Wed Jan 27 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.2-60.2
- Apply patch for RHBZ#1219531. Fix quotes in man page.

* Wed Jan 27 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.2-60.1
- Rebuild for RHSCL 2.2 update.

* Wed Jan 28 2015 Omair Majid <omajid@redhat.com> - 2.0-60.9
- Require mongodb26 scl.

* Mon Jan 19 2015 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.8
- Fix xmvn config so as to generate correct provides/requires.

* Mon Jan 19 2015 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.7
- Switch to mongodb 2.6.

* Thu Jan 15 2015 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.6
- Really remove mongodb24 deps.

* Thu Jan 15 2015 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.5
- Remove own java requires/provides generators.

* Thu Jan 15 2015 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.4
- Adjust XMvn and javapackages configuration

* Thu Dec 18 2014 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.3
- Allow for building srpm without mongdb scldevel package
  being installed.

* Tue Dec 16 2014 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.2
- Change to scl_prefix_* and scl_* rather than hard-code collection
  names where possible. Only use hard-coded names in BR.

* Tue Dec 16 2014 Severin Gehwolf <sgehwolf@redhat.com> - 2.0-60.1
- Start RHSCL 2.0 development.
- Depend on rh-java-common collection for shared dependencies.
- Bump version to match RHSCL version.

* Tue Aug 05 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.2-60.3
- Be sure -runtime owns javadoc.req with proper mode. Work-around
  for RHBZ#1122109.
- Resolves: RHBZ#1121715.

* Tue Jun 24 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.2-60.2
- Obsolete merged -common sub-package.

* Tue Jun 17 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.2-60.1
- Fix xmvn configuration.
- Add maven30-javapackages-tools BR for java macro expansion.

* Mon Jun 16 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.2-6.2
- Don't enable maven30 in main enable script. It's a
  build only dependency.

* Fri Jun 13 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.2-6.1
- Start RHSCL 1.2 development.
- Merge common/runtime subpackages.
- Depend on maven30 collection for building.
- Produce proper scldevel package for rebuilding.

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 1.1-4
- Fix path typo in README
  Related: #1061461

* Thu Feb 13 2014 Omair Majid <omajid@redhat.com> - 1.1-3
- Update README
- Resolves: RHBZ#1061461

* Wed Feb 12 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1.1-2
- Introduce scldevel subpackage.
- Resolves: RHBZ#1063360

* Wed Feb 12 2014 Omair Majid <omajid@redhat.com> - 1.1-1
- Add LICENSE, README and man page
- Bump version to 1.1
- Resolves: RHBZ#1061461

* Mon Jan 27 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1-18
- Own common java/maven/icon directories for this scl.
- Resolves: RHBZ#1057169

* Wed Jan 15 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1-17
- Depend on minimal scl-utils version which contains
  the scl_source file.
- Include release in requires for thermostat1-common.
- Resolves: RHBZ#1051576

* Wed Dec 18 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-16
- Remove osgi provides/requires generation
- Resolves: RHBZ#1042888

* Wed Dec 18 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-15
- Fix javadoc requires/provides generation
- Resolves: RHBZ#1042912

* Fri Dec 13 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-14
- Make the thermostat1 metapackage depend on webapp.
- Resolves: RHBZ#891540. 

* Wed Nov 27 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-13
- Properly source dependent mongodb24 SCL. 

* Wed Nov 27 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-13
- Properly source dependent mongodb24 SCL. 

* Wed Nov 27 2013 Omair Majid <omajid@redhat.com> - 1-12
- Provide java = 1:1.7.0 in -build just in case the openjdk package
  doesn't.

* Thu Nov 21 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-11
- Use java-1.7.0-openjdk-devel over java7-devel in Requires of build
  subpackage.

* Fri Nov 15 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-10
- Add java7-devel to Requires of build subpackage

* Wed Nov 13 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-9
- Re-enable mongodb24 dependency.

* Tue Nov 12 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-8
- Disable mongodb dependency for now (rhbz#1029128)

* Mon Nov 11 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-7
- Add provides and requires generator wrapper

* Mon Nov 11 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-6
- Enable the mongodb24 collection in the thermostat1
  enable scriptlet.

* Thu Nov 07 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-5
- Fix xmvn repo dependency on mongodb24 collection.

* Fri Oct 25 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-4
- Move essential files into common subpackage.

* Fri Oct 25 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-3
- First version including Java SCL configs.

* Tue Sep 24 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-2
- Bump release for rebuild.

* Mon Jul 29 2013 Omair Majid <omajid@redhat.com> 1-1
- Initial package
