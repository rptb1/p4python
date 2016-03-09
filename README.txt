========
P4Python
========

:Author: Richard Brooksby <rb@ravenbrook.com>
:Organization: Ravenbrook Limited <http://www.ravenbrook.com/>

.. note::

    This repository is obsolete.  Perforce Software support pip
    installation themselves starting at version 2016.1.  Just try::

        pip install p4python

    Thank you, Perforce!

This is P4Python, the Python interface to the Perforce API , enables you
to write Python code that interacts with a Perforce server.  For details,
see the P4Python chapter of the Perforce scripting manual
<http://www.perforce.com/perforce/doc.current/manuals/p4script/03_python.html>.

Please see RELNOTES.txt for hints how to build and use P4Python and for a 
list of changes.

This is a fork of P4Python by Richard Brooksby of Ravenbrook Limited,
with the goal of making a command like::

    pip install p4python

work smoothly, quickly, and without manual intervention.  This should
make it much easier for people to develop Python apps that use Perforce.

The P4Python distributed by Perforce Software relies on the user
manually fetching the Perforce C/C++ API (P4API).  In addition, on some
platforms (such as Mac OS X 8) the user must fetch, configure, and build
dependent packages such as OpenSSL 1.0.1.  All of this hinders development
and distribution of Python packages using Perforce.

So far, this fork includes a script ``p4apiget.py`` that attempts to fetch
a relevant version of the Perforce API from Perforce Software's FTP server.
This is called from ``setup.py`` if the user didn't specify a directory
containing the API.

Open issues:

1. p4apiget.py may not guess the right place to get P4API on all
   supported platforms.

2. Nothing has been done to fetch libraries that P4API depends on, such as
   OpenSSL 1.0.1.
