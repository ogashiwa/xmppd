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
import xmpp
import xmpp.ns as ns
import xmpp.msg as msg
import xmpp.msgin as msgin
import xmpp.msgout as msgout
import server.client, server.component, server.server
import xml
import queue
import subprocess

class svssmanager:
    
    def __init__(self, manager):
        self.manager = manager
        self.peersvlist = []
        self.sendqueue = queue.Queue()
        pass

    def flush(self):
        
        (mfr,mto,msg) = self.sendqueue.get()
        (ju,jh,jr) = msgin.splitjid(mto)
        
        # search peer-connection by mto(jh)
        for ps in self.peersvlist:
            if ps.mto == jh and ps.stat=='ready':
                x = xmpp.msg.xmsg(ps.m_sendsthdr)
                x.fromstring(msg)
                x.e.attrib['from'] = mfr
                ps.stream.send(x.tostring())
                return
            elif ps.mto == jh and ps.stat!='ready':
                self.sendqueue.put((mfr,mto,msg))
                return
            pass
        
        # get SRV record
        domain = jh
        host = self.srvrec(domain)
        
        # connect to server
        print("### connect to " + host + " as master of " + domain)
        self.connect(domain, host, 5269)
        
        self.sendqueue.put((mfr,mto,msg))
        pass
    
    def srvrec(self,domain):
        m = subprocess.check_output(['/usr/bin/host', '-t', 'SRV', '_xmpp-server._tcp.'+domain])
        m = m.decode('utf-8')
        lm = m.splitlines()
        svlist=[]
        for l in lm:
            r = re.search(r'(?ms).*SRV record (.+) (.+) (.+) (.+)\.[\r\n]*', l)
            (prio,weig,port,host) = (int(r.group(1)),int(r.group(2)),
                                     int(r.group(3)),r.group(4))
            svlist.append((host,port,prio,weig))
            pass
        minsv = ''
        for s in svlist:
            if minsv == '': minsv = s
            if minsv[2] > s[2]: minsv = s
            pass
        minsv = minsv[0]
        return minsv
                                                            
    def closed(self,st,m):
        for sess in self.peersvlist:
            if sess.stream is st: self.peersvlist.remove(sess)
            pass
        pass

    def connect(self,domain,serv,port):
        st = xmpp.stream.stream()
        ss = server.server.servsess()
        ss.manager = self.manager
        ss.mfrom = self.manager.servname
        ss.mto = domain
        ss.stream = st
        st.CBF_recv = ss.recv
        st.CBF_closed = self.closed
        st.connect(serv,port)
        st.start()
        ss.m_sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_SERVER, msgid='no', xmlnsdb='yes')
        st.send(ss.m_sendsthdr)
        ss.sendsthdr = True
        ss.reqsendkey = True
        self.peersvlist.append(ss)
        pass
    
    def closed(self,st,m):
        for sess in self.peersvlist:
            if sess.stream is st: self.peersvlist.remove(sess)
            pass
        pass

    def addsocket(self,s):
        st = xmpp.stream.stream()
        ss = server.server.servsess()
        ss.manager = self.manager
        ss.mfrom = self.manager.servname
        ss.stream = st
        st.CBF_recv = ss.recv
        st.CBF_closed = self.closed
        st.socket = s
        ss.m_sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_SERVER, xmlnsdb='yes')
        st.send(ss.m_sendsthdr+'<stream:features><dialback xmlns="urn:xmpp:features:dialback"><optional/></dialback></stream:features>')
        ss.sendsthdr = True
        ss.sendfeat = True
        st.start()
        self.peersvlist.append(ss)
        pass
    pass

class sessmanager:

    def __init__(self, manager):
        self.manager = manager
        self.tcpconlist = []
        self.clientlist = []
        self.compntlist = []
        pass
    
    def getclientsess(self, jid):
        retlist = []
        for cs in self.clientlist:
            if cs.barejid == jid or cs.fulljid == jid:
                retlist.append(cs)
                pass
            pass
        return retlist
    
    def getcompntsess(self, to):
        retlist = []
        for cm in self.compntlist:
            if cm.name == to or to.find("@"+cm.name) != -1:
                retlist.append(cm)
                pass
            pass
        return retlist

    def getforwardsess(self,msgto):
        retlist = []
        if msgto.find("@"):
            # if after '@' is me, find client-list
            if msgto.find("@"+self.manager.servname):
                retlist.extend(self.getclientsess(msgto))
                pass
            # if after '@' is my components, find component-list
            retlist.extend(self.getcompntsess(msgto))
            # if after '@' is unknown, other servers
            pass
        else:
            # if '@' doesn't exist, find component-list
            retlist.extend(self.getcompntsess(msgto))
            pass
        return retlist
    
    def recvsthdr(self, stream, m):
        sthdr = msgin.sthdr(m)
        if sthdr.attrs[ns.XMLNS] == ns.JABBER_CLIENT:
            stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CLIENT))
            cs = server.client.session(stream,self.manager)
            self.clientlist.append(cs)
            while stream in self.tcpconlist: self.tcpconlist.remove(stream)
            pass
        elif sthdr.attrs[ns.XMLNS] == ns.JABBER_CMPNT:
            stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CMPNT))
            cm = server.component.session(stream, self.manager)
            cm.name = sthdr.attrs['from']
            self.compntlist.append(cm)
            while stream in self.tcpconlist: self.tcpconlist.remove(stream)
            pass
        pass
    
    def timercheck(self):
        for cs in self.clientlist:
            if cs.tmping+60<int(time.time()):
                cs.send(msgout.ping(self.manager.servname,cs.fulljid))
                cs.tmping = int(time.time())
                pass
            if cs.tmrmsg+180<int(time.time()):
                cs.stream.close()
                pass
            pass
        for cm in self.compntlist:
            if cm.tmping+60<int(time.time()):
                cm.send(msgout.ping(self.manager.servname,cm.name))
                cm.tmping = int(time.time())
                pass
            if cm.tmrmsg+180<int(time.time()):
                cm.stream.close()
                pass
            pass
        pass
    
    def closed(self,st,m):
        while st in self.tcpconlist: self.tcpconlist.remove(st)
        for sess in self.clientlist:
            if sess.stream is st: self.clientlist.remove(sess)
            pass
        for sess in self.compntlist:
            if sess.stream is st: self.compntlist.remove(sess)
            pass
        pass

    def addsocket(self,s):
        st = xmpp.stream.stream()
        st.CBF_recv = self.recvsthdr
        st.CBF_closed = self.closed
        st.socket = s
        st.start()
        self.tcpconlist.append(st)
        pass
    
    def print(self):
        xmpp.utils.print_clear()
        print("=====================")
        print("clients:")
        l = "|{JID:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|{PT:>10}|{PS:>10}|{PH:>10}|"
        l = l.format(JID="JID",CRM="#recv",CSM="#send",TP="ping",TR="last",
                     PT="ptype", PS="pstat", PH="pshow")
        print(l)
        for s in self.clientlist:
            s.print()
            pass
        print("=====================")
        print("components:")
        l = "|{NAME:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|"
        l = l.format(NAME="name",CRM="#recv",CSM="#send",TP="ping",TR="last")
        print(l)
        for s in self.compntlist:
            s.print()
            pass
        pass
    pass

class confmanager:

    def __init__(self, manager):
        self.manager = manager
        self.userlist = {}
        self.rosterlist = {}
        self.cmpntlist = {}
        self.cbindport4 = 5222
        self.cbindport6 = 5222
        self.cbindaddr4 = '0.0.0.0'
        self.cbindaddr6 = '::'
        self.sbindport4 = 5269
        self.sbindport6 = 5269
        self.sbindaddr4 = '0.0.0.0'
        self.sbindaddr6 = '::'
        self.servname = ''
        pass
    
    def read(self, fname):
        f = open(fname, 'r')
        for line in f:
            if line.find('#') != None: line = line[:line.find("#")]
            r = re.search(r'(?ms)([^ \t]+)[ \t]+([^\r\n]+).*',line)
            if r is None: continue
            n = r.group(1)
            v = r.group(2)
            
            if n == 'User':
                r = re.search(r'(?ms)([^ \t]+)[ \t]+([^ \t\r\n]+).*',v)
                self.userlist[r.group(1)] = r.group(2)
                pass
            elif n == 'Component':
                r = re.search(r'(?ms)([^ \t]+)[ \t]+([^ \t\r\n]+).*',v)
                self.cmpntlist[r.group(1)] = r.group(2)
                pass
            elif n == 'Roster':
                r = re.search(r"(?ms)([^ \t]+)[ \t]+([^ \t]+)" + 
                              "[ \t]+([^ \t]+)[ \t]+([^ \t\r\n]+).*",v)
                self.rosterlist[(r.group(1),r.group(2))] = (r.group(3),r.group(4))
                pass
            elif n == 'BindAddress4':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                self.cbindaddr4 = r.group(1)
                pass
            elif n == 'ClientListenPort4':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                self.cbindport4 = r.group(1)
                pass
            elif n == 'BindAddress6':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                self.cbindaddr6 = r.group(1)
                pass
            elif n == 'ClientListenPort6':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                self.cbindport6 = r.group(1)
                pass
            elif n == 'ServerName':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                self.servname = r.group(1)
                pass
            elif n == 'Debug':
                r = re.search(r'(?ms)([^ \t\r\n]+).*',v)
                if r.group(1) == 'yes': xmpp.utils.debug(True)
                pass
            pass
        
        f.close()
        pass
    
    pass

class serversocket(threading.Thread):
    
    def __init__(self, bindaddr, port):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sfamily = socket.AF_INET
        self.sstream = socket.SOCK_STREAM
        self.bindaddr = bindaddr
        self.port = port
        self.accepted = None
        pass
    
    def run(self):
        try:
            s = socket.socket(self.sfamily, self.sstream)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.bindaddr, self.port))
            s.listen(5)
            while True:
                (peersock, peeraddr) = s.accept()
                if self.accepted: self.accepted(peersock, peeraddr)
                pass
            pass
        except: print("Unexpected error:", sys.exc_info())
        pass
    pass


class manager:
    
    def __init__(self):
        
        self.conffile = ''
        self.servname = ''
        self.confmanager = confmanager(self)
        self.sessmanager = sessmanager(self)
        self.svssmanager = svssmanager(self)
        
        pass
    
    def accept(self, ps,pa):
        self.sessmanager.addsocket(ps)
        pass
    
    def s2saccept(self, ps, pa):
        print("def s2saccept(self, ps, pa):")
        self.svssmanager.addsocket(ps)
        pass
    
    def start(self):
        
        self.confmanager.read(self.conffile)
        self.servname = self.confmanager.servname
        
        BindAddress4 = '0.0.0.0'
        s4 = serversocket(BindAddress4, int(self.confmanager.cbindport4))
        s4.sfamily = socket.AF_INET
        s4.sstream = socket.SOCK_STREAM
        s4.accepted = self.accept
        s4.start()
        
        BindAddress6 = '::'
        s6 = serversocket(BindAddress6, int(self.confmanager.cbindport6))
        s6.sfamily = socket.AF_INET6
        s6.sstream = socket.SOCK_STREAM
        s6.accepted = self.accept
        s6.start()
        
        ss4 = serversocket("0.0.0.0", 5269)
        ss4.accepted = self.s2saccept
        ss4.start()
        
        while True:
            self.sessmanager.timercheck()
            self.sessmanager.print()
            print("\n")
            time.sleep(1)
            pass
        
        pass
    
    pass
