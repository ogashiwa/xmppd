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

import sys, socket, threading, time, abc, re, queue, string, random
from . import utils, ns, msg

class stream(threading.Thread):
    """ class XmppStream(threading.Thread): """
    def nf(self,s,m):
        pass
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.ServerName = "localhost"
        self.StateSendStHdr = False
        self.StateRecvStHdr = False
        self.CBF_recv = self.nf
        self.CBF_closed = self.nf
        self.socket = None
        self.peeraddr = None
        self._binbuf = bytearray()
        self._utfbuf = ""
        self._SendQueue = queue.Queue()
        self.ready = True
        pass
    
    def run(self):
        try:
            while True:
                self.send("")
                r = self.socket.recv(1*1024*1024)
                if len(r) is 0: break
                self._binbuf += r
                ubuf = self._binbuf
                try: ubuf = ubuf.decode('utf-8')
                except: continue
                self._binbuf = bytearray()
                self._utfbuf += ubuf
                self._utfbuf = self._getxmlblock(self._utfbuf)
                pass
            pass
        except: print("Unexpected error:", sys.exc_info())
        try: self.socket.close()
        except: pass
        if self.CBF_closed: self.CBF_closed(self,"")
        pass
    
    def close(self):
        self.socket.close()
        pass
    
    def send(self,m):
        try:
            if len(m) > 0: self._SendQueue.put(m)
            if self.ready == False: return
            while self._SendQueue.empty() is False:
                b = self._SendQueue.get()
                utils.dprint("S:"+str(self.peeraddr)+": "+b)
                self.socket.send(b.encode("cp932"))
                pass
            pass
        except: print("Unexpected error:", sys.exc_info())
        pass
    
    def connect(self, serv, port):
        self.socket = socket.create_connection((serv, port), 5)
        self.socket.settimeout(None)
        pass
    
    def connect6(self, serv, port):
        self.socket = socket.create_connection((serv, port), 5)
        self.socket.settimeout(None)
        pass
    
    def _getxmlblock(self, s):
        res = re.search(r'(?ms)[^<]*(<\?xml[^>]+\?>)(.*)',str(s))
        if res:
            utils.dprint("R:"+str(self.peeraddr)+": "+res.group(1))
            s = res.group(2)
            pass
        res = re.search(r'(?ms)[^<]*(<stream:stream[^>]+>)(.*)',str(s))
        if res:
            utils.dprint("R:"+str(self.peeraddr)+": "+res.group(1))
            s = res.group(2)
            self.CBF_recv(self,res.group(1))
        while True:
            spl = msg.xmlblock(s)
            (blk, s) = spl.get()
            if len(blk) > 0:
                utils.dprint("R:"+str(self.peeraddr)+": "+blk)
                self.CBF_recv(self,blk)
            else: break
            pass
        return s
    pass
