#!/usr/bin/env python
#
# Fetch and install the Perforce API from Perforce Software.
#
# Modified by Richard Brooksby <rb@ravenbrook.com> from
# <http://reviewboard.googlecode.com/svn/trunk/P4PythonInstaller/>
# which is stated at <https://pypi.python.org/pypi/P4PythonInstaller/0.2>
# and at <https://code.google.com/p/reviewboard/>
# to be under the MIT License <http://opensource.org/licenses/MIT>.


import copy
import ftplib
import os
import os.path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


p4api_version = "13.1"

perforce_hostname = "ftp.perforce.com"
perforce_path = "/perforce/r%s" % p4api_version
p4python_path = "%s/bin.tools" % perforce_path


def download(paths, path = '.'):
    """
    Downloads files from the Perforce FTP server.
    """
    ftp = ftplib.FTP(perforce_hostname)
    ftp.login()

    for remote_path in paths:
        filename = remote_path.rsplit("/", 1)[1]
        print "Downloading %s..." % filename
        ftp.retrbinary("RETR %s" % remote_path,
                       open(os.path.join(path, filename), "wb").write)

    ftp.quit()


def extract(filename, path = '.'):
    """
    Extracts a tarball into the current directory, and returns the directory
    name where the files were extracted.
    """
    print "Extracting %s..." % filename
    tar = tarfile.open(filename, "r:gz")
    dirname = tar.getnames()[0].rstrip("/")

    if hasattr(tar, "extractall"):
        tar.extractall(path = path)
    else:
        # Simulate extractall

        directories = []

        for tarinfo in tar:
            if tarinfo.isdir():
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0700

            tar.extract(tarinfo, path = path)

        directories.sort(lambda a, b: cmp(a.name, b.name))
        directories.reverse()

        # Set correct owner, mtime and filemode on directories.
        for tarinfo in directories:
            dirpath = os.path.join(path, tarinfo.name)

            try:
                tar.chown(tarinfo, dirpath)
                tar.utime(tarinfo, dirpath)
                tar.chmod(tarinfo, dirpath)
            except ExtractError, e:
                if self.errorlevel > 1:
                    raise
                else:
                    print e

    tar.close()

    return os.path.join(path, dirname)


def get_p4api_path():
    """
    Returns the p4api.tgz download path, based on the platform information.
    """
    arch = platform.machine()

    if re.match("i\d86", arch):
        arch = "x86"
    elif arch in ("x86_64", "amd64"):
        arch = "x86_64"
    else:
        sys.stderr.write("Unsupported system architecture: %s\n" % arch)
        sys.exit(1)

    osname = platform.system()

    if osname == "Linux":
        linuxver = platform.release()
        if linuxver.startswith('2.6') or linuxver.startswith('3.'):
            osname = "linux26"
        elif linuxver.startswith("2.4"):
            osname = "linux24"
        else:
            sys.stderr.write("Unsupported Linux version: %s" % linuxver)
            sys.exit(1)
    elif osname == "Windows":
        # TODO: Download and run the Windows installer.
        print "Download the Windows installer at:"
        print "http://public.perforce.com/guest/robert_cowham/perforce/API/python/index.html"
        sys.exit(1)
    elif osname == "Darwin":
        osname = 'macosx105'
    elif osname == "FreeBSD":
        osname = "freebsd"
        freebsd_ver = platform.release()
        freebsd_major = int(freebsd_ver.split(".")[0])

        if freebsd_major == 5:
            osname += "54"
        elif freebsd_major >= 6:
            osname += "60"
        else:
            sys.stderr.write("Unsupported FreeBSD version: %s" % freebsd_ver)
            sys.exit(1)
    else:
        # TODO: Should support Solaris/OpenSolaris
        sys.stderr.write("Unsupported operating system: %s" % osname)
        sys.exit(1)

    return "%s/bin.%s%s" % (perforce_path, osname, arch)


def get_p4api():
    tmpdir = tempfile.mkdtemp()
    remote_path = "%s/p4api.tgz" % get_p4api_path()
    download([remote_path], path = tmpdir)
    local_path = os.path.join(tmpdir, "p4api.tgz")
    p4api_dir = os.path.abspath(extract(local_path, path = tmpdir))
    return p4api_dir


def main():
    p4api_path = get_p4api_path()
    download(["%s/p4api.tgz" % p4api_path])

    curdir = os.getcwd()

    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)

    download(["%s/p4api.tgz" % p4api_path,
              "%s/p4python.tgz" % p4python_path])

    p4api_dir = os.path.abspath(extract("p4api.tgz"))
    p4python_dir = extract("p4python.tgz")

    os.chdir(p4python_dir)

    # Generate the setup.cfg file.
    fp = open("setup.cfg", "w")
    fp.write("[p4python_config]\n")
    fp.write("p4_api=%s" % p4api_dir)
    fp.close()

    args = []

#    for arg in sys.argv[1:]:
#        if arg.startswith("bdist"):
#            args.append("install")
#        elif arg.
#        else:
#            args.append(arg)

    p = subprocess.Popen([sys.executable, "setup.py", "install"])
    rc = p.wait()

    os.chdir(curdir)

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()
