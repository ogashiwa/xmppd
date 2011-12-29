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

import sys, socket, threading, time, getopt, re
import xml
from xml.etree.ElementTree import Element, SubElement, tostring
import xmpp.stream, xmpp.msgin, xmpp.msgout, xmpp.auth, xmpp.utils
import xmpp.ns as ns
import xmpp.msgin as msgin
import xmpp.msgout as msgout
import xmpp.utils

class mucmanager:
    def __init__(self):
        self.name = ""
        self.ckey = ""
        self.server = ""
        self.rooms = {}
        self.connected = False
        self.s = xmpp.stream.stream()
        self.s.CBF_recv = self.cbrecv
        self.s.CBF_closed = self.cbclose
        pass

    def print(self):
        l = "|{ROOM:<35}|{NMEM:>5}|"
        print(l.format(ROOM="room",NMEM="#mem"))
        for k,v in self.rooms.items():
            print(l.format(ROOM=k,NMEM=len(v)))
            pass
        pass
    
    def recv_component(self,m):
        global s
        t = xml.etree.ElementTree.fromstring(m)
        mid = t.attrib['id']
        mfrom = t.attrib['from']
        qtag = t.find('*')
        if qtag == None: return
        if qtag.tag == xmpp.utils.nt(ns.HTTP_DINFO,ns.TAG_QUERY):
            if t.tag != xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_IQ): return
            icateg = "conference"
            itype = "text"
            iname = "Chatrooms"
            featlist = ["http://jabber.org/protocol/muc"]
            self.s.send(msgout.dinfo(mid, self.name, mfrom, icateg,
                                     itype, iname, featlist))
            return 
        if qtag.tag == xmpp.utils.nt(ns.HTTP_DITEMS,ns.TAG_QUERY):
            if t.tag != xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_IQ): return
            itemslist = []
            for k,v in self.rooms.items():
                itemslist.append(k+"@"+self.name)
                pass
            self.s.send(msgout.ditems(mid, self.name, mfrom, itemslist))
            return
        if t.attrib['type'] == 'get' and \
               qtag.tag == xmpp.utils.nt("urn:xmpp:ping","ping"):
            self.s.send(msgout.pong(self.name, mfrom, t.attrib['id']))
            return
        pass

    def cbclose(self,stream,m):
        self.connected = False
        self.rooms = {}
        pass

    def cbrecv(self, stream,m):
        try: t = xml.etree.ElementTree.fromstring(m)
        except:
            m += "</stream:stream>"
            try: t = xml.etree.ElementTree.fromstring(m)
            except: return
            pass
        
        # stream header
        if t.tag == xmpp.utils.nt("http://etherx.jabber.org/streams", "stream"):
            self.s.send(msgout.hshake(t.attrib['id'], self.ckey))
            return 
        
        # to component-self
        if ('to' in t.attrib) == False:
            self.recv_component(m)
            return
        if t.attrib['to'] == self.name:
            self.recv_component(m)
            return
        
        (roomname, servname, nickname) = xmpp.msgin.splitjid(t.attrib['to'])
        
        # to room
        if roomname != '' and servname != '' and nickname == '':
            t = xml.etree.ElementTree.fromstring(m)
            
            if t.tag == xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_MSG) or t.tag==ns.TAG_MSG:
                fromnick = ''
                for (fjid,nick) in self.rooms[roomname]:
                    if t.attrib['from']==fjid: fromnick = nick
                    pass
                for (fjid,nick) in self.rooms[roomname]:
                    newto = fjid
                    newfm = roomname+"@"+servname+"/"+fromnick
                    t.attrib["from"] = newfm
                    t.attrib["to"] = newto
                    self.s.send(tostring(t).decode("utf-8"))
                    pass
                pass
            
            intag = t.find('*')
            if t.tag == xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_IQ) and \
                   intag != None and \
                   intag.tag == xmpp.utils.nt(ns.HTTP_DINFO,ns.TAG_QUERY):
                
                icateg = "conference"
                itype = "text"
                iname = "The Room"
                featlist = ["http://jabber.org/protocol/muc",
                            "muc_public",
                            "muc_persistent",
                            "muc_open",
                            "muc_semianonymous",
                            "muc_unmoderated",
                            "muc_unsecured"]
                mfrom = t.attrib['from']
                mid = t.attrib['id']
                self.s.send(msgout.dinfo(mid, self.name, mfrom,
                                         icateg, itype, iname, featlist))
                return
            
            if t.tag == xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_IQ) and \
                   intag != None and \
                   intag.tag == xmpp.utils.nt(ns.HTTP_DITEMS,ns.TAG_QUERY):
                itemslist = []
                if roomname in self.rooms:
                    for (f,n) in self.rooms[roomname]:
                        itemslist.append(n)
                        pass
                    pass
                mfrom = t.attrib['from']
                mid = t.attrib['id']
                self.s.send(msgout.ditems(mid, self.name, mfrom, itemslist))
                return
            
            pass
        
        # to user in a room
        if roomname != '' and servname != '' and nickname != '':
            t = xml.etree.ElementTree.fromstring(m)
            
            if t.tag == xmpp.utils.nt(ns.JABBER_CLIENT,ns.TAG_PRES) or \
                   t.tag == ns.TAG_PRES:
                if ('type' in t.attrib) == False:
                    t.attrib['type'] = 'available'
                    pass
                mfrom = t.attrib['from']
                mto = t.attrib['to']
                if t.attrib['type'] == 'available':                
                    if roomname in self.rooms:
                        found = False
                        for (f,n) in self.rooms[roomname]:
                            if f == mfrom: found = True
                            if n == nickname: found = True
                            pass
                        if found == False: self.rooms[roomname].append((mfrom,nickname))
                        pass
                    else: self.rooms[roomname] = [(mfrom,nickname)]
                    if roomname in self.rooms:
                        for (f,n) in self.rooms[roomname]:
                            t = roomname+"@"+servname+"/"+nickname
                            self.s.send(msgout.presence_ret(t, f, '', '', ''))
                            pass
                        for (f,n) in self.rooms[roomname]:
                            t = roomname+"@"+servname+"/"+n
                            self.s.send(msgout.presence_ret(t, mfrom, '', '', ''))
                            pass
                        pass
                    pass
                elif t.attrib['type'] == 'unavailable':
                    if roomname in self.rooms == False: return
                    # send unavailable presence to other group members
                    for (f,n) in self.rooms[roomname]:
                        if f == mfrom: self.rooms[roomname].remove((f,n))
                        pass
                    for (f,n) in self.rooms[roomname]:
                        t = roomname+"@"+servname+"/"+nickname
                        self.s.send(msgout.presence_ret(t,f, 'unavailable', '', ''))
                        pass
                    if len(self.rooms[roomname]) == 0: self.rooms.pop(roomname)
                    pass
                else:
                    pass
                pass
            
            pass
        
        pass
    
    pass

def usage():
    print("muc "
          "[-n <name.domain>|--name=<name.domain>]"
          "[-k <key>|--key=<key>]"
          "[-s <serverhost>]|[--server=<serverhost>]"
          "[-h|--help] [-v|--version]")
    pass

def main():
    xmpp.utils.debug(False)
    name = ""
    server = ""
    ckey = ""
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "n:k:s:hvD",
                                   ["name=", "key=", "server=", "help", "version", "debug"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        pass
    
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
            pass
        if o in ("-v", "--version"):
            print("muc: version 0.0.7")
            sys.exit()
            pass
        if o in ("-D", "--debug"):
            xmpp.utils.debug(True)
            pass
        if o in ("-n", "--name"):
            name = a
            pass
        if o in ("-k", "--key"):
            ckey = a
            pass
        if o in ("-s", "--server"):
            server = a
            pass
        pass

    if name == "" or server == "":
        usage()
        sys.exit(2)
        pass
    
    try:
        while True:
            mm = mucmanager()
            mm.name = name
            mm.ckey = ckey
            mm.server = server
            while True:
                xmpp.utils.print_clear()
                print("try to connect to ", mm.server)
                try: mm.s.connect(mm.server, 5222)
                except:
                    time.sleep(3)
                    continue
                break
            xmpp.utils.print_clear()
            print("connected")
            mm.connected = True
            mm.s.send(xmpp.msgout.sthdr(name, ns.JABBER_CMPNT))
            mm.s.start()
            while mm.connected == True:
                time.sleep(1)
                xmpp.utils.print_clear()
                print("Multi-User Conference Component")
                print(mm.server)
                mm.print()
                xmpp.utils.dprint(mm.rooms)
                pass
            pass
        pass
    
    except: print("Unexpected error:", sys.exc_info())
    pass

if __name__ == "__main__":
    main()
    pass
