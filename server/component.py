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

class session():

    def __init__(self, stream, manager):
        self.name = ''
        self.manager = manager
        self.stream = stream
        self.cntsmsg = 0
        self.cntrmsg = 0
        self.tmping = int(time.time())
        self.tmrmsg = int(time.time())
        self.stream.CBF_recv = self.recv
        pass

    def print(self):
        l = "|{NAME:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|"
        tp = int(time.time())-self.tmping
        tr = int(time.time())-self.tmrmsg
        l = l.format(NAME=self.name, CRM=self.cntrmsg, CSM=self.cntsmsg, TP=tp,TR=tr)
        print(l)
        #print(self.name,
        #      self.cntrmsg,
        #      self.cntsmsg,
        #      (int(time.time())-self.tmping),
        #      (int(time.time())-self.tmrmsg))
        pass
    
    def recv(self,stream,m):
        
        self.tmrmsg = int(time.time())
        self.cntrmsg += 1

        # forward the message if needed
        mto = msgin.getmsgto(m)

        tome = False
        if len(mto) == 0: tome = True
        if mto == self.manager.servname: tome = True
        if tome == False:
            targ = []
            targ = self.manager.sessmanager.getforwardsess(mto)
            for ses in targ:
                ses.send(m)
                pass
            return
        
        mt = msgin.getmsgtype(m)
        
        # proc msg
        if mt == "handshake":
            p = msgin.hshake(m)
            # check component key
            authok = False
            for (k,v) in self.manager.confmanager.cmpntlist.items():
                if (k,v) == (self.name,p.key):
                    authok = True
                    pass
                pass

            if authok == False:
                self.stream.close()
                return
            pass
        pass
    
    def send(self,m):
        self.cntsmsg += 1
        self.stream.send(m)
        pass
    
    pass
