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
from xmpp import entity

XmppComponent = entity.entity(type='component')

def g_received(stz):
    global XmppComponent
    RecvStz = stz.GetSourceStanza()
    RecvET = stz.GetElementTree()
    
    print("#####STANZA#####")
    print(RecvStz)
    print("################")
    print(RecvET.tag)
    print("################")
    
    if RecvET.tag=='{jabber:client}iq':
        pass
    
    elif RecvET.tag=='{jabber:client}message':
        pass
    
    elif RecvET.tag=='{jabber:client}presence':
        pass
    
    else:
        pass
    
    pass

def g_connected(): print("connected")
def g_closed(): print("closed")
def g_error(): print("error")

################################################################################

def main():
    global XmppComponent
    
    XmppComponent.DebugMode(True)
    
    XmppComponent.RegisterCallbackFunctions(
        Received = g_received,
        Closed = g_closed,
        Connected = g_connected,
        ErrorOccurred = g_error)
    
    XmppComponent.SetOptions(
        AuthPong = True,
        UserName = 'test001',
        Password = 'test001',
        AuthMethod = 'PLAIN',
        ServerName = 'nlab.im',
        ServerPort = 5222)
    
    XmppComponent.Start()
    
    while True:
        time.sleep(1)
        pass
    pass

################################################################################

if __name__ == "__main__":
    main()
    pass
