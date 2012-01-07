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

import time, base64
import xmpp, xmpp.stream, xmpp.auth
import xmpp.utils as utils
from xmpp.msg import xmsg as xm

class client:
    def __init__(self):
        self.Authorized = False
        self.RecvStmHdr = ''
        self.SendStmHdr = ''
        self.stream = xmpp.stream.stream()
        self.stream.CBF_recv = self.received
        self.stream.CBF_closed = self.closed
        self.server = ''
        self.port = 5222
        self.username = ''
        self.password = ''
        self.resource = ''
        self.CBF_received = None
        self.CBF_closed = None
        pass

    def received(self,s,m):
        self.stream.send(' ')
        x=xm(self.RecvStmHdr)
        x.fromstring(m)
        utils.dprint(x.e.tag)
        
        if '{http://etherx.jabber.org/streams}stream'==x.e.tag:
            self.RecvStmHdr = m
            pass
        
        elif '{http://etherx.jabber.org/streams}features'==x.e.tag:
            if self.Authorized == False:
                pwstr = '\0' + self.username  + '\0' + self.password + '\0'
                pwstr = base64.b64encode(pwstr.encode('cp932')).decode('utf-8')
                nx=xm(self.SendStmHdr)
                nx.create(tag='auth',
                          attrib={'xmlns':'urn:ietf:params:xml:ns:xmpp-sasl',
                                  'mechanism':'PLAIN'},
                          text=pwstr)
                self.stream.send(nx.tostring())
                pass
            
            else:
                rm = '<iq type="set" id="bind_1" >'+\
                     '<bind xmlns="urn:ietf:params:xml:ns:xmpp-bind"><resource>' +\
                     self.resource + '</resource></bind></iq>'
                sm = '<iq type="set" id="sess_1" >' +\
                     '<session xmlns="urn:ietf:params:xml:ns:xmpp-session" /></iq>'
                self.stream.send(rm+sm)
                pass
            
            pass
        
        elif '{urn:ietf:params:xml:ns:xmpp-sasl}success'==x.e.tag:            
            self.Authorized = True
            self.SendStmHdr = ''
            self.RecvStmHdr = ''
            x=xm('',tag='stream:stream',
                 attrib={'to':self.server,
                         'version':'1.0',
                         'xmlns':'jabber:client',
                         'xmlns:stream':'http://etherx.jabber.org/streams'})
            self.SendStmHdr = x.tostring()
            self.stream.send(self.SendStmHdr)
            pass

        elif '{jabber:client}iq'==x.e.tag and \
             'id' in x.e.attrib and \
             (x.e.attrib['id'] == 'bind_1' or x.e.attrib['id'] == 'sess_1'):
            pass
        
        else:
            if self.CBF_received!=None: self.CBF_received(m)
            pass
        
        pass
    
    def closed(self,s,m):
        if self.CBF_closed!=None: self.CBF_closed()
        pass
    
    def connect(self, sv, pt, us, pw, rs):
        self.server = sv
        self.port = pt
        self.username = us
        self.password = pw
        self.resource = rs
        self.stream.CBF_recv = self.received
        self.stream.CBF_closed = self.closed
        self.stream.connect(sv,pt)
        x=xm('',tag='stream:stream',
             attrib={'to':sv,
                     'version':'1.0',
                     'xmlns':'jabber:client',
                     'xmlns:stream':'http://etherx.jabber.org/streams'})
        self.SendStmHdr = x.tostring()
        self.stream.send(x.tostring())
        self.stream.start()
        pass

    def send(self,m):
        self.stream.send(m)
        pass
    
    pass
