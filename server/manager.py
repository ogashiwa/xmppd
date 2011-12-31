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

#import datetime
#import sys, socket, threading, time, getopt, re
#import xmpp.stream, xmpp.msgin, xmpp.msgout, xmpp.auth, xmpp.utils
#import xmpp
#import xmpp.ns as ns
#import xmpp.msg as msg
#
#import xmpp.msgout as msgout
#
#import server.client, server.component, server.server
#import xml
#import queue

import threading, re, socket, time, subprocess
import xmpp, xmpp.stream, xmpp.auth
import xmpp.msgin as msgin
import xmpp.utils as utils
from xmpp.msg import xmsg as xm

#class svssmanager:
#    
#    def __init__(self, manager):
#        self.manager = manager
#        self.peersvlist = []
#        self.sendqueue = queue.Queue()
#        pass
#
#    def flush(self):
#        
#        (mfr,mto,msg) = self.sendqueue.get()
#        (ju,jh,jr) = msgin.splitjid(mto)
#        
#        # search peer-connection by mto(jh)
#        for ps in self.peersvlist:
#            if ps.mto == jh and ps.stat=='ready':
#                x = xmpp.msg.xmsg(ps.m_sendsthdr)
#                x.fromstring(msg)
#                x.e.attrib['from'] = mfr
#                ps.stream.send(x.tostring())
#                return
#            elif ps.mto == jh and ps.stat!='ready':
#                self.sendqueue.put((mfr,mto,msg))
#                return
#            pass
#        
#        # get SRV record
#        domain = jh
#        host = self.srvrec(domain)
#        
#        # connect to server
#        print("### connect to " + host + " as master of " + domain)
#        self.connect(domain, host, 5269)
#        
#        self.sendqueue.put((mfr,mto,msg))
#        pass
#    
#    def srvrec(self,domain):
#        m = subprocess.check_output(['/usr/bin/host', '-t', 'SRV', '_xmpp-server._tcp.'+domain])
#        m = m.decode('utf-8')
#        lm = m.splitlines()
#        svlist=[]
#        for l in lm:
#            r = re.search(r'(?ms).*SRV record (.+) (.+) (.+) (.+)\.[\r\n]*', l)
#            (prio,weig,port,host) = (int(r.group(1)),int(r.group(2)),
#                                     int(r.group(3)),r.group(4))
#            svlist.append((host,port,prio,weig))
#            pass
#        minsv = ''
#        for s in svlist:
#            if minsv == '': minsv = s
#            if minsv[2] > s[2]: minsv = s
#            pass
#        minsv = minsv[0]
#        return minsv
#                                                            
#    def closed(self,st,m):
#        for sess in self.peersvlist:
#            if sess.stream is st: self.peersvlist.remove(sess)
#            pass
#        pass
#
#    def connect(self,domain,serv,port):
#        st = xmpp.stream.stream()
#        ss = server.server.servsess()
#        ss.manager = self.manager
#        ss.mfrom = self.manager.servname
#        ss.mto = domain
#        ss.stream = st
#        st.CBF_recv = ss.recv
#        st.CBF_closed = self.closed
#        st.connect(serv,port)
#        st.start()
#        ss.m_sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_SERVER, msgid='no', xmlnsdb='yes')
#        st.send(ss.m_sendsthdr)
#        ss.sendsthdr = True
#        ss.reqsendkey = True
#        self.peersvlist.append(ss)
#        pass
#    
#    def closed(self,st,m):
#        for sess in self.peersvlist:
#            if sess.stream is st: self.peersvlist.remove(sess)
#            pass
#        pass
#
#    def addsocket(self,s):
#        st = xmpp.stream.stream()
#        ss = server.server.servsess()
#        ss.manager = self.manager
#        ss.mfrom = self.manager.servname
#        ss.stream = st
#        st.CBF_recv = ss.recv
#        st.CBF_closed = self.closed
#        st.socket = s
#        ss.m_sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_SERVER, xmlnsdb='yes')
#        st.send(ss.m_sendsthdr+'<stream:features><dialback xmlns="urn:xmpp:features:dialback"><optional/></dialback></stream:features>')
#        ss.sendsthdr = True
#        ss.sendfeat = True
#        st.start()
#        self.peersvlist.append(ss)
#        pass
#    pass

class session:
    
    def __init__(self):
        self.manager = None
        self.authman = None
        self.peername = ''
        self.username = ''
        self.resource = ''
        self.Type = ''
        self.SentHeader = ''
        self.RcvdHeader = ''
        self.stream = None
        self.TmPing = int(time.time())
        self.TmRmsg = int(time.time())
        self.CntSMsg = 0
        self.CntRMsg = 0
        pass

    def fulljid(self):
        return self.username + "@" + self.manager.servname + "/" + self.resource
    
    def barejid(self):
        return self.username + "@" + self.manager.servname

    def ident(self):
        if self.Type=='Client': return self.fulljid()
        if self.Type=='Component': return self.peername
        if self.Type=='Server': return self.peername
        return ''
    
    def authenticated(self,result):
        if result == True:
            self.username = self.authman.username
            self.RcvdHeader = ''
            utils.dprint("# Authenticated ")
            utils.dprint("# UserName: {U} ".format(U=self.username))
            utils.dprint("# Reset Stream ")
            pass
        else:
            utils.dprint("# Authentication failed ")
            utils.dprint("# Reset Stream ")
            self.stream.close()
            pass
        pass
    
    def pwfunc(self, u):
        return self.manager.confmanager.userlist[u]
    
    def send(self,m):
        self.CntSMsg += 1
        self.stream.send(m)
        pass
    
    def recv(self, stream, m):
        
        self.CntRMsg += 1
        self.TmRmsg = int(time.time())
        
        x = xm(self.RcvdHeader)
        x.fromstring(m)
        
        if x.e.tag=='{http://etherx.jabber.org/streams}stream':
            
            self.RcvdHeader = m
            nx = xm(self.SentHeader)
            a = {'xmlns:stream':'http://etherx.jabber.org/streams',
                 'xmlns:xml':"http://www.w3.org/XML/1998/namespace",
                 'version':'1.0',
                 'from':self.manager.servname}
            
            if m.find('jabber:client')>0:
                self.Type='Client'
                a['xmlns'] = 'jabber:client'
                nx.create(tag='stream:stream', attrib=a)
                self.SentHeader = ''
                pass
            
            elif m.find('jabber:component:accept')>0:
                self.Type='Component'
                a['xmlns'] = 'jabber:component:accept'
                a['id'] = utils.randstr(8)
                nx.create(tag='stream:stream', attrib=a)
                pass
            
            elif m.find('jabber:server')>0:
                self.Type='Server'
                a['xmlns'] = 'jabber:server'
                self.peername = x.e.attrib['from']
                nx.create(tag='stream:stream', attrib=a)
                pass
            
            else:
                stream.close()
                return

            if self.SentHeader=='':
                self.SentHeader = nx.tostring()
                self.send(self.SentHeader)
                pass
            
            if self.Type=='Client':
                mec = xm(self.SentHeader)
                mec.create(tag='mechanisms',attrib={'xmlns':'urn:ietf:params:xml:ns:xmpp-sasl'},
                           sub=[xm(self.SentHeader,tag='mechanism',text='PLAIN'),
                                xm(self.SentHeader,tag='mechanism',text='DIGEST-MD5'),
                                xm(self.SentHeader,tag='required')])
                bid = xm(self.SentHeader)
                bid.create(tag='bind',attrib={'xmlns':'urn:ietf:params:xml:ns:xmpp-bind'},
                           sub=[xm(self.SentHeader,tag='required')])
                stg = xm(self.SentHeader)
                stg.create(tag='session',attrib={'xmlns':'urn:ietf:params:xml:ns:xmpp-session'},
                           sub=[xm(self.SentHeader,tag='optional')])
                nx = xm(self.SentHeader)
                subtag=[]
                if self.username == '': subtag=[mec]
                else: subtag=[bid,stg]
                nx.create(tag='stream:features', sub=subtag)
                self.send(nx.tostring())
                pass

            if self.Type=='Component':
                self.peername = x.e.attrib['from']
                pass
            
            return
        
        print(x.e.tag)
        if 'to' in x.e.attrib:
            print(x.e.attrib['to'])
            (uname, sname, rname) = msgin.splitjid(x.e.attrib['to'])
            print((uname, sname, rname))
            for sess in self.manager.sessmanager.sessionlist:
                fw = False
                if x.e.attrib['to']==sess.ident(): fw = True
                elif x.e.attrib['to']==sess.barejid(): fw = True
                elif sname==sess.ident(): fw = True
                if fw==True:
                    if ('from' in x.e.attrib)==False: x.e.attrib['from']=self.ident()
                    sess.send(x.tostring())
                    return
                pass
            if sname!=self.manager.servname:
                self.manager.sessmanager.pendingmsg.append((self,m,int(time.time()),'init'))
                return
            pass
        
        if self.Type=='Client':
            
            if x.e.tag=='{urn:ietf:params:xml:ns:xmpp-sasl}auth' or \
                   x.e.tag=='{urn:ietf:params:xml:ns:xmpp-sasl}response':
                if self.authman == None:
                    self.authman = xmpp.auth.manager(self.manager.servname, self.send,
                                                     self.pwfunc, self.authenticated)
                    (self.authman.sendsthdr,self.authman.recvsthdr) = (self.SentHeader,self.RcvdHeader)
                    pass
                if self.authman.authenticated == False:
                    self.authman.proc(m)
                    return
                return
            
            if x.e.tag=='{jabber:client}iq':
                
                ResourceTag='{NS}bind/{NS}resource'.format(NS='{urn:ietf:params:xml:ns:xmpp-bind}')
                ResourceStz = x.e.find(ResourceTag)
                if ResourceStz!=None:
                    self.resource = ResourceStz.text
                    utils.dprint("# Client Resource is " + self.resource)
                    nx = xm(self.SentHeader)
                    nx.create(tag='iq',
                              attrib={'id':x.e.attrib['id'],'type':'result'},
                              sub=[xm(self.SentHeader,tag='bind',
                                      attrib={'xmlns':'urn:ietf:params:xml:ns:xmpp-bind'},
                                      sub=[xm(self.SentHeader,tag='jid',
                                              text=self.fulljid())])])
                    self.send(nx.tostring())
                    return
                
                SessionTag='{NS}session'.format(NS='{urn:ietf:params:xml:ns:xmpp-session}')
                SessionStz = x.e.find(SessionTag)
                if SessionStz!=None:
                    nx = xm(self.SentHeader,tag='iq',
                            attrib={'id':x.e.attrib['id'],'type':'result'})
                    self.send(nx.tostring())
                    return
                
                RosterQueryTag='{jabber:iq:roster}query'
                RosterQueryStz=x.e.find(RosterQueryTag)
                if RosterQueryStz!=None:
                    nx = xm(self.SentHeader,tag='iq',
                            attrib={'id':x.e.attrib['id'],'type':'result'},
                            sub=[xm(self.SentHeader,tag='query',
                                    attrib={'xmlns':'jabber:iq:roster'})])
                    self.send(nx.tostring())
                    return

                if 'type' in x.e.attrib:
                    if x.e.attrib['type']=='get' or x.e.attrib['type']=='set':
                        nx = xm(self.SentHeader,tag='iq',
                                attrib={'id':x.e.attrib['id'],'type':'result'})
                        self.send(nx.tostring())
                        return
                    return
                
                pass
            
            pass
        
        elif self.Type=='Component':
            if x.e.tag=='{jabber:component:accept}handshare':
                print(m)
                return
            pass
        
        elif self.Type=='Server':
            if x.e.tag=='{http://etherx.jabber.org/streams}features':
                DialBackTag='{urn:xmpp:features:dialback}dialback'
                DialBackStz=x.e.find(DialBackTag)
                if DialBackStz!=None:
                    key='128937498012384103458123401923788912837081238023492341237892378'
                    nx = xm(self.SentHeader,tag='db:result',
                            attrib={'from':self.manager.servname,'to':self.peername},
                            text=key)
                    self.send(nx.tostring())
                    return
                return
            pass
        
        else:
            return
        
        #sthdr = msgin.sthdr(m)
        #if sthdr.attrs[ns.XMLNS] == ns.JABBER_CLIENT:
        #    stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CLIENT))
        #    cs = server.client.session(stream,self.manager)
        #    self.clientlist.append(cs)
        #    while stream in self.tcpconlist: self.tcpconlist.remove(stream)
        #    pass
        #elif sthdr.attrs[ns.XMLNS] == ns.JABBER_CMPNT:
        #    stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CMPNT))
        #    cm = server.component.session(stream, self.manager)
        #    cm.name = sthdr.attrs['from']
        #    self.compntlist.append(cm)
        #    while stream in self.tcpconlist: self.tcpconlist.remove(stream)
        #    pass
        #pass
        pass

    pass

class sessmanager:

    def __init__(self, manager):
        self.manager = manager
        self.pendingmsg = []
        self.sessionlist = []
        
#        self.tcpconlist = []
#        self.clientlist = []
#        self.compntlist = []

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
    
    def pendmsgcheck(self):
        if len(self.pendingmsg)==0: return
        (s,m,t,stat) = self.pendingmsg[0]
        if t<int(time.time()-5):
            self.pendingmsg.remove((s,m,t,stat))
            return
        x = xm(s.RcvdHeader)
        x.fromstring(m)
        if ('to' in x.e.attrib) == False:
            self.pendingmsg.remove((s,m,t,stat))
            return
        (uname, sname, rname) = msgin.splitjid(x.e.attrib['to'])
        try: host = self.srvrec(sname)
        except:
            self.pendingmsg.remove((s,m,t,stat))
            return
        if stat=='init':
            pa = (host,5269)
            try: ps = socket.create_connection(pa, 5)
            except:
                self.pendingmsg.remove((s,m,t,stat))
                return
            self.pendingmsg.remove((s,m,t,stat))
            self.pendingmsg.append((s,m,t,'connecting'))
            ps.settimeout(None)
            nx = xm('')
            a = {'xmlns:stream':'http://etherx.jabber.org/streams',
                 'xmlns':'jabber:server',
                 'xmlns:db':'jabber:server:dialback',
                 'version':'1.0',
                 'from':self.manager.servname,
                 'to':sname}
            nx.create(tag='stream:stream', attrib=a)
            self.addsocket(ps,pa,nx.tostring())
            pass
        pass
    
    def timercheck(self):
        for ses in self.sessionlist:
            if ses.TmPing+60<int(time.time()):
                nx = xm(ses.SentHeader,tag='iq',
                        attrib={'from':self.manager.servname,
                                'to':ses.ident(),
                                'id':utils.randstr(8),
                                'type':'get'},
                        sub=[xm(ses.SentHeader,tag='ping',attrib={'xmlns':'urn:xmpp:ping'})])
                ses.send(nx.tostring())
                ses.TmPing = int(time.time())
                pass
            if ses.TmRmsg+180<int(time.time()):
                ses.stream.close()
                pass
            pass
        pass

    def print(self):
        xmpp.utils.print_clear()
        print("=====================")
        print("clients:")
        l = "|{JID:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|{PT:>10}|{PS:>10}|{PH:>10}|"
        l = l.format(JID="JID",CRM="#recv",CSM="#send",TP="ping",TR="last",
                     PT="ptype", PS="pstat", PH="pshow")
        print(l)
        for ses in self.sessionlist:
            #s.print()
            print(ses.Type, ses.stream.peeraddr, ses.ident(),
                  ses.CntSMsg,ses.CntRMsg,
                  int(time.time())-ses.TmPing,
                  int(time.time())-ses.TmRmsg)
            pass
        pass
    
#    
#    def getclientsess(self, jid):
#        retlist = []
#        for cs in self.clientlist:
#            if cs.barejid == jid or cs.fulljid == jid:
#                retlist.append(cs)
#                pass
#            pass
#        return retlist
#    
#    def getcompntsess(self, to):
#        retlist = []
#        for cm in self.compntlist:
#            if cm.name == to or to.find("@"+cm.name) != -1:
#                retlist.append(cm)
#                pass
#            pass
#        return retlist
#
#    def getforwardsess(self,msgto):
#        retlist = []
#        if msgto.find("@"):
#            # if after '@' is me, find client-list
#            if msgto.find("@"+self.manager.servname):
#                retlist.extend(self.getclientsess(msgto))
#                pass
#            # if after '@' is my components, find component-list
#            retlist.extend(self.getcompntsess(msgto))
#            # if after '@' is unknown, other servers
#            pass
#        else:
#            # if '@' doesn't exist, find component-list
#            retlist.extend(self.getcompntsess(msgto))
#            pass
#        return retlist
    
#    def recvsthdr(self, stream, m):
#        sthdr = msgin.sthdr(m)
#        if sthdr.attrs[ns.XMLNS] == ns.JABBER_CLIENT:
#            stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CLIENT))
#            cs = server.client.session(stream,self.manager)
#            self.clientlist.append(cs)
#            while stream in self.tcpconlist: self.tcpconlist.remove(stream)
#            pass
#        elif sthdr.attrs[ns.XMLNS] == ns.JABBER_CMPNT:
#            stream.send(msgout.sthdr(self.manager.servname, ns.JABBER_CMPNT))
#            cm = server.component.session(stream, self.manager)
#            cm.name = sthdr.attrs['from']
#            self.compntlist.append(cm)
#            while stream in self.tcpconlist: self.tcpconlist.remove(stream)
#            pass
#        pass
    
#    def timercheck(self):
#        for cs in self.clientlist:
#            if cs.tmping+60<int(time.time()):
#                cs.send(msgout.ping(self.manager.servname,cs.fulljid))
#                cs.tmping = int(time.time())
#                pass
#            if cs.tmrmsg+180<int(time.time()):
#                cs.stream.close()
#                pass
#            pass
#        for cm in self.compntlist:
#            if cm.tmping+60<int(time.time()):
#                cm.send(msgout.ping(self.manager.servname,cm.name))
#                cm.tmping = int(time.time())
#                pass
#            if cm.tmrmsg+180<int(time.time()):
#                cm.stream.close()
#                pass
#            pass
#        pass
    
    def closed(self,st,m):
        st.close()
        for ses in self.sessionlist:
            if ses.stream is st: self.sessionlist.remove(ses)
            pass
        pass
#        while st in self.tcpconlist: self.tcpconlist.remove(st)
#        for sess in self.clientlist:
#            if sess.stream is st: self.clientlist.remove(sess)
#            pass
#        for sess in self.compntlist:
#            if sess.stream is st: self.compntlist.remove(sess)
#            pass
#        pass

    def addsocket(self, peersock, peeraddr, initmsg=''):
        #s = peersock
        #st = 
        #st.CBF_recv = self.recvsthdr
        #st.CBF_closed = self.closed
        #st.socket = s
        #st.start()
        ses = session()
        ses.manager = self.manager
        ses.stream = xmpp.stream.stream()
        ses.stream.CBF_recv = ses.recv
        ses.stream.CBF_closed = self.closed
        ses.stream.peeraddr = peeraddr
        ses.stream.socket = peersock
        if initmsg!='':
            ses.send(initmsg)
            ses.SentHeader = initmsg
            pass
        ses.stream.start()
        #self.tcpconlist.append(st)
        self.sessionlist.append(ses)
        pass
    
#    def print(self):
#        xmpp.utils.print_clear()
#        print("=====================")
#        print("clients:")
#        l = "|{JID:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|{PT:>10}|{PS:>10}|{PH:>10}|"
#        l = l.format(JID="JID",CRM="#recv",CSM="#send",TP="ping",TR="last",
#                     PT="ptype", PS="pstat", PH="pshow")
#        print(l)
#        for s in self.clientlist:
#            s.print()
#            pass
#        print("=====================")
#        print("components:")
#        l = "|{NAME:<35}|{CRM:>5}|{CSM:>5}|{TP:>4}|{TR:>4}|"
#        l = l.format(NAME="name",CRM="#recv",CSM="#send",TP="ping",TR="last")
#        print(l)
#        for s in self.compntlist:
#            s.print()
#            pass
#        pass
#    pass

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
    
    def __init__(self, bindaddr, port, ipver=4):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sfamily = socket.AF_INET
        if ipver==6: self.sfamily = socket.AF_INET6
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
        # self.svssmanager = svssmanager(self)
        
        pass
    
    def accept(self, ps, pa):
        self.sessmanager.addsocket(ps, pa)
        pass
    
    #def s2saccept(self, ps, pa):
    #    print("def s2saccept(self, ps, pa):")
    #    self.svssmanager.addsocket(ps)
    #    pass
    
    def start(self):
        
        self.confmanager.read(self.conffile)
        self.servname = self.confmanager.servname
        
        #BindAddress4 = '0.0.0.0'
        #s4 = serversocket(BindAddress4, int(self.confmanager.cbindport4))
        #s4.sfamily = socket.AF_INET
        #s4.sstream = socket.SOCK_STREAM        
        #BindAddress6 = '::'
        #s6 = serversocket(BindAddress6, int(self.confmanager.cbindport6))
        #s6.sfamily = socket.AF_INET6
        #s6.sstream = socket.SOCK_STREAM        
        #ss4 = serversocket("0.0.0.0", 5269)
        
        cs4 = serversocket('0.0.0.0', 5222)
        cs4.accepted = self.accept
        cs4.start()
        cs6 = serversocket('::', 5222, 6)
        cs6.accepted = self.accept
        cs6.start()
        ss4 = serversocket('0.0.0.0', 5269)
        ss4.accepted = self.accept
        ss4.start()
        ss6 = serversocket('::', 5269, 6)
        ss6.accepted = self.accept
        ss6.start()
        
        while True:
            self.sessmanager.timercheck()
            self.sessmanager.print()
            self.sessmanager.pendmsgcheck()
            print("\n")
            time.sleep(1)
            pass
        
        pass
    
    pass
