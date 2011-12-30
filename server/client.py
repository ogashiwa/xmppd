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
        self.cntrmsg = 0
        self.cntsmsg = 0
        self.username = ""
        self.barejid = ""
        self.fulljid = ""
        self.resource = ""
        self.stream = stream
        self.stream.CBF_recv = self.recv
        self.authman = xmpp.auth.manager(self.manager.servname, self.send, self.pwfunc)
        self.tmping = int(time.time())
        self.tmrmsg = int(time.time())
        self.ptype = ''
        self.pstat = ''
        self.pshow = ''
        self.send(msgout.featmech())
        pass

    def print(self):
        l = "|{JID:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|{PT:>10}|{PS:>10}|{PH:>10}|"
        tp = int(time.time())-self.tmping
        tr = int(time.time())-self.tmrmsg
        l = l.format(JID=self.fulljid, CRM=self.cntrmsg, CSM=self.cntsmsg,
                     TP=tp,TR=tr,PT=self.ptype,PS=self.pstat,PH=self.pshow)
        print(l)
        #print(self.username,
        #      self.barejid,
        #      self.fulljid,
        #      self.resource,
        #      self.cntrmsg,
        #      self.cntsmsg,
        #      (int(time.time())-self.tmping),
        #      (int(time.time())-self.tmrmsg),
        #      '"'+self.ptype+'"',
        #      '"'+self.pstat+'"',
        #      '"'+self.pshow+'"')
        pass
    
    def send(self,m):
        self.cntsmsg += 1
        self.stream.send(m)
        pass

    def checkauth(self, m):
        if self.authman.authenticated == False:
            self.authman.proc(m)
            return False
        if self.username == "":
            self.username = self.authman.username
            self.barejid = self.username + "@" + self.manager.servname
            self.fulljid = self.barejid
            self.name = self.fulljid
            pass        
        return True
    
    def recv(self,stream,m):
        
        self.tmrmsg = int(time.time())
        self.cntrmsg += 1
        
        # if not yet authorized
        if self.checkauth(m) == False: return

        # get message type
        mt = msgin.getmsgtype(m)
        
        # process stream header
        if mt == ns.TAG_STST:
            sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_CLIENT)
            self.authman.sendsthdr = sendsthdr
            self.authman.recvsthdr = m
            self.send(sendsthdr)
            self.send(msgout.featbs())
            return
        
        # forward the message if needed
        mto = msgin.getmsgto(m)
        mfrom = msgin.getmsgfrom(m)
        (uname, sname, rname) = msgin.splitjid(mto)
        print((uname, sname, rname))
        if sname != '' and sname != self.manager.servname: #forward msg to other server
            self.manager.svssmanager.sendqueue.put((mfrom,mto,m))
            self.manager.svssmanager.flush()
            return
        tome = False
        if len(mto) == 0: tome = True
        if mto == self.manager.servname: tome = True
        if tome == False:
            targ = []
            targ = self.manager.sessmanager.getforwardsess(mto)
            for ses in targ:
                xmpp.utils.dprint("!!! FORWARD TO "+ses.name)
                m = msgout.addfrom(m, self.name)
                ses.send(m)
                pass
            return

        if mt == ns.TAG_PRES:
            p = msgin.presence(m)
            self.ptype = p.type
            self.pstat = p.status
            self.pshow = p.show
            if self.ptype == 'unavailable': return
            rlkeys = self.manager.confmanager.rosterlist.keys()
            
            for kv in rlkeys:
                if kv[0] != self.username: continue
                targ = self.manager.sessmanager.getclientsess(kv[1])
                for ses in targ:
                    ses.send(msgout.presence(self.barejid,kv[1],
                                             p.type, p.status,p.show))
                    pass
                pass
            
            for kv in rlkeys:
                if kv[1] != self.barejid: continue
                targ = self.manager.sessmanager.getclientsess(kv[0]+"@"+self.manager.servname)
                for ses in targ:
                    self.send(msgout.presence(ses.barejid,
                                              self.barejid,
                                              ses.ptype,
                                              ses.pstat,
                                              ses.pshow))
                    pass
                pass
            
            pass
        
        if mt == ns.TAG_IQ:
            p = msgin.iq(m)
            
            if p.iqtype == ns.IQTYPE_SET and p.xmlns == ns.XMPP_BIND:
                self.resource = p.resource
                self.fulljid = self.barejid + "/" + self.resource
                self.name = self.fulljid
                self.send(msgout.bindres(self.barejid,p.msgid))
                pass
            
            elif p.iqtype == ns.IQTYPE_GET and p.xmlns == ns.JABBER_ROSTER:
                rlkeys = self.manager.confmanager.rosterlist.keys()
                tmproslist = {}
                for kv in rlkeys:
                    if kv[0] != self.username: continue
                    tmproslist[kv[1]] = self.manager.confmanager.rosterlist[kv]
                    pass
                self.send(msgout.rosterres(p.msgid,self.manager.servname,
                                                  self.fulljid, tmproslist))
                pass
            
            elif p.iqtype == ns.IQTYPE_GET and p.xmlns == ns.HTTP_DITEMS:
                itemslist = []
                for nm in self.manager.sessmanager.compntlist:
                    itemslist.append(nm.name)
                    pass
                self.send(msgout.ditems(p.msgid,p.msgto, self.fulljid,itemslist))
                pass
            
            elif p.iqtype == ns.IQTYPE_SET:
                self.send(msgout.bindres(self.barejid,p.msgid))
                pass
            
            elif p.iqtype != ns.IQTYPE_RESULT:
                self.send(msgout.iqres(p.msgid))
                pass
            
            return
        pass
    
    def pwfunc(self, u):
        return self.manager.confmanager.userlist[u]
    
    pass
