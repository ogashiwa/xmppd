#!/usr/local/bin/python3.2

import socket

class servsess:
    
    def __init__(self):
        self.type = 'connection' # connection, dialback
        self.stat = 'wait' # wait authorized
        self.stream = None
        pass
    
    def sendsthdr(self):
        a={'xmlns':'jabber:server',
           'xmlns:db':'jabber:server:dialback',
           'xmlns:stream':'http://etherx.jabber.org/streams',
           'from':'nlab.im', #xxx
           'to':'jabber.org',#xxx
           'version':'1.0'}
        m = xs1.newstr(tag="stream:stream",attrib=a)
        self.stream.send(m)
        pass
    
    def recevied(self,st,m):
        if : # receive stream header
            # send stream header with id
            return
        pass
    
    def closed(self,st,m):
        
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
