#!/usr/local/bin/python3.2

import xml
from xml.etree import ElementTree
import xmpp
import xmpp.ns as ns
import xmpp.msg as msg
import xmpp.msgin as msgin
import xmpp.msgout as msgout
from xmpp.utils import randstr

import socket

class servsess:
    
    def __init__(self):
        self.stat = ''
        self.manager = None
        self.mfrom = ''
        self.mto = ''
        self.stream = None
        self.sendsthdr = False
        self.sendfeat = False
        self.authorized = False
        self.reqsendkey = False
        self.m_recvsthdr = ''
        self.m_sendsthdr = ''
        self.check_connection = False
        self.key = '12378489238471923708295802384023874109832942304728371083212093'#randstr(128)
        pass
    
    def recv(self, stream, m):
        
        mt = msgin.getmsgtype(m)

        # forward the message if needed
        mto = msgin.getmsgto(m)
        mfr = msgin.getmsgfrom(m)
        (uname, sname, rname) = msgin.splitjid(mto)
        print((uname, sname, rname))
        if sname != '' and sname != self.manager.servname: #forward msg to other server
            self.manager.svssmanager.sendqueue.put((mfr,mto,m))
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
                #m = msgout.addfrom(m, self.name)
                ses.send(m)
                pass
            return
        
        if mt == 'stream:stream':
            #self.stream.ready = True
            #self.stream.send('')
            sthdr = msgin.sthdr(m)
            self.m_recvsthdr = m
            if sthdr.attrs[ns.XMLNS] == ns.JABBER_SERVER:
                if self.sendsthdr==False:
                    self.m_sendsthdr = msgout.sthdr(self.mfrom, ns.JABBER_SERVER)
                    stream.send(self.m_sendsthdr)
                    pass
                elif self.authorized==False and self.reqsendkey==True:
                    m = '<db:result from="{MFROM}" to="{MTO}">{MKEY}</db:result>'
                    m = m.format(MFROM=self.mfrom,MTO=self.mto,MKEY=self.key)
                    stream.send(m)
                    pass
                else:
                    if self.sendfeat==False:
                        stream.send(msgout.featdback())
                        self.sendfeat=True
                        pass
                    pass
                pass
            #ss = server.server.session(stream,self.manager)
            #self.clientlist.append(ss)
            #while stream in self.tcpconlist: self.tcpconlist.remove(stream)
            pass
        
        if mt == 'stream:features' or mt == 'features':
            self.stream.ready = True
            self.stream.send('')
            pass
        
        if mt == 'result':
            # if type is valid
            # change connection status to 'ready'
            
            xr = msg.xmsg(self.m_recvsthdr)
            xr.fromstring(m)

            if ('type' in xr.e.attrib) == False:
                mf = msgin.getmsgfrom(m)                
                domain = mf
                host = self.manager.svssmanager.srvrec(domain)
                #xxx
                xr = msg.xmsg(self.m_recvsthdr)
                xr.fromstring(m)
                xs = msg.xmsg(self.m_sendsthdr)
                xs.fromstring(m)
                xs.e.attrib['type'] = 'valid'
                xs.e.attrib['to'] = xr.e.attrib['from']
                xs.e.attrib['from'] = xr.e.attrib['to']
                self.stream.send(xs.tostring())
                #######################################################
                # print("### connect to " + host + " as master of " + domain)
                # st = xmpp.stream.stream()
                # ss = servsess()
                # ss.manager = self.manager
                # ss.mfrom = self.manager.servname
                # ss.mto = domain
                # ss.stream = st
                # st.CBF_recv = ss.recv
                # st.CBF_closed = self.manager.svssmanager.closed
                # st.connect(host,5269)
                # st.start()
                # ss.m_sendsthdr = msgout.sthdr(self.manager.servname, ns.JABBER_SERVER, msgid='no', xmlnsdb='yes',msgto=domain)
                # st.send(ss.m_sendsthdr)
                # ss.sendsthdr = True
                # ss.sendfeat = True
                # ss.check_connection = True
                # newm = msg.xmsg(ss.m_sendsthdr,
                #                 tag='db:verify',
                #                 attrib={'from':self.manager.servname,
                #                         'to':domain,
                #                         'id':randstr(16)},
                #                 text=xr.e.text)
                # ss.stream.ready = False
                # st.send(newm.tostring())
                # self.manager.svssmanager.peersvlist.append(ss)
                #######################################################
                pass
            
            elif xr.e.attrib['type']=='valid':
                if self.check_connection == True:
                    self.stream.send("</stream:stream>")
                    self.stream.close()
                    return
                self.stat='ready'
                self.manager.svssmanager.flush()
                pass
            
            pass

        if mt == 'verify':
            xr = msg.xmsg(self.m_recvsthdr)
            xr.fromstring(m)
            if ('type' in xr.e.attrib) != False:
                if xr.e.attrib['type'] == 'invalid':
                    self.stream.close()
                    return
                pass
            
            xs = msg.xmsg(self.m_sendsthdr)
            xs.fromstring(m)
            xs.e.attrib['type'] = 'valid'
            xs.e.attrib['to'] = xr.e.attrib['from']
            xs.e.attrib['from'] = xr.e.attrib['to']
            stream.send(xs.tostring())
            pass
        
        if mt == '/stream:stream':
            print("### closed ###")
            self.stream.close()
            pass
        
        pass
    
    pass

# #class peerserver:
# #    pass
# 
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #s.connect(('xmpp.l.google.com', 5269))
# s.connect(('hermes.jabber.org', 5269))
# 
# m1 = '<stream:stream from="nlab.im" to="jabber.org" version="1.0" xmlns="jabber:server" xmlns:db="jabber:server:dialback" xmlns:stream="http://etherx.jabber.org/streams">'
# print("S: " +m1)
# s.send(m1.encode("cp932"))
# 
# r1 = s.recv(1024*1024)
# print("R: " +r1.decode('utf-8'))
# 
# m2 = '<db:result from="nlab.im" to="jabber.org">38971378734895180238409185072893475018230498178578934750182394</db:result>'
# s.send(m2.encode("cp932"))
# print("S: " +m2)
# 
# ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ls.bind(('0.0.0.0', 5269))
# ls.listen(5)
# 
# (ps, pa) = ls.accept()
# r2 = ps.recv(1024*1024)
# print("R: " +r2.decode('utf-8'))
# 
# m1 = '<stream:stream from="nlab.im" to="jabber.org" version="1.0" xmlns="jabber:server" xmlns:db="jabber:server:dialback" xmlns:stream="http://etherx.jabber.org/streams">'
# print("S: " +m1)
# ps.send(m1.encode("cp932"))
# 
# 
# # sv1# ./test.py
# # S: <stream:stream from="nlab.im" to="c.kyoai.ac.jp" version="1.0" xmlns="jabber:server" xmlns:db="jabber:server:dialback" xmlns:stream="http://etherx.jabber.org/streams">
# # R: <stream:stream id="A67B47E4DB7C86B0" xmlns:stream="http://etherx.jabber.org/streams" xmlns="jabber:server" xmlns:db="jabber:server:dialback">
# # S: <db:result from="nlab.im" to="c.kyoai.ac.jp">38971378734895180238409185072893475018230498178578934750182394</db:result>
# # R: <stream:stream id="A35D361399E05270" xmlns:stream="http://etherx.jabber.org/streams" xmlns="jabber:server" xmlns:db="jabber:server:dialback">
# 
# 
# # S: <stream:stream from="nlab.im" to="jabber.org" version="1.0" xmlns="jabber:server" xmlns:db="jabber:server:dialback" xmlns:stream="http://etherx.jabber.org/streams">
# # R: <?xml version='1.0'?><stream:stream xmlns='jabber:server' xmlns:db='jabber:server:dialback' xmlns:stream='http://etherx.jabber.org/streams' to='nlab.im' from='jabber.org' id='74169a2ad611d297' version='1.0'><stream:features><starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls'/><dialback xmlns='urn:xmpp:features:dialback'/><compression xmlns='http://jabber.org/features/compress'><method>zlib</method></compression></stream:features>
# # S: <db:result from="nlab.im" to="jabber.org">38971378734895180238409185072893475018230498178578934750182394</db:result>
# # R: <?xml version='1.0'?><stream:stream xmlns='jabber:server' xmlns:db='jabber:server:dialback' xmlns:stream='http://etherx.jabber.org/streams' to='nlab.im' from='jabber.org' version='1.0'>
