fosm-fix-missing-nodes
======================

Small python script to fix ways with missing nodes in the fosm database. Either a specific way can be fixed or an osm file can be opened and checked for broken ways. Tested on python 2.7. A fosm account is required to make database changes. The script checks the latest version of the way in the database to ensure corrections are not applied twice.

pycurl must be installed (I think)

Examples:

<pre>Check a way:      python fixmissingnodes.py 55511190
Check a file:     python fixmissingnodes.py --file wiltboat.osm
Check a relation: python fixmissingnodes.py --relation 20469
Check many files: python fixmissingnodes.py --path /path/to/files</pre>

To check a way without being prompted for username and password:

<pre>python fixmissingnodes.py 55511190 --cred ~/Desktop/user.txt</pre>

user.txt has username as first line and the password as the second line.

Copying
=======

Copyright (c) 2014, Tim Sheerman-Chase
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
