%global pybasever 3.1
%global pylibdir %{_libdir}/python%{pybasever}

# We want to byte-compile the .py files within the packages using the new
# python3 binary.
# 
# Unfortunately, rpmbuild's infrastructure requires us to jump through some
# hoops to avoid byte-compiling with the system python 2 version:
#   /usr/lib/rpm/redhat/macros sets up build policy that (amongst other things)
# defines __os_install_post.  In particular, "brp-python-bytecompile" is
# invoked without an argument thus using the wrong version of python
# (/usr/bin/python, rather than the freshly built python), thus leading to
# numerous syntax errors, and incorrect magic numbers in the .pyc files.  We
# thus override __os_install_post to avoid invoking this script:
%global __os_install_post /usr/lib/rpm/redhat/brp-compress \
  %{!?__debug_package:/usr/lib/rpm/redhat/brp-strip %{__strip}} \
  /usr/lib/rpm/redhat/brp-strip-static-archive %{__strip} \
  /usr/lib/rpm/redhat/brp-strip-comment-note %{__strip} %{__objdump} \
  /usr/lib/rpm/redhat/brp-python-hardlink 
# to remove the invocation of brp-python-bytecompile, whilst keeping the
# invocation of brp-python-hardlink (since this should still work for python3
# pyc/pyo files)

Summary: Version 3 of the Python programming language aka Python 3000
Name: python3
Version: %{pybasever}.1
Release: 18%{?dist}
License: Python
Group: Development/Languages
Source: http://python.org/ftp/python/%{version}/Python-%{version}.tar.bz2

# Avoid having various bogus auto-generated Provides lines for the various
# python c modules' SONAMEs:
Source1: find-provides-without-python-sonames.sh
%global _use_internal_dependency_generator 0
%global __find_provides %{SOURCE1}

# Supply various useful macros for building python 3 modules:
#  __python3, python3_sitelib, python3_sitearch
Source2: macros.python3

Patch0: python-3.1.1-config.patch


# Fixup distutils/unixccompiler.py to remove standard library path from rpath:
# Was Patch0 in ivazquez' python3000 specfile:
Patch1:         Python-3.1.1-rpath.patch

# Fixup importlib/_bootstrap.py so that it correctly handles being unable to
# open .pyc files for writing
# Sent upstream as http://bugs.python.org/issue7187
Patch2: python-3.1.1-importlib-fix-handling-of-readonly-pyc-files.patch

# The four TestMIMEAudio tests fail due to "audiotest.au" not being packaged.
# It's simplest to remove them:
Patch3: python-3.1.1-remove-mimeaudio-tests.patch

# ImportTests.test_issue1267 in test_imp.py reads pydoc.py's shebang line and
# checks that it read it correctly.
#
# Since we modify the shebang lines in our packaging, we also need to modify
# the expected value in this test:
Patch4: python-3.1.1-apply-our-changes-to-expected-shebang-for-test_imp.patch

# test_tk test_ttk_guionly and test_ttk_textonly all rely on tkinter/test, but
# upstream's Makefile.pre.in doesn't install that subdirectory; patch it so that
# it does:
Patch5: python-3.1.1-install-tkinter-tests.patch
# (The resulting test support code is in the tkinter subpackage, but
# this is not a major problem)

# Patch the Makefile.pre.in so that the generated Makefile doesn't try to build
# a libpythonMAJOR.MINOR.a (bug 550692):
Patch6: python-3.1.1-no-static-lib.patch

Patch102: python-3.1.1-lib64.patch

# http://bugs.python.org/issue6999 -- fixed in r75062
Patch200: python-3.1.1-pathfix.patch


BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: readline-devel, openssl-devel, gmp-devel
BuildRequires: ncurses-devel, gdbm-devel, zlib-devel, expat-devel
BuildRequires: libGL-devel gcc-c++ libX11-devel glibc-devel
BuildRequires: bzip2 tar /usr/bin/find pkgconfig tcl-devel tk-devel
BuildRequires: tix-devel bzip2-devel sqlite-devel
BuildRequires: autoconf
BuildRequires: db4-devel >= 4.7
BuildRequires: libffi-devel

URL: http://www.python.org/

# See notes in bug 532118:
Provides: python(abi) = %{pybasever}

%description
Python 3 is a new version of the language that is incompatible with the 2.x
line of releases. The language is mostly the same, but many details, especially
how built-in objects like dictionaries and strings work, have changed
considerably, and a lot of deprecated features have finally been removed.

%package libs
Summary:        Python 3 runtime libraries
Group:          Development/Libraries
#Requires:       %{name} = %{version}-%{release}

%description libs
This package contains files used to embed Python 3 into applications.

%package devel
Summary: Libraries and header files needed for Python 3 development
Group: Development/Libraries
Requires: %{name}%{?_isa} = %{version}-%{release}
Conflicts: %{name} < %{version}-%{release}

%description devel
This package contains libraries and header files used to build applications 
with and native libraries for Python 3

%package tools
Summary: A collection of tools included with Python 3
Group: Development/Tools
Requires: %{name} = %{version}-%{release}
Requires: %{name}-tkinter = %{version}-%{release}

%description tools
This package contains several tools included with Python 3

%package tkinter
Summary: A GUI toolkit for Python 3
Group: Development/Languages
BuildRequires:  tcl, tk
Requires: %{name} = %{version}-%{release}

%description tkinter
The Tkinter (Tk interface) program is an graphical user interface for
the Python scripting language.

%package test
Summary: The test modules from the main python 3 package
Group: Development/Languages
Requires: %{name} = %{version}-%{release}
Requires: %{name}-tools = %{version}-%{release}

%description test
The test modules from the main %{name} package.
These are in a separate package to save space, as they are almost never used
in production.

You might want to install the python3-test package if you're developing
python 3 code that uses more than just unittest and/or test_support.py.

%prep
%setup -q -n Python-%{version}
chmod +x %{SOURCE1}

# Ensure that we're using the system copy of libffi, rather than the copy
# shipped by upstream in the tarball:
for SUBDIR in darwin libffi libffi_arm_wince libffi_msvc libffi_osx ; do
  rm -r Modules/_ctypes/$SUBDIR || exit 1 ;
done

%patch0 -p1 -b .config
%patch1 -p1 -b .rpath
%patch2 -p0 -b .fix-handling-of-readonly-pyc-files
%patch3 -p1 -b .remove-mimeaudio-tests
%patch4 -p1 -b .apply-our-changes-to-expected-shebang
%patch5 -p1 -b .install-tkinter-tests
%patch6 -p1 -b .no-static-lib

%if "%{_lib}" == "lib64"
%patch102 -p1 -b .lib64
%endif

%patch200 -p1 -b .pathfix

# Currently (2010-01-15), http://docs.python.org/library is for 2.6, and there
# are many differences between 2.6 and the Python 3 library.
#
# Fix up the URLs within pydoc to point at the documentation for this
# MAJOR.MINOR version:
#
sed --in-place \
    --expression="s|http://docs.python.org/library|http://docs.python.org/%{pybasever}/library|g" \
    Lib/pydoc.py || exit 1

%build
export CFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC"
export CXXFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC"
export CPPFLAGS="`pkg-config --cflags-only-I libffi`"
export OPT="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC"
export LINKCC="gcc"
export CFLAGS="$CFLAGS `pkg-config --cflags openssl`"
export LDFLAGS="$LDFLAGS `pkg-config --libs-only-L openssl`"

autoconf
%configure --enable-ipv6 --with-wide-unicode --enable-shared --with-system-ffi

make OPT="$CFLAGS" %{?_smp_mflags}


%install
rm -fr $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_prefix} $RPM_BUILD_ROOT%{_mandir}

make install DESTDIR=$RPM_BUILD_ROOT

mkdir -p ${RPM_BUILD_ROOT}%{pylibdir}/site-packages

mv ${RPM_BUILD_ROOT}%{_bindir}/2to3 ${RPM_BUILD_ROOT}%{_bindir}/2to3-3

# Development tools
install -m755 -d ${RPM_BUILD_ROOT}%{pylibdir}/Tools
install Tools/README ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/freeze ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/i18n ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/modulator ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/pynche ${RPM_BUILD_ROOT}%{pylibdir}/Tools/
cp -ar Tools/scripts ${RPM_BUILD_ROOT}%{pylibdir}/Tools/

# Documentation tools
install -m755 -d $RPM_BUILD_ROOT%{pylibdir}/Doc
cp -ar Doc/tools $RPM_BUILD_ROOT%{pylibdir}/Doc/

# Demo scripts
cp -ar Demo $RPM_BUILD_ROOT%{pylibdir}/

find $RPM_BUILD_ROOT%{pylibdir}/lib-dynload -type d | sed "s|$RPM_BUILD_ROOT|%dir |" > dynfiles
find $RPM_BUILD_ROOT%{pylibdir}/lib-dynload -type f | \
  grep -v "_tkinter.so$" | \
  grep -v "_ctypes_test.so$" | \
  grep -v "_testcapimodule.so$" | \
  sed "s|$RPM_BUILD_ROOT||" >> dynfiles

# Fix for bug #136654
rm -f $RPM_BUILD_ROOT%{pylibdir}/email/test/data/audiotest.au $RPM_BUILD_ROOT%{pylibdir}/test/audiotest.au

%if "%{_lib}" == "lib64"
install -d $RPM_BUILD_ROOT/usr/lib/python%{pybasever}/site-packages
%endif

# Make python3-devel multilib-ready (bug #192747, #139911)
%global _pyconfig32_h pyconfig-32.h
%global _pyconfig64_h pyconfig-64.h

%ifarch ppc64 s390x x86_64 ia64 alpha sparc64
%global _pyconfig_h %{_pyconfig64_h}
%else
%global _pyconfig_h %{_pyconfig32_h}
%endif
mv $RPM_BUILD_ROOT%{_includedir}/python%{pybasever}/pyconfig.h \
   $RPM_BUILD_ROOT%{_includedir}/python%{pybasever}/%{_pyconfig_h}
cat > $RPM_BUILD_ROOT%{_includedir}/python%{pybasever}/pyconfig.h << EOF
#include <bits/wordsize.h>

#if __WORDSIZE == 32
#include "%{_pyconfig32_h}"
#elif __WORDSIZE == 64
#include "%{_pyconfig64_h}"
#else
#error "Unknown word size"
#endif
EOF

# Fix for bug 201434: make sure distutils looks at the right pyconfig.h file
sed -i -e "s/'pyconfig.h'/'%{_pyconfig_h}'/" $RPM_BUILD_ROOT%{pylibdir}/distutils/sysconfig.py

# Switch all shebangs to refer to the specific Python version.
LD_LIBRARY_PATH=. ./python Tools/scripts/pathfix.py -i "%{_bindir}/python%{pybasever}" $RPM_BUILD_ROOT

# Remove shebang lines from .py files that aren't executable, and
# remove executability from .py files that don't have a shebang line:
find $RPM_BUILD_ROOT -name \*.py \
  \( \( \! -perm /u+x,g+x,o+x -exec sed -e '/^#!/Q 0' -e 'Q 1' {} \; \
  -print -exec sed -i '1d' {} \; \) -o \( \
  -perm /u+x,g+x,o+x ! -exec grep -m 1 -q '^#!' {} \; \
  -exec chmod a-x {} \; \) \)

# .xpm and .xbm files should not be executable:
find $RPM_BUILD_ROOT \
  \( -name \*.xbm -o -name \*.xpm -o -name \*.xpm.1 \) \
  -exec chmod a-x {} \;

# Remove executable flag from files that shouldn't have it:
chmod a-x \
  $RPM_BUILD_ROOT%{pylibdir}/Demo/comparisons/patterns \
  $RPM_BUILD_ROOT%{pylibdir}/distutils/tests/Setup.sample \
  $RPM_BUILD_ROOT%{pylibdir}/Demo/rpc/test \
  $RPM_BUILD_ROOT%{pylibdir}/Tools/README \
  $RPM_BUILD_ROOT%{pylibdir}/Demo/scripts/newslist.doc \
  $RPM_BUILD_ROOT%{pylibdir}/Demo/md5test/foo

# Get rid of DOS batch files:
find $RPM_BUILD_ROOT -name \*.bat -exec rm {} \;

# Get rid of backup files:
find $RPM_BUILD_ROOT/ -name "*~" -exec rm -f {} \;
find . -name "*~" -exec rm -f {} \;
rm -f $RPM_BUILD_ROOT%{pylibdir}/LICENSE.txt
# Junk, no point in putting in -test sub-pkg
rm -f ${RPM_BUILD_ROOT}/%{pylibdir}/idlelib/testcode.py*

# Get rid of stray patch file from buildroot:
rm -f $RPM_BUILD_ROOT%{pylibdir}/test/test_imp.py.apply-our-changes-to-expected-shebang # from patch 4

# Fix end-of-line encodings:
find $RPM_BUILD_ROOT/ -name \*.py -exec sed -i 's/\r//' {} \;

# Fix an encoding:
iconv -f iso8859-1 -t utf-8 $RPM_BUILD_ROOT/%{pylibdir}/Demo/rpc/README > README.conv && mv -f README.conv $RPM_BUILD_ROOT/%{pylibdir}/Demo/rpc/README

# Note that 
#  %{pylibdir}/Demo/distutils/test2to3/setup.py
# is in iso-8859-1 encoding, and that this is deliberate; this is test data
# for the 2to3 tool, and one of the functions of the 2to3 tool is to fixup
# character encodings within python source code

# Do bytecompilation with the new interpreter.
LD_LIBRARY_PATH=. /usr/lib/rpm/brp-python-bytecompile ./python

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find $RPM_BUILD_ROOT \
    -perm 555 -exec chmod 755 {} \;

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rpm
install -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/rpm

%check
# Run the upstream test suite, using the "runtests.sh" harness from the upstream
# tarball.
# I'm seeing occasional hangs in "test_httplib" when running the test suite inside
# Koji.  For that reason I exclude that one.
LD_LIBRARY_PATH=$(pwd) ./runtests.sh -x test_httplib

# Note that we're running the tests using the version of the code in the builddir,
# not in the buildroot.

# The harness only emits the names of the test scripts it ran, along with a
# summary of the form:
#   2 BAD
# 313 GOOD
#  22 SKIPPED
# 337 total
# As a byproduct it writes files "GOOD", "BAD", "SKIPPED", listing names of
# files (e.g. "test_imp") along with a subdirectory OUT containing files of the
# form $TEST.out
# Each such logfile starts with a line indicating the name of the test

# Output the logs from failing tests, so that they are captured in the rpmbuild
# log:
for TESTNAME in $(cat BAD); do
  cat OUT/$TESTNAME.out ; 
done

# There are 5 expected BAD results here:
#
# (1) test_distutils.py: tries to build an RPM inside the rpmbuild; I'll simply
# let this one fail for now (has trouble linking against -lpython3.1; perhaps
# LD_LIBRARY_PATH is being discarded somewhere?)
#
# (2) test_imp.py: ImportTests.test_issue1267 in test_imp.py reads pydoc.py's
# shebang line and checks that it read it correctly.tests that the shebang line
# is as expected.  Unfortunately if we patch this up in the buildir (in the
# build phase), then the "make install" will try to reference
# /usr/bin/python%{pybasever} which won't exist on a clean build environment.
# So we fix up the shebang lines after this in the install phase, and expect
# this test to fail in the check phase.  It ought to pass when run on the built
# RPMs
#
# (3) test_socket.py:testSockName can fail here if DNS isn't properly set up:
#     my_ip_addr = socket.gethostbyname(socket.gethostname())
# socket.gaierror: [Errno -2] Name or service not known
#
# (4) test_subprocess: merely get "errors occurred"
#
# (5) test_telnet: can get a "socket.error: [Errno 104] Connection reset by peer"
#
# Some additional tests fail when running the test suite as non-root outside of
# the build, due to permissions issues.

%clean
rm -fr $RPM_BUILD_ROOT

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files -f dynfiles
%defattr(-, root, root)
%doc LICENSE README
%{_bindir}/pydoc*
%{_bindir}/python3
%{_bindir}/python%{pybasever}
%{_mandir}/*/*
%dir %{pylibdir}
%dir %{pylibdir}/site-packages
%{pylibdir}/site-packages/README
%{pylibdir}/*.py*
%{pylibdir}/*.doc
%{pylibdir}/wsgiref.egg-info
%dir %{pylibdir}/ctypes
%{pylibdir}/ctypes/*.py*
%{pylibdir}/ctypes/macholib
%{pylibdir}/curses
%dir %{pylibdir}/dbm
%{pylibdir}/dbm/*.py*
%dir %{pylibdir}/distutils
%{pylibdir}/distutils/*.py*
%{pylibdir}/distutils/README
%{pylibdir}/distutils/command
%dir %{pylibdir}/email
%{pylibdir}/email/*.py*
%{pylibdir}/email/mime
%{pylibdir}/encodings
%{pylibdir}/html
%{pylibdir}/http
%{pylibdir}/idlelib
%dir %{pylibdir}/importlib
%{pylibdir}/importlib/*.py*
%dir %{pylibdir}/json
%{pylibdir}/json/*.py*
%{pylibdir}/lib2to3
%exclude %{pylibdir}/lib2to3/tests
%{pylibdir}/logging
%{pylibdir}/multiprocessing
%{pylibdir}/plat-linux2
%{pylibdir}/pydoc_data
%dir %{pylibdir}/sqlite3
%{pylibdir}/sqlite3/*.py*
%dir %{pylibdir}/test
%{pylibdir}/test/__init__.py*
%{pylibdir}/urllib
%{pylibdir}/wsgiref
%{pylibdir}/xml
%{pylibdir}/xmlrpc
%if "%{_lib}" == "lib64"
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages
%endif

# "Makefile" and the config-32/64.h file are needed by
# distutils/sysconfig.py:_init_posix(), so we include them in the core
# package, along with their parent directories (bug 531901):
%dir %{pylibdir}/config
%{pylibdir}/config/Makefile
%dir %{_includedir}/python%{pybasever}
%{_includedir}/python%{pybasever}/%{_pyconfig_h}

%files libs
%defattr(-,root,root,-)
%{_libdir}/libpython%{pybasever}.so.*

%files devel
%defattr(-,root,root)
%{pylibdir}/config/*
%exclude %{pylibdir}/config/Makefile
/usr/include/python%{pybasever}/*.h
%exclude /usr/include/python%{pybasever}/%{_pyconfig_h}
%doc Misc/README.valgrind Misc/valgrind-python.supp Misc/gdbinit
%{_bindir}/python3-config
%{_bindir}/python%{pybasever}-config
%{_libdir}/libpython%{pybasever}.so
%{_libdir}/pkgconfig/python*.pc
%config(noreplace) %{_sysconfdir}/rpm/macros.python3

%files tools
%defattr(-,root,root,755)
%{_bindir}/2to3*
%{_bindir}/idle*
%{pylibdir}/Tools
%doc %{pylibdir}/Demo
%exclude %{pylibdir}/Demo/distutils
%exclude %{pylibdir}/Demo/md5test
%doc %{pylibdir}/Doc

%files tkinter
%defattr(-,root,root,755)
%{pylibdir}/tkinter
%exclude %{pylibdir}/tkinter/test
%{pylibdir}/lib-dynload/_tkinter.so

%files test
%defattr(-, root, root)
%{pylibdir}/ctypes/test
%{pylibdir}/distutils/tests
%{pylibdir}/email/test
%{pylibdir}/importlib/test
%{pylibdir}/json/tests
%{pylibdir}/sqlite3/test
%{pylibdir}/test
%{pylibdir}/lib-dynload/_ctypes_test.so
%{pylibdir}/lib-dynload/_testcapimodule.so
%{pylibdir}/lib2to3/tests
%doc %{pylibdir}/Demo/distutils
%doc %{pylibdir}/Demo/md5test
%{pylibdir}/tkinter/test

%changelog
* Wed Jan 20 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-18
- move lib2to3 from -tools subpackage to main package (bug 556667)

* Sun Jan 17 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-17
- patch Makefile.pre.in to avoid building static library (patch 6, bug 556092)

* Fri Jan 15 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-16
- use the %%{_isa} macro to ensure that the python-devel dependency on python
is for the correct multilib arch (#555943)
- delete bundled copy of libffi to make sure we use the system one

* Fri Jan 15 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-15
- fix the URLs output by pydoc so they point at python.org's 3.1 build of the
docs, rather than the 2.6 build

* Wed Jan 13 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-14
- replace references to /usr with %%{_prefix}; replace references to
/usr/include with %%{_includedir} (Toshio)

* Mon Jan 11 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-13
- fix permission on find-provides-without-python-sonames.sh from 775 to 755

* Mon Jan 11 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-12
- remove build-time requirements on tix and tk, since we already have
build-time requirements on the -devel subpackages for each of these (Thomas
Spura)
- replace usage of %%define with %%global (Thomas Spura)
- remove forcing of CC=gcc as this old workaround for bug 109268 appears to
longer be necessary
- move various test files from the "tools"/"tkinter" subpackages to the "test"
subpackage

* Thu Jan  7 2010 David Malcolm <dmalcolm@redhat.com> - 3.1.1-11
- add %%check section (thanks to Thomas Spura)
- update patch 4 to use correct shebang line
- get rid of stray patch file from buildroot

* Tue Nov 17 2009 Andrew McNabb <amcnabb@mcnabbs.org> - 3.1.1-10
- switched a few instances of "find |xargs" to "find -exec" for consistency.
- made the description of __os_install_post more accurate.

* Wed Nov  4 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-9
- add macros.python3 to the -devel subpackage, containing common macros for use
when packaging python3 modules

* Tue Nov  3 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-8
- add a provides of "python(abi)" (see bug 532118)
- fix issues identified by a.badger in package review (bug 526126, comment 39):
  - use "3" thoughout metadata, rather than "3.*"
  - remove conditional around "pkg-config openssl"
  - use standard cleanup of RPM_BUILD_ROOT
  - replace hardcoded references to /usr with _prefix macro
  - stop removing egg-info files
  - use /usr/bin/python3.1 rather than /use/bin/env python3.1 when fixing
up shebang lines
  - stop attempting to remove no-longer-present .cvsignore files
  - move the post/postun sections above the "files" sections

* Thu Oct 29 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-7
- remove commented-away patch 51 (python-2.6-distutils_rpm.patch): the -O1
flag is used by default in the upstream code
- "Makefile" and the config-32/64.h file are needed by distutils/sysconfig.py
_init_posix(), so we include them in the core package, along with their parent
directories (bug 531901)

* Tue Oct 27 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-6
- reword description, based on suggestion by amcnabb
- fix the test_email and test_imp selftests (patch 3 and patch 4 respectively)
- fix the test_tk and test_ttk_* selftests (patch 5)
- fix up the specfile's handling of shebang/perms to avoid corrupting
test_httpservers.py (sed command suggested by amcnabb)

* Thu Oct 22 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-5
- fixup importlib/_bootstrap.py so that it correctly handles being unable to
open .pyc files for writing (patch 2, upstream issue 7187)
- actually apply the rpath patch (patch 1)

* Thu Oct 22 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-4
- update patch0's setup of the crypt module to link it against libcrypt
- update patch0 to comment "datetimemodule" back out, so that it is built
using setup.py (see Setup, option 3), thus linking it statically against
timemodule.c and thus avoiding a run-time "undefined symbol:
_PyTime_DoubleToTimet" failure on "import datetime"

* Wed Oct 21 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-3
- remove executable flag from various files that shouldn't have it
- fix end-of-line encodings
- fix a character encoding

* Tue Oct 20 2009 David Malcolm <dmalcolm@redhat.com> - 3.1.1-2
- disable invocation of brp-python-bytecompile in postprocessing, since
it would be with the wrong version of python (adapted from ivazquez'
python3000 specfile)
- use a custom implementation of __find_provides in order to filter out bogus
provides lines for the various .so modules
- fixup distutils/unixccompiler.py to remove standard library path from rpath
(patch 1, was Patch0 in ivazquez' python3000 specfile)
- split out libraries into a -libs subpackage
- update summaries and descriptions, basing content on ivazquez' specfile
- fixup executable permissions on .py, .xpm and .xbm files, based on work in
ivazquez's specfile
- get rid of DOS batch files
- fixup permissions for shared libraries from non-standard 555 to standard 755
- move /usr/bin/python*-config to the -devel subpackage
- mark various directories as being documentation

* Thu Sep 24 2009 Andrew McNabb <amcnabb@mcnabbs.org> 3.1.1-1
- Initial package for Python 3.

