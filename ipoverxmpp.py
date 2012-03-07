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
import os
import binascii
import sys
import getpass
import re
import subprocess
from xmpp.entity import XmppClient

def ByteToHex( byteStr ): return str(binascii.b2a_hex(byteStr))

f = 0
xc = XmppClient()

def g_received(stz):
    RecvStz = stz.GetSourceStanza()
    RecvET = stz.GetElementTree()
    
    #print("#####STANZA#####")
    #print(RecvStz)
    #print("################")
    #print(RecvET.tag)
    #print("################")
    
    if RecvET.tag=='{jabber:client}iq':
        pass
    
    elif RecvET.tag=='{jabber:client}message':
        tag = '{NS}body'.format(NS='{jabber:client}')
        bodytag = RecvET.find(tag)
        print("###############")
        print(bodytag.text)
        print("###############")
        #data = binascii.a2b_hex(bin(bodytag.text))
        #os.write(data) # xxxxxxx
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

def splitjid(jid):
    r = re.search(r'(?ms)([^@]+)@([^/]+)/(.+)',jid)
    if r is not None: return (r.group(1),r.group(2),r.group(3))
    r = re.search(r'(?ms)([^@]+)@([^/]+)',jid)
    if r is not None: return (r.group(1),r.group(2),'')
    return ('',jid,'')

def srvrec(domain):
    try:
        m = subprocess.check_output(['/usr/bin/host',
                                     '-t',
                                     'SRV',
                                     '_xmpp-server._tcp.'+domain])
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
        return minsv
    except: return domain

def usage():
    print("USAGE: ipoverxmpp.py user@domain/resource user@domain/resource tapN ipaddr netmask")
    pass

def main():
    global xc
    
    argv = sys.argv
    argc = len(argv)
    print(argv)
    print(argc)
    if argc != 6:
        usage()
        return
    print("Please enter password for " + argv[1])
    pw = getpass.getpass(stream=sys.stderr)
    
    (user, domain, resource) = splitjid(argv[1])
    serv = srvrec(domain)
    
    xc.DebugMode(True)
    
    xc.RegisterCallbackFunctions(
        Received = g_received,
        Closed = g_closed,
        Connected = g_connected,
        ErrorOccurred = g_error)
    
    xc.SetOptions(
        AutoPong = True,
        UserName =   user,
        Password =   pw,
        Resource =   resource,
        AuthMethod = 'PLAIN',
        ServerName = serv,
        ServerPort = 5222)
    
    xc.Start()

    time.sleep(10)

    ifopen = '/dev/{IFNAME}'
    ifcfg1 = 'ifconfig {IFNAME} {IPADDR} netmask {MASK}'
    ifcfg2 = 'ifconfig {IFNAME} up'
    ifopen = ifopen.format(IFNAME=argv[3])
    ifcfg1 = ifcfg1.format(IFNAME=argv[3], IPADDR=argv[4], MASK=argv[5])
    ifcfg2 = ifcfg2.format(IFNAME=argv[3])
    global f
    f = os.open(ifopen,os.O_RDWR)
    os.system(ifcfg1)
    os.system(ifcfg2)
    while True:
        try:
            data = os.read(f,4096)
            strd = ByteToHex(data)
            print(strd)
            msg = "<message from='{FROM}' to='{TO}' type='chat'><body>{DATA}</body></message>"
            msg = msg.format(FROM=argv[1], TO=argv[2], DATA=strd)
            xc.send(msg)
        except: pass
        pass
    pass

################################################################################

if __name__ == "__main__":
    main()
    pass
