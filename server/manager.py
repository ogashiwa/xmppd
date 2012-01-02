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

import sys, threading, re, socket, time, subprocess, xml, random
import xmpp, xmpp.stream, xmpp.auth
import xmpp.utils as utils
from xml.etree import ElementTree as ET
from xmpp.msg import xmsg as xm

def splitjid(jid):
    r = re.search(r'(?ms)([^@]+)@([^/]+)/(.+)',jid)
    if r is not None: return (r.group(1),r.group(2),r.group(3))
    r = re.search(r'(?ms)([^@]+)@([^/]+)',jid)
    if r is not None: return (r.group(1),r.group(2),'')
    return ('',jid,'')

class session:
    
    def __init__(self):
        self.manager = None
        self.authman = None
        #self.servauth = False
        self.activeopen = False
        self.sendkey = False
        self.authorized = True
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
    
    def send(self,m,force=False):
        if force==False and self.authorized==False: return
        self.CntSMsg += 1
        self.stream.send(m)
        pass

    def forward(self,sess,m):
        
        x = xm(self.RcvdHeader)
        x.fromstring(m)
        utils.dprint("#forward to "+sess.ident()+" type is "+sess.Type)
        
        #pmsg='<presence from="{F}" to="{T}" type="subscribed" /><presence from="{F}" to="{T}" />'
        #pmsg=pmsg.format(F=self.ident(),T=x.e.attrib['to'])
        
        inttag = ''
        posa = m.find('>')
        posb = m.rfind('<')
        inttag = m[posa+1:posb]
        utils.dprint(inttag)
        att={'to':x.e.attrib['to']}
        
        if 'from' in x.e.attrib: att['from']=x.e.attrib['from']
        elif self.ident()!='': att['from']=self.ident()
        if 'id' in x.e.attrib: att['id']=x.e.attrib['id']
        if 'type' in x.e.attrib: att['type']=x.e.attrib['type']
        atstr = ''
        for k,v in att.items():
            tmpstr = ' {N}="{VAL}" '.format(N=k,VAL=v)
            atstr += tmpstr
            pass
        nt='iq'
        if x.e.tag.find('}message')>0: nt='message'
        elif x.e.tag.find('}iq')>0: nt='iq'
        elif x.e.tag.find('}presence')>0: nt='presence'
        
        newmsg = '<{T} {A}>{I}</{T}>'.format(T=nt,A=atstr,I=inttag)
        nx=xm(sess.SentHeader)
        nx.fromstring(newmsg)
        #utils.dprint(nx.tostring())
        #utils.dprint(nx.tostring())
        #sess.send(pmsg)
        sess.send(nx.tostring())
        
        pass

    def recv(self, stream, m):
        try: self.recv_internal(stream, m)
        except:
            print("Unexpected error:", sys.exc_info())
            self.stream.close()
            pass
        pass
    
    def recv_internal(self, stream, m):
        
        self.CntRMsg += 1
        self.TmRmsg = int(time.time())
        
        x = xm(self.RcvdHeader)
        x.fromstring(m)

        # ============================================================
        # receive stream header
        # ============================================================
        
        if x.e.tag=='{http://etherx.jabber.org/streams}stream':
            
            self.RcvdHeader = m
            nx = xm(self.SentHeader)
            a = {'xmlns:stream':'http://etherx.jabber.org/streams',
                 'xmlns:xml':"http://www.w3.org/XML/1998/namespace",
                 'version':'1.0'}
            
            
            if m.find('jabber:client')>0:
                self.Type='Client'
                a['xmlns'] = 'jabber:client'
                a['from'] = self.manager.servname
                nx.create(tag='stream:stream', attrib=a)
                self.SentHeader = ''
                pass
            
            elif m.find('jabber:component:accept')>0:
                self.Type='Component'
                a['xmlns'] = 'jabber:component:accept'
                a['id'] = utils.randstr(8)
                a['from'] = self.manager.servname
                nx.create(tag='stream:stream', attrib=a)
                pass

            elif m.find('jabber:server')>0:
                self.Type='Server'
                if 'from' in x.e.attrib: self.peername = x.e.attrib['from']
                a['xmlns'] = 'jabber:server'
                a['xmlns:db']='jabber:server:dialback'
                if self.peername!='': a['to'] = self.peername
                a['id'] = utils.randstr(16)
                nx.create(tag='stream:stream', attrib=a)
                pass
            
            else:
                self.stream.close()
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

            if self.Type=='Server':
                
                if self.activeopen:
                    key='1e701f120f66824b57303384e83b51feba858024fd2221d39f7acc52dcf767a9'
                    nx = xm(self.SentHeader,tag='db:result',
                            attrib={'from':self.manager.servname,'to':self.peername},
                            text=key)
                    self.send(nx.tostring(),force=True)
                    pass

                #if random.choice('01')=='1' and self.activeopen==False:
                #    nx = xm(self.SentHeader)
                #    nx.create(tag='stream:features',
                #              sub=[xm(self.SentHeader,tag='dialback',
                #                      attrib={'xmlns':'urn:xmpp:features:dialback'},
                #                      sub=[xm(self.SentHeader,tag='optional')])])
                #    self.send(nx.tostring())
                #    pass
                
                pass
            return

        # ============================================================
        # msg forward check
        # ============================================================

        utils.dprint(x.e.tag)
        
        if 'to' in x.e.attrib:
            utils.dprint(x.e.attrib['to'])
            (uname, sname, rname) = splitjid(x.e.attrib['to'])
            utils.dprint((uname, sname, rname))
            
            for sess in self.manager.sessmanager.sessionlist:
                fw = False
                if sess==self: continue
                
                if x.e.attrib['to']==sess.ident(): fw = True
                elif sname==sess.ident(): fw = True
                
                if fw==True:
                    if sess.Type == 'Server':
                        if sess.ident()==sname and sess.authorized and sess.activeopen==True:
                            self.forward(sess,m)
                            pass
                        pass
                    else:
                        self.forward(sess,m)
                    return                
                pass
            
            if sname!=self.manager.servname:
                self.manager.sessmanager.pendingmsg.append((self,m,int(time.time()),'init'))
                return
            
            pass
        
        # ============================================================
        # in case of client connection
        # ============================================================

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

        # ============================================================
        # in case of component connection
        # ============================================================
        
        elif self.Type=='Component':
            if x.e.tag=='{jabber:component:accept}handshare':
                utils.dprint(m)
                return
            pass
        
        # ============================================================
        # in case of server connection
        # ============================================================
        
        elif self.Type=='Server':
            
            #if x.e.tag=='{http://etherx.jabber.org/streams}features':
            #    nx = xm(self.SentHeader)
            #    nx.create(tag='stream:features',
            #              sub=[xm(self.SentHeader,tag='dialback',
            #                      attrib={'xmlns':'urn:xmpp:features:dialback'},
            #                      sub=[xm(self.SentHeader,tag='optional')])])
            #    self.send(nx.tostring())
                
            #     
            #     intags = x.e.findall('*')
            #     itstr = []
            #     for ie in intags: itstr.append(ie.tag)
            # 
            #     if '{urn:ietf:params:xml:ns:xmpp-tls}starttls' in itstr: pass
            #     if '{http://jabber.org/features/compress}compression' in itstr: pass
            #     if '{urn:xmpp:features:dialback}dialback' in itstr:
            #         key='1e701f120f66824b57303384e83b51feba858024fd2221d39f7acc52dcf767a9'
            #         nx = xm(self.SentHeader,tag='db:result',
            #                 attrib={'from':self.manager.servname,'to':self.peername},
            #                 text=key)
            #         self.send(nx.tostring(),force=True)
            #         return
            #     
            #     #DialBackTag='{urn:xmpp:features:dialback}dialback'
            #     #DialBackStz=x.e.find(DialBackTag)
            #     #if DialBackStz!=None:
            #     #    return
            #     
            #     return

            if x.e.tag=='{jabber:server:dialback}verify':
                
                nx = xm(self.SentHeader,tag='db:verify',
                        attrib={'xmlns:db':'jabber:server:dialback',
                                'from':x.e.attrib['to'],
                                'to':x.e.attrib['from'],
                                'id':x.e.attrib['id'],
                                'type':'valid'},
                        text=x.e.text)
                self.send(nx.tostring())
                # time.sleep(1)
                # self.send('</stream:stream>')
                return
            
            if x.e.tag=='{jabber:server:dialback}result':
                
                if 'type' in x.e.attrib:
                    if x.e.attrib['type']=='valid': self.authorized = True
                    else: self.stream.close()
                    return
                else:
                    nx = xm(self.SentHeader,tag='db:result',
                            attrib={'from':x.e.attrib['to'],
                                    'to':x.e.attrib['from'],
                                    'type':'valid'})
                    time.sleep(1)
                    self.send(nx.tostring())
                    return

                #    serv = x.e.attrib['from']
                #    hostportlist = self.manager.sessmanager.srvrec(serv)
                #    self.manager.sessmanager.add_active_socket(hostportlist[0],serv)
                    
                    # s = socket.create_connection((host, 5269), 5)
                    # s.settimeout(None)
                    # nx1 = xm('',tag='stream:stream',
                    #          attrib={'xmlns':'jabber:server',
                    #                  'xmlns:db':'jabber:server:dialback',
                    #                  'xmlns:stream':'http://etherx.jabber.org/streams',
                    #                  'xmlns:xml':"http://www.w3.org/XML/1998/namespace",
                    #                  'version':'1.0',
                    #                  'to':serv,
                    #                  'from':self.manager.servname})
                    # sth = nx1.tostring()
                    # s.send(sth.encode('cp932'))
                    # utils.dprint(sth.encode('cp932'))
                    # rmsg = s.recv(1024*1024)
                    # utils.dprint(rmsg)
                    # nx2 = xm(sth,tag='db:verify',
                    #          attrib={'from':self.manager.servname,
                    #                  'to':serv,
                    #                  'id':utils.randstr(16)},
                    #          text=x.e.text)
                    # s.send(nx2.tostring().encode('cp932'))
                    # utils.dprint(nx2.tostring().encode('cp932'))
                    # rmsg = s.recv(1024*1024)
                    # utils.dprint(rmsg)
                    # s.send('</stream:stream>'.encode('cp932'))
                    
                #    nx = xm(self.SentHeader,tag='db:result',
                #            attrib={'from':x.e.attrib['to'],
                #                    'to':x.e.attrib['from'],
                #                    'type':'valid'},
                #            text=x.e.text)
                #    self.send(nx.tostring())
                #    return
                return
            pass

        # ============================================================
        # error
        # ============================================================

        else: self.stream.close()
        pass
    
    pass

class sessmanager:

    def __init__(self, manager):
        self.manager = manager
        self.pendingmsg = []
        self.sessionlist = []
        pass
    
    def srvrec(self,domain):
        m = subprocess.check_output(['/usr/bin/host', '-t', 'SRV', '_xmpp-server._tcp.'+domain])
        m = m.decode('utf-8')
        lm = m.splitlines()
        svlist=[]
        hostportlist=[]
        for l in lm:
            r = re.search(r'(?ms).*SRV record (.+) (.+) (.+) (.+)\.[\r\n]*', l)
            (prio,weig,port,host) = (int(r.group(1)),int(r.group(2)),
                                     int(r.group(3)),r.group(4))
            svlist.append((host,port,prio,weig))
            hostportlist.append((host,port))
            pass
        minsv = ''
        for s in svlist:
            if minsv == '': minsv = s
            if minsv[2] > s[2]: minsv = s
            pass
        minsv = minsv[0]
        #return minsv
        return hostportlist
    
    def pendmsgcheck(self):
        
        # if pending message doesn't exist
        if len(self.pendingmsg)==0: return

        # obtain a pending message
        (s,m,t,stat) = self.pendingmsg[0]
        
        # if its a too old message, discard it
        if t<int(time.time()-60):
            try: self.pendingmsg.remove((s,m,t,stat))
            except: pass
            return
        
        if t<int(time.time()-5) and int(time.time()-5)%5==0:
            try:
                self.pendingmsg.remove((s,m,t,stat))
                self.pendingmsg.append((s,m,t,'init'))
            except: pass
            pass
        
        # obtain servname and to-connect-hostname
        x = xm(s.RcvdHeader)
        x.fromstring(m)
        if ('to' in x.e.attrib) == False:
            try: self.pendingmsg.remove((s,m,t,stat))
            except: pass
            return
        (uname, sname, rname) = splitjid(x.e.attrib['to'])
        try: hostportlist = self.srvrec(sname)
        except:
            try: self.pendingmsg.remove((s,m,t,stat))
            except: pass
            return

        # if already have connection, send it
        for ses in self.sessionlist:
            if ses.ident()==sname and ses.authorized and ses.activeopen==True:
                s.forward(ses,m)
                try: self.pendingmsg.remove((s,m,t,stat))
                except: pass
                return
            pass
        
        # if not yet connected
        if stat=='init':
            #for hostport in hostportlist:
            #    self.add_active_socket(hostport,sname)
            #    pass
            self.add_active_socket(hostportlist[0],sname)
            try:
                self.pendingmsg.remove((s,m,t,stat))
                self.pendingmsg.append((s,m,t,'connecting'))
            except: pass
            
            # try: ps = socket.create_connection(pa, 5)
            # except:
            #     self.pendingmsg.remove((s,m,t,stat))
            #     return
            # self.pendingmsg.remove((s,m,t,stat))
            # self.pendingmsg.append((s,m,t,'connecting'))
            # ps.settimeout(None)
            # nx = xm('')
            # a = {'xmlns:stream':'http://etherx.jabber.org/streams',
            #      'xmlns':'jabber:server',
            #      'xmlns:db':'jabber:server:dialback',
            #      'version':'1.0',
            #      'from':self.manager.servname,
            #      'to':sname}
            # nx.create(tag='stream:stream', attrib=a)
            # self.addsocket(ps,pa,nx.tostring(),sname)
            # try: self.pendingmsg.append((s,m,t,'connecting'))
            # except: pass
            
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
                if ses.Type=='Server': ses.TmRmsg=int(time.time())
                else: ses.stream.close()
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
            print(ses.Type, ses.stream.peeraddr, ses.ident(),
                  ses.CntSMsg,ses.CntRMsg,
                  int(time.time())-ses.TmPing,
                  int(time.time())-ses.TmRmsg)
            pass
        pass
    
    def closed(self,st,m):
        st.close()
        for ses in self.sessionlist:
            try:
                if ses.stream is st: self.sessionlist.remove(ses)
            except: pass
            pass
        pass

    def add_passive_socket(self, peersock, peeraddr):
        ses = session()
        ses.manager = self.manager
        ses.stream = xmpp.stream.stream()
        ses.stream.CBF_recv = ses.recv
        ses.stream.CBF_closed = self.closed
        ses.stream.peeraddr = peeraddr
        ses.stream.socket = peersock
        ses.stream.start()
        self.sessionlist.append(ses)
        pass
    
    def add_active_socket(self, peeraddr, peername):
        try:
            peersock = socket.create_connection(peeraddr, 10)
            peersock.settimeout(None)
            ses = session()
            ses.activeopen = True
            ses.manager = self.manager
            ses.peername = peername
            ses.stream = xmpp.stream.stream()
            ses.stream.CBF_recv = ses.recv
            ses.stream.CBF_closed = self.closed
            ses.stream.peeraddr = peeraddr
            ses.stream.socket = peersock
            nx = xm('')
            a = {'xmlns:stream':'http://etherx.jabber.org/streams',
                 'xmlns':'jabber:server',
                 'xmlns:db':'jabber:server:dialback',
                 'version':'1.0'}
            #'from':self.manager.servname,
            #'to':ses.peername}
            nx.create(tag='stream:stream', attrib=a)
            sthdr = nx.tostring()
            ses.send(sthdr)
            ses.SentHeader = sthdr
            ses.authorized = False
            ses.sendkey = True
            ses.stream.start()
            self.sessionlist.append(ses)
        except:
            print("Unexpected error:", sys.exc_info())
            return
        pass
    
    #def addsocket(self, peersock, peeraddr, initmsg='', peername=''):
    #    ses = session()
    #    ses.manager = self.manager
    #    ses.stream = xmpp.stream.stream()
    #    ses.stream.CBF_recv = ses.recv
    #    ses.stream.CBF_closed = self.closed
    #    ses.stream.peeraddr = peeraddr
    #    ses.stream.socket = peersock
    #    ses.peername = peername
    #    if initmsg!='':
    #        ses.send(initmsg)
    #        ses.SentHeader = initmsg
    #        ses.servauth = False
    #        pass
    #    else: ses.servauth = True
    #    ses.stream.start()
    #    self.sessionlist.append(ses)
    #    pass
    
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
        
        pass
    
    def accept(self, ps, pa):
        self.sessmanager.add_passive_socket(ps, pa)
        pass

    def start(self):
        
        self.confmanager.read(self.conffile)
        self.servname = self.confmanager.servname
        
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
