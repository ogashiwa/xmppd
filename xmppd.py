#!/usr/local/bin/python3.2

# Copyright (c) 2011, Nobuo Ogashiwa <ogashiwa@wide.ad.jp>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of the <organization> nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import sys, socket, threading, time, getopt, re
import xmpp.stream, xmpp.msgin, xmpp.msgout, xmpp.auth, xmpp.utils
import xmpp.ns as ns
import xmpp.msgin as msgin
import xmpp.msgout as msgout
import server.manager
#import os
#from os import fork, chdir, setsid, umask
#from sys import exit

def usage(): print("xmppd [-c <FILENAME>|--config-file=<FILENAME>] "
                   "[-h|--help] [-v|--version]")

#def daemonize():
#    try:
#        pid = fork()
#        if pid > 0: exit(0)
#        pass
#    except:
#        exit(1)
#        pass
#    chdir("/")
#    setsid()
#    umask(0)
#    try:
#        pid = fork()
#        if pid > 0:
#            exit(0)
#            pass
#        pass
#    except:
#        exit(1)
#        pass
#    
#    import resource
#    MAXFD = 1024
#    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
#    if (maxfd == resource.RLIM_INFINITY):
#        maxfd = MAXFD
#        pass
#    for fd in range(0, maxfd):
#        try:
#            os.close(fd)
#        except OSError:	# ERROR, fd wasn't open to begin with (ignored)
#            pass
#        pass
#    os.open(REDIRECT_TO, os.O_RDWR)	# standard input (0)
#    os.dup2(0, 1)			# standard output (1)
#    os.dup2(0, 2)			# standard error (2)
#    pass

def main():
    xmpp.utils.debug(False)
    conffile = "xmppd.conf"
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "c:hvdD",
                                   ["config-file=", "help", "version",
                                    "daemonize", "debug"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        pass
    
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
            pass
        if o in ("-v", "--version"):
            print("xmppd: version 0.0.7")
            sys.exit()
            pass
        if o in ("-D", "--debug"):
            xmpp.utils.debug(True)
            pass
        if o in ("-d", "--daemonize"):
            daemonize()
            pass
        if o in ("-c", "--config-file"):
            conffile = a
            pass
        pass

    
    
    try:
        m = server.manager.manager()
        m.conffile = conffile
        m.start()
        
    except: print("Unexpected error:", sys.exc_info())
    pass

if __name__ == "__main__":
    main()
    pass
