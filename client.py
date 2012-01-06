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

import time
import xmpp.utils as utils
from xmpp.msg import xmsg as xm
from client.client import client as client

c = client()
sent_sthdr = ''
recv_sthdr = ''

def g_received(stanza):
    global c, sent_sthdr, recv_sthdr
    if sent_sthdr=='': sent_sthdr = c.SendStmHdr
    if recv_sthdr=='': recv_sthdr = c.RecvStmHdr
    
    print("#####STANZA#####")
    print(stanza)
    
    x = xm(recv_sthdr)
    x.fromstring(stanza)
    
    if x.e.tag=='{jabber:client}iq':
        
        pe = x.e.find('{urn:xmpp:ping}ping')
        if pe!=None:
            print(x.e.tag)
            print(x.e.attrib)
            print(pe)
            print(pe.tag)
            print(pe.attrib)
            pong = xm(sent_sthdr)
            pong.create(tag='iq',
                        attrib={'from':x.e.attrib['to'],
                                'to':x.e.attrib['from'],
                                'id':x.e.attrib['id'],
                                'type':'result'})
            c.send(pong.tostring())
            pass
        
        pass
    
    pass

def g_closed():
    pass

def main():
    utils.debug(True)

    global c
    c.CBF_received = g_received
    c.CBF_closed = g_closed
    c.connect('nlab.im', 5222, 'test001', 'test001', 'myclient')
    
    while True:
        time.sleep(1)
        pass
    pass

if __name__ == "__main__":
    main()
    pass
